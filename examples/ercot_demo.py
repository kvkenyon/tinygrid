#!/usr/bin/env python3
"""Example script demonstrating ERCOT client with DataFrame output.

This script shows how to use the tinygrid ERCOT client to fetch data
and work with pandas DataFrames.

Features demonstrated:
- Authentication setup
- Fetching LMP data as DataFrames
- Automatic pagination (fetches all pages)
- Retry logic for transient failures
- Human-readable column labels
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Load environment variables from .env file
load_dotenv()


def main():
    """Main example function."""
    # Check for required environment variables
    username = os.getenv("ERCOT_USERNAME")
    password = os.getenv("ERCOT_PASSWORD")
    subscription_key = os.getenv("ERCOT_SUBSCRIPTION_KEY")

    if not all([username, password, subscription_key]):
        print("Error: Missing required environment variables.")
        print(
            "Please set ERCOT_USERNAME, ERCOT_PASSWORD, and ERCOT_SUBSCRIPTION_KEY"
        )
        print("\nYou can create a .env file with these values:")
        print("  ERCOT_USERNAME=your_email@example.com")
        print("  ERCOT_PASSWORD=your_password")
        print("  ERCOT_SUBSCRIPTION_KEY=your_subscription_key")
        return

    # Initialize authentication
    auth = ERCOTAuth(
        ERCOTAuthConfig(
            username=username,
            password=password,
            subscription_key=subscription_key,
        )
    )

    # Initialize ERCOT client with custom settings
    ercot = ERCOT(
        auth=auth,
        page_size=10000,  # Records per page (max for most endpoints)
        max_retries=3,  # Retry transient failures up to 3 times
        retry_min_wait=1.0,  # Start with 1 second wait
        retry_max_wait=60.0,  # Cap at 60 seconds
        max_concurrent_requests=5,  # Parallel page fetching
    )

    # Example 1: Get LMP data for electrical buses
    print("\n" + "=" * 60)
    print("Example 1: LMP by Electrical Bus")
    print("=" * 60)

    # Get data for the last hour
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)

    try:
        df_lmp = ercot.get_lmp_electrical_bus(
            sced_timestamp_from=start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            sced_timestamp_to=end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        )

        print(f"\nFetched {len(df_lmp)} LMP records")
        print(f"Columns: {list(df_lmp.columns)}")
        if not df_lmp.empty:
            print("\nSample data:")
            print(df_lmp.head(10))

            # Show some statistics
            if "LMP" in df_lmp.columns:
                print("\nLMP Statistics:")
                print(f"  Min: ${df_lmp['LMP'].min():.2f}")
                print(f"  Max: ${df_lmp['LMP'].max():.2f}")
                print(f"  Mean: ${df_lmp['LMP'].mean():.2f}")
    except Exception as e:
        print(f"Error fetching LMP data: {e}")

    # Example 2: Get actual system load by weather zone
    print("\n" + "=" * 60)
    print("Example 2: Actual System Load by Weather Zone")
    print("=" * 60)

    # Get data for yesterday (more likely to have complete data)
    yesterday = datetime.now() - timedelta(days=1)
    operating_day = yesterday.strftime("%Y-%m-%d")

    try:
        df_load = ercot.get_actual_system_load_by_weather_zone(
            operating_day_from=operating_day,
            operating_day_to=operating_day,
        )

        print(f"\nFetched {len(df_load)} load records")
        print(f"Columns: {list(df_load.columns)}")
        if not df_load.empty:
            print("\nSample data:")
            print(df_load.head(10))
    except Exception as e:
        print(f"Error fetching load data: {e}")

    # Example 3: Get wind power forecast
    print("\n" + "=" * 60)
    print("Example 3: Wind Power Hourly Average")
    print("=" * 60)

    try:
        df_wind = ercot.get_wpp_hourly_average_actual_forecast(
            delivery_date_from=operating_day,
            delivery_date_to=operating_day,
        )

        print(f"\nFetched {len(df_wind)} wind power records")
        print(f"Columns: {list(df_wind.columns)}")
        if not df_wind.empty:
            print("\nSample data:")
            print(df_wind.head(10))
    except Exception as e:
        print(f"Error fetching wind data: {e}")

    # Example 4: Get solar power data
    print("\n" + "=" * 60)
    print("Example 4: Solar Power Hourly Average")
    print("=" * 60)

    try:
        df_solar = ercot.get_spp_hourly_average_actual_forecast(
            delivery_date_from=operating_day,
            delivery_date_to=operating_day,
        )

        print(f"\nFetched {len(df_solar)} solar power records")
        print(f"Columns: {list(df_solar.columns)}")
        if not df_solar.empty:
            print("\nSample data:")
            print(df_solar.head(10))
    except Exception as e:
        print(f"Error fetching solar data: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
