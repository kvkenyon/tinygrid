from unittest.mock import MagicMock

import pandas as pd
import pytest

from pyercot.errors import UnexpectedStatus

from tinygrid.constants.ercot import LOAD_ZONES, LocationType, Market, TRADING_HUBS
from tinygrid.errors import GridAPIError, GridAuthenticationError, GridTimeoutError
from tinygrid.ercot import ERCOT


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


def test_get_client_creates_authenticated_client(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, object] = {}

    class DummyAuthenticatedClient:
        def __init__(self, base_url, token, timeout, verify_ssl, raise_on_unexpected_status):  # type: ignore[no-untyped-def]
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

    monkeypatch.setattr("tinygrid.ercot.AuthenticatedClient", DummyAuthenticatedClient)

    client = make_ercot(auth=auth)
    result = client._get_client()

    assert isinstance(result, DummyAuthenticatedClient)
    assert created["headers"] == {"Ocp-Apim-Subscription-Key": "subkey"}


def test_get_client_refreshes_token_and_closes_old(monkeypatch: pytest.MonkeyPatch) -> None:
    closed = {"value": False}

    class DummyAuthenticatedClient:
        def __init__(self, base_url=None, token=None, timeout=None, verify_ssl=None, raise_on_unexpected_status=None):  # type: ignore[no-untyped-def]
            self.token = token

        def with_headers(self, headers):
            return self

        def __exit__(self, exc_type, exc, tb):
            closed["value"] = True
            return False

    auth = MagicMock()
    auth.get_token.return_value = "new"
    auth.get_subscription_key.return_value = "sub"

    monkeypatch.setattr("tinygrid.ercot.AuthenticatedClient", DummyAuthenticatedClient)

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


def test_products_to_dataframe_handles_additional_properties() -> None:
    client = make_ercot()
    response = {
        "additional_properties": {
            "_embedded": {
                "products": [
                    {
                        "emilId": "np1",
                        "name": "test",
                        "details": {"nested": 1},
                    }
                ]
            }
        }
    }

    df = client._products_to_dataframe(response)

    assert not df.empty
    assert list(df["emilId"])[0] == "np1"
    assert df.filter(like="details.nested").iloc[0, 0] == 1


def test_product_history_to_dataframe_expands_archives() -> None:
    client = make_ercot()
    response = {
        "emilId": "np1",
        "archives": [
            {"version": 1, "size": 10},
            {"version": 2, "size": 20},
        ],
    }

    df = client._product_history_to_dataframe(response)

    assert len(df) == 2
    assert set(df["version"].tolist()) == {1, 2}
    assert df["emilId"].iloc[0] == "np1"


def test_filter_by_location_excludes_zones_for_resource_nodes() -> None:
    client = make_ercot()
    df = pd.DataFrame(
        {
            "Settlement Point": ["HB_HOUSTON", "CUSTOM1", "LZ_NORTH", "CUSTOM2"],
            "val": [1, 2, 3, 4],
        }
    )

    filtered = client._filter_by_location(
        df,
        location_type=LocationType.RESOURCE_NODE,
        location_column="Settlement Point",
    )

    assert set(filtered["Settlement Point"]) == {"CUSTOM1", "CUSTOM2"}
    assert all(pt not in LOAD_ZONES + TRADING_HUBS for pt in filtered["Settlement Point"])


def test_filter_by_location_matches_allowed_types() -> None:
    client = make_ercot()
    df = pd.DataFrame(
        {
            "Settlement Point": ["HB_HOUSTON", "LZ_SOUTH", "CUSTOM"],
            "val": [1, 2, 3],
        }
    )

    filtered = client._filter_by_location(
        df,
        location_type=[LocationType.TRADING_HUB, LocationType.LOAD_ZONE],
        location_column="Settlement Point",
    )

    assert set(filtered["Settlement Point"]) == {"HB_HOUSTON", "LZ_SOUTH"}


def test_filter_by_date_handles_alternate_column_names() -> None:
    client = make_ercot()
    df = pd.DataFrame({"DeliveryDate": ["2024-01-01", "2024-01-03"]})

    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2024-01-02")

    filtered = client._filter_by_date(df, start, end, date_column="Delivery Date")

    assert len(filtered) == 1
    assert filtered.iloc[0]["DeliveryDate"] == "2024-01-01"


def test_add_time_columns_from_interval_fields() -> None:
    client = make_ercot()
    df = pd.DataFrame({"Date": ["2024-01-01"], "Hour": [1], "Interval": [2]})

    result = client._add_time_columns(df.copy())

    assert "Time" in result and "End Time" in result
    assert result["Time"].dt.tz is not None
    assert (result["End Time"] - result["Time"]).dt.total_seconds().iloc[0] == 900


def test_add_time_columns_from_hour_ending_strings() -> None:
    client = make_ercot()
    df = pd.DataFrame({"Date": ["2024-01-01"], "Hour Ending": ["01:00"]})

    result = client._add_time_columns(df.copy())

    assert "Time" in result and "End Time" in result
    assert result["Time"].dt.hour.iloc[0] == 0
    assert result["End Time"].dt.hour.iloc[0] == 1


def test_get_shadow_prices_routes_to_archive_for_day_ahead(monkeypatch: pytest.MonkeyPatch) -> None:
    class HistoricalERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return True

        def _filter_by_date(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:  # type: ignore[override]
            return df

        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = HistoricalERCOT()
    calls: dict[str, object] = {}

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame({"Delivery Date": ["2024-01-01"]})
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    monkeypatch.setattr(
        client,
        "get_dam_shadow_prices",
        lambda **kwargs: calls.setdefault("live", kwargs) or pd.DataFrame(),
    )

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

        def _filter_by_date(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:  # type: ignore[override]
            return df

        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = HistoricalERCOT()

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame({"Oper Day": ["2024-01-01"], "value": [1]})
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    monkeypatch.setattr(
        client,
        "get_actual_system_load_by_weather_zone",
        lambda **kwargs: pd.DataFrame(),
    )

    df = client.get_load(start="2024-01-01", end="2024-01-02", by="weather_zone")

    assert df["value"].iloc[0] == 1
    archive.fetch_historical.assert_called_once()


def test_get_shadow_prices_real_time_live_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class LiveERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return False

        def _filter_by_date(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:  # type: ignore[override]
            return df

        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = LiveERCOT()
    monkeypatch.setattr(
        client,
        "get_shadow_prices_bound_transmission_constraint",
        lambda **kwargs: pd.DataFrame({"Delivery Date": ["2024-01-01"]}),
    )

    df = client.get_shadow_prices(start="2024-01-01", end="2024-01-02", market=Market.REAL_TIME_SCED)

    assert not df.empty


def test_get_wind_forecast_mixes_historical_and_live(monkeypatch: pytest.MonkeyPatch) -> None:
    class MixedERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return market == "forecast"

        def _filter_by_date(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:  # type: ignore[override]
            return df

        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = MixedERCOT()

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame({"Posted Datetime": ["2024-01-01"]})
    monkeypatch.setattr(client, "_get_archive", lambda: archive)
    monkeypatch.setattr(
        client,
        "get_wpp_hourly_actual_forecast_geo",
        lambda **kwargs: pd.DataFrame({"Posted Datetime": ["2024-01-02"]}),
    )

    df_region = client.get_wind_forecast(start="2024-01-01", end="2024-01-02", by_region=True)
    df_global = client.get_wind_forecast(start="2024-01-01", end="2024-01-02", by_region=False)

    assert not df_region.empty and not df_global.empty
    assert archive.fetch_historical.call_count == 2


def test_get_solar_forecast_live_region(monkeypatch: pytest.MonkeyPatch) -> None:
    class LiveERCOT(ERCOT):
        def _needs_historical(self, start: pd.Timestamp, market: str) -> bool:  # type: ignore[override]
            return False

        def _filter_by_date(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:  # type: ignore[override]
            return df

        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = LiveERCOT()
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

        def _filter_by_date(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:  # type: ignore[override]
            return df

        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = HistoricalERCOT()
    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame({"Posted Datetime": ["2024-01-01"]})
    monkeypatch.setattr(client, "_get_archive", lambda: archive)

    df = client.get_solar_forecast(start="2024-01-01", end="2024-01-02", by_region=False)

    assert not df.empty
    archive.fetch_historical.assert_called_once()


def test_get_60_day_dam_disclosure_uses_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    class DisclosureERCOT(ERCOT):
        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = DisclosureERCOT()

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame({"DeliveryDate": ["2024-01-01"]})
    monkeypatch.setattr(client, "_get_archive", lambda: archive)

    for method_name in [
        "get_dam_gen_res_as_offers",
        "get_dam_load_res_data",
        "get_dam_load_res_as_offers",
        "get_dam_energy_only_offers",
        "get_dam_energy_only_offer_awards",
        "get_dam_energy_bids",
        "get_dam_energy_bid_awards",
        "get_dam_ptp_obl_bids",
        "get_dam_ptp_obl_bid_awards",
        "get_dam_ptp_obl_opt",
        "get_dam_ptp_obl_opt_awards",
    ]:
        monkeypatch.setattr(client, method_name, lambda **kwargs: pd.DataFrame({"dummy": [1]}))

    reports = client.get_60_day_dam_disclosure("today")

    assert "dam_gen_resource" in reports
    archive.fetch_historical.assert_called_once()


def test_get_60_day_sced_disclosure(monkeypatch: pytest.MonkeyPatch) -> None:
    class DisclosureERCOT(ERCOT):
        def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
            return df

    client = DisclosureERCOT()

    archive = MagicMock()
    archive.fetch_historical.return_value = pd.DataFrame({"DeliveryDate": ["2024-01-01"]})
    monkeypatch.setattr(client, "_get_archive", lambda: archive)

    monkeypatch.setattr(client, "get_sced_gen_res_data", lambda **kwargs: pd.DataFrame({"a": [1]}))
    monkeypatch.setattr(client, "get_load_res_data_in_sced", lambda **kwargs: pd.DataFrame({"b": [2]}))

    reports = client.get_60_day_sced_disclosure("today")

    assert "sced_smne" in reports
    archive.fetch_historical.assert_called_once()
