from unittest.mock import MagicMock

import pandas as pd
import pytest
from pyercot.errors import UnexpectedStatus

from tinygrid.constants.ercot import LOAD_ZONES, TRADING_HUBS, LocationType, Market
from tinygrid.ercot import ERCOT
from tinygrid.errors import GridAPIError, GridAuthenticationError, GridTimeoutError


def make_ercot(**kwargs: object) -> ERCOT:
    """Create an ERCOT instance with sensible defaults for unit tests."""
    return ERCOT(auth=kwargs.get("auth"))  # type: ignore[arg-type]


def test_get_client_wraps_unexpected_auth_error() -> None:
    auth = MagicMock()
    auth.get_token.side_effect = ValueError("boom")
    auth.get_subscription_key.return_value = "sub"

    client = make_ercot(auth=auth)

    with pytest.raises(GridAuthenticationError):
        client._get_client()

    auth.get_subscription_key.assert_not_called()


def test_get_client_creates_authenticated_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: dict[str, object] = {}

    class DummyAuthenticatedClient:
        def __init__(
            self, base_url, token, timeout, verify_ssl, raise_on_unexpected_status
        ):  # type: ignore[no-untyped-def]
            created["token"] = token
            created["base_url"] = base_url
            created["headers"] = {}
            self.token = token

        def with_headers(self, headers):
            created["headers"] = headers
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    auth = MagicMock()
    auth.get_token.return_value = "token123"
    auth.get_subscription_key.return_value = "subkey"

    monkeypatch.setattr(
        "tinygrid.ercot.client.AuthenticatedClient", DummyAuthenticatedClient
    )

    client = make_ercot(auth=auth)
    result = client._get_client()

    assert isinstance(result, DummyAuthenticatedClient)
    assert created["headers"] == {"Ocp-Apim-Subscription-Key": "subkey"}


def test_get_client_refreshes_token_and_closes_old(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed = {"value": False}

    class DummyAuthenticatedClient:
        def __init__(
            self,
            base_url=None,
            token=None,
            timeout=None,
            verify_ssl=None,
            raise_on_unexpected_status=None,
        ):  # type: ignore[no-untyped-def]
            self.token = token

        def with_headers(self, headers):
            return self

        def __exit__(self, exc_type, exc, tb):
            closed["value"] = True
            return False

    auth = MagicMock()
    auth.get_token.return_value = "new"
    auth.get_subscription_key.return_value = "sub"

    monkeypatch.setattr(
        "tinygrid.ercot.client.AuthenticatedClient", DummyAuthenticatedClient
    )

    client = make_ercot(auth=auth)
    client._client = DummyAuthenticatedClient(token="old")

    result = client._get_client()

    assert isinstance(result, DummyAuthenticatedClient)
    assert closed["value"] is True
    assert result.token == "new"


def test_handle_api_error_wraps_exceptions() -> None:
    client = make_ercot()
    unexpected = UnexpectedStatus(status_code=500, content=b"err")

    with pytest.raises(GridAPIError):
        client._handle_api_error(unexpected, endpoint="/test")

    with pytest.raises(GridTimeoutError):
        client._handle_api_error(TimeoutError(), endpoint="/test")


@pytest.mark.skip(reason="Method removed in refactor - not part of public API")
def test_flatten_dict_handles_nested_lists_and_nulls() -> None:
    client = make_ercot()
    data = {
        "meta": {"id": 1, "name": "x"},
        "values": [{"foo": "bar"}, {"foo": "baz"}],
        "tags": ["a", "b", "c"],
        "_links": {"self": "skip"},
        "none_val": None,
    }

    flattened = client._flatten_dict_for_dataframe(data)

    assert flattened["meta.id"] == 1
    assert flattened["values_count"] == 2
    assert "values" in flattened and "skip" not in str(flattened)
    assert flattened["tags"] == "a, b, c"
    assert "none_val" in flattened and flattened["none_val"] is None


def test_products_to_dataframe_handles_products_list() -> None:
    """Test the simplified _products_to_dataframe method."""
    client = make_ercot()
    response = {
        "products": [
            {
                "emilId": "np1",
                "name": "test",
            }
        ]
    }

    df = client._products_to_dataframe(response)

    assert not df.empty
    assert df.iloc[0]["emilId"] == "np1"


def test_product_history_to_dataframe_returns_archives() -> None:
    """Test the simplified _product_history_to_dataframe method."""
    client = make_ercot()
    response = {
        "archives": [
            {"version": 1, "size": 10},
            {"version": 2, "size": 20},
        ],
    }

    df = client._product_history_to_dataframe(response)

    assert len(df) == 2
    assert set(df["version"].tolist()) == {1, 2}


def test_filter_by_location_excludes_zones_for_resource_nodes() -> None:
    from tinygrid.ercot.transforms import filter_by_location

    df = pd.DataFrame(
        {
            "Settlement Point": ["HB_HOUSTON", "CUSTOM1", "LZ_NORTH", "CUSTOM2"],
            "val": [1, 2, 3, 4],
        }
    )

    filtered = filter_by_location(
        df,
        location_type=LocationType.RESOURCE_NODE,
        location_column="Settlement Point",
    )

    assert set(filtered["Settlement Point"]) == {"CUSTOM1", "CUSTOM2"}
    assert all(
        pt not in LOAD_ZONES + TRADING_HUBS for pt in filtered["Settlement Point"]
    )


def test_filter_by_location_matches_allowed_types() -> None:
    from tinygrid.ercot.transforms import filter_by_location

    df = pd.DataFrame(
        {
            "Settlement Point": ["HB_HOUSTON", "LZ_SOUTH", "CUSTOM"],
            "val": [1, 2, 3],
        }
    )

    filtered = filter_by_location(
        df,
        location_type=[LocationType.TRADING_HUB, LocationType.LOAD_ZONE],
        location_column="Settlement Point",
    )

    assert set(filtered["Settlement Point"]) == {"HB_HOUSTON", "LZ_SOUTH"}


def test_filter_by_date_handles_alternate_column_names() -> None:
    from tinygrid.ercot.transforms import filter_by_date

    df = pd.DataFrame({"DeliveryDate": ["2024-01-01", "2024-01-03"]})

    start = pd.Timestamp("2024-01-01", tz="US/Central")
    end = pd.Timestamp("2024-01-02", tz="US/Central")

    filtered = filter_by_date(df, start, end, date_column="Delivery Date")

    assert len(filtered) == 1
    assert filtered.iloc[0]["DeliveryDate"] == "2024-01-01"


def test_add_time_columns_from_interval_fields() -> None:
    from tinygrid.ercot.transforms import add_time_columns

    df = pd.DataFrame({"Date": ["2024-01-01"], "Hour": [1], "Interval": [2]})

    result = add_time_columns(df.copy())

    assert "Time" in result and "End Time" in result
    assert result["Time"].dt.tz is not None
    assert (result["End Time"] - result["Time"]).dt.total_seconds().iloc[0] == 900


def test_add_time_columns_from_hour_ending_strings() -> None:
    from tinygrid.ercot.transforms import add_time_columns

    df = pd.DataFrame({"Date": ["2024-01-01"], "Hour Ending": ["01:00"]})

    result = add_time_columns(df.copy())

    assert "Time" in result and "End Time" in result
    assert result["Time"].dt.hour.iloc[0] == 0
    assert result["End Time"].dt.hour.iloc[0] == 1


def test_get_shadow_prices_routes_to_archive_for_day_ahead(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class HistoricalERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return True

    client = HistoricalERCOT()
    calls: dict[str, object] = {}

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame(
        {"Delivery Date": ["2024-01-01"]}
    )
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    monkeypatch.setattr(
        client,
        "get_dam_shadow_prices",
        lambda **kwargs: calls.setdefault("live", kwargs) or pd.DataFrame(),
    )
    # Patch the standalone functions to pass through
    monkeypatch.setattr(
        "tinygrid.ercot.api.filter_by_date", lambda df, *args, **kwargs: df
    )
    monkeypatch.setattr("tinygrid.ercot.api.standardize_columns", lambda df: df)

    df = client.get_shadow_prices(
        start="2024-01-01", end="2024-01-02", market=Market.DAY_AHEAD_HOURLY
    )

    assert not df.empty
    archive.fetch_historical.assert_called_once()
    assert "live" not in calls


def test_get_load_uses_historical_weather_zone(monkeypatch: pytest.MonkeyPatch) -> None:
    class HistoricalERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return True

    client = HistoricalERCOT()

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame(
        {"Oper Day": ["2024-01-01"], "value": [1]}
    )
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    monkeypatch.setattr(
        client,
        "get_actual_system_load_by_weather_zone",
        lambda **kwargs: pd.DataFrame(),
    )
    # Patch the standalone functions to pass through
    monkeypatch.setattr(
        "tinygrid.ercot.api.filter_by_date", lambda df, *args, **kwargs: df
    )
    monkeypatch.setattr("tinygrid.ercot.api.standardize_columns", lambda df: df)

    df = client.get_load(start="2024-01-01", end="2024-01-02", by="weather_zone")

    assert df["value"].iloc[0] == 1
    archive.fetch_historical.assert_called_once()


def test_get_shadow_prices_real_time_live_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class LiveERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return False

    client = LiveERCOT()
    monkeypatch.setattr(
        client,
        "get_shadow_prices_bound_transmission_constraint",
        lambda **kwargs: pd.DataFrame({"Delivery Date": ["2024-01-01"]}),
    )
    # Patch the standalone functions to pass through
    monkeypatch.setattr(
        "tinygrid.ercot.api.filter_by_date", lambda df, *args, **kwargs: df
    )
    monkeypatch.setattr("tinygrid.ercot.api.standardize_columns", lambda df: df)

    df = client.get_shadow_prices(
        start="2024-01-01", end="2024-01-02", market=Market.REAL_TIME_SCED
    )

    assert not df.empty


def test_get_wind_forecast_mixes_historical_and_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MixedERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return market == "forecast"

    client = MixedERCOT()

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame(
        {"Posted Datetime": ["2024-01-01"]}
    )
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    monkeypatch.setattr(
        client,
        "get_wpp_hourly_actual_forecast_geo",
        lambda **kwargs: pd.DataFrame({"Posted Datetime": ["2024-01-02"]}),
    )
    # Patch the standalone functions to pass through
    monkeypatch.setattr(
        "tinygrid.ercot.api.filter_by_date", lambda df, *args, **kwargs: df
    )
    monkeypatch.setattr("tinygrid.ercot.api.standardize_columns", lambda df: df)

    df_region = client.get_wind_forecast(
        start="2024-01-01", end="2024-01-02", by_region=True
    )
    df_global = client.get_wind_forecast(
        start="2024-01-01", end="2024-01-02", by_region=False
    )

    assert not df_region.empty and not df_global.empty
    assert archive.fetch_historical.call_count == 2


def test_get_solar_forecast_live_region(monkeypatch: pytest.MonkeyPatch) -> None:
    class LiveERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return False

    client = LiveERCOT()
    # Patch the standalone functions to pass through
    monkeypatch.setattr(
        "tinygrid.ercot.api.filter_by_date", lambda df, *args, **kwargs: df
    )
    monkeypatch.setattr("tinygrid.ercot.api.standardize_columns", lambda df: df)
    monkeypatch.setattr(
        client,
        "get_spp_hourly_actual_forecast_geo",
        lambda **kwargs: pd.DataFrame({"Posted Datetime": ["2024-01-01"]}),
    )

    df = client.get_solar_forecast(start="2024-01-01", end="2024-01-02", by_region=True)

    assert not df.empty


def test_get_solar_forecast_historical(monkeypatch: pytest.MonkeyPatch) -> None:
    class HistoricalERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return True

    client = HistoricalERCOT()
    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame(
        {"Posted Datetime": ["2024-01-01"]}
    )
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    # Patch the standalone functions to pass through
    monkeypatch.setattr(
        "tinygrid.ercot.api.filter_by_date", lambda df, *args, **kwargs: df
    )
    monkeypatch.setattr("tinygrid.ercot.api.standardize_columns", lambda df: df)

    df = client.get_solar_forecast(
        start="2024-01-01", end="2024-01-02", by_region=False
    )

    assert not df.empty
    archive.fetch_historical.assert_called_once()


def test_get_60_day_dam_disclosure_uses_archive() -> None:
    client = ERCOT()
    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame(
        {"DeliveryDate": ["2024-01-01"]}
    )
    client.get_60_day_dam_disclosure()
    archive.fetch_historical.assert_called_once()


def test_get_60_day_sced_disclosure() -> None:
    client = ERCOT()

    documents = MagicMock()
    documents.get_60d_sced_disclosure.return_value = pd.DataFrame(
        {"DeliveryDate": ["2024-01-01"]}
    )
    reports = client.get_60_day_sced_disclosure("today")

    documents._get_document.assert_called_once()
