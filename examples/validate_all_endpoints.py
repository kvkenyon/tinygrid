import os

from dotenv import load_dotenv

from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

load_dotenv()


def main():
    auth = ERCOTAuth(
        ERCOTAuthConfig(
            username=os.getenv("ERCOT_USERNAME"),
            password=os.getenv("ERCOT_PASSWORD"),
            subscription_key=os.getenv("ERCOT_SUBSCRIPTION_KEY"),
        )
    )

    ercot = ERCOT(auth=auth)

    # Get product as DataFrame (default)
    # df = ercot.get_product("NP3-233-CD")

    # Get product history as DataFrame - one row per archive
    # df_history = ercot.get_product_history("NP3-233-CD")
    # print(df_history.head())

    # Get version as DataFrame
    # df_version = ercot.get_version()
    # print(df_version)

    # Get raw dictionaries if needed
    # product_dict = ercot.get_product("NP3-233-CD", as_dataframe=False)
    # print(product_dict)

    df_load_forecast = ercot.get_load_forecast_by_weather_zone(
        start_date="2025-12-25",
        end_date="2025-12-31",
    )

    print(df_load_forecast.head())

    df_load_forecast_by_study_area = ercot.get_load_forecast_by_study_area(
        start_date="2025-12-25",
        end_date="2025-12-31",
    )
    print(df_load_forecast_by_study_area.head())

    df_aggregated_dsr_loads = ercot.get_aggregated_dsr_loads(
        sced_timestamp_from="2025-12-25T00:00:00",
    )
    print(df_aggregated_dsr_loads.head())


if __name__ == "__main__":
    main()
