#!/usr/bin/env python3
"""Example script demonstrating ERCOT API usage with authentication"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

# Load environment variables from .env file
env_path = Path(__file__).parent
load_dotenv(env_path / ".env")

# Verify environment variables are loaded
required_vars = ["ERCOT_USERNAME", "ERCOT_PASSWORD", "ERCOT_SUBSCRIPTION_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}. "
        "Please create a .env file with your ERCOT credentials."
    )


def format_response(data: dict, max_records: int = 3) -> str:
    """Format API response data for display."""
    if not data:
        return "  No data returned"

    # Check if data has records (common structure for ERCOT API responses)
    records = data.get("records", [])
    if records:
        output_lines = [f"  Total records in response: {len(records)}"]
        output_lines.append(f"  Showing first {min(max_records, len(records))} records:")
        for i, record in enumerate(records[:max_records]):
            output_lines.append(f"\n  Record {i + 1}:")
            output_lines.append(f"    {json.dumps(record, indent=4, default=str)}")
        return "\n".join(output_lines)

    # Otherwise just show the dict keys and some sample data
    output_lines = [f"  Response keys: {list(data.keys())}"]
    sample = {k: v for i, (k, v) in enumerate(data.items()) if i < 5}
    output_lines.append(f"  Sample data: {json.dumps(sample, indent=4, default=str)}")
    return "\n".join(output_lines)


def main():
    """Main example function"""
    print("=" * 60)
    print("ERCOT API Example - Tiny Grid SDK")
    print("=" * 60)
    print()

    # Calculate dates dynamically
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    # Format dates as YYYY-MM-DD strings
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    two_days_ago_str = two_days_ago.strftime("%Y-%m-%d")

    print(f"Using dates: {two_days_ago_str} to {yesterday_str}")
    print()

    print("Setting up ERCOT authentication...")

    # Create authentication configuration from environment variables
    auth_config = ERCOTAuthConfig(
        username=os.getenv("ERCOT_USERNAME"),
        password=os.getenv("ERCOT_PASSWORD"),
        subscription_key=os.getenv("ERCOT_SUBSCRIPTION_KEY"),
    )

    # Create authentication handler
    auth = ERCOTAuth(auth_config)

    # Create ERCOT client with authentication
    ercot = ERCOT(auth=auth)

    print("✓ ERCOT client created with authentication\n")

    # =========================================================================
    # Example 1: Get Actual System Load by Weather Zone (Historical Data)
    # =========================================================================
    print("-" * 60)
    print("Example 1: Actual System Load by Weather Zone")
    print("-" * 60)
    print(f"Fetching actual load data for {yesterday_str}...")

    try:
        # Use operating_day_from/to for actual system load endpoint
        # Add size parameter to get more records
        actual_load = ercot.get_actual_system_load_by_weather_zone(
            operating_day_from=yesterday_str,
            operating_day_to=yesterday_str,
            size=10,  # Limit to 10 records for example
        )
        print("✓ Retrieved actual system load data")
        print(format_response(actual_load))
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # =========================================================================
    # Example 2: Get Load Forecast by Weather Zone
    # =========================================================================
    print("-" * 60)
    print("Example 2: Seven-Day Load Forecast by Weather Zone")
    print("-" * 60)
    print(f"Fetching load forecast starting from {today_str}...")

    try:
        # Use delivery_date_from/to for forecast endpoint
        # The forecast is typically available for the next 7 days
        forecast = ercot.get_load_forecast_by_weather_zone(
            start_date=today_str,
            end_date=today_str,
            size=10,  # Limit to 10 records
        )
        print("✓ Retrieved load forecast data")
        print(format_response(forecast))
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # =========================================================================
    # Example 3: Get Day-Ahead Market Hourly LMP (Locational Marginal Prices)
    # =========================================================================
    print("-" * 60)
    print("Example 3: Day-Ahead Market Hourly LMP")
    print("-" * 60)
    print(f"Fetching DAM hourly LMP for {yesterday_str}...")

    try:
        # DAM LMP data is available for past dates
        dam_lmp = ercot.get_dam_hourly_lmp(
            start_date=yesterday_str,
            end_date=yesterday_str,
            size=10,  # Limit to 10 records
        )
        print("✓ Retrieved DAM hourly LMP data")
        print(format_response(dam_lmp))
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # =========================================================================
    # Example 4: Get Solar Power Production (Actual vs Forecast)
    # =========================================================================
    print("-" * 60)
    print("Example 4: Solar Power Production - Hourly Actual vs Forecast")
    print("-" * 60)
    print("Fetching solar power production data...")

    try:
        solar_data = ercot.get_spp_hourly_average_actual_forecast(size=10)
        print("✓ Retrieved solar power production data")
        print(format_response(solar_data))
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # =========================================================================
    # Example 5: Get Wind Power Production (Actual vs Forecast)
    # =========================================================================
    print("-" * 60)
    print("Example 5: Wind Power Production - Hourly Actual vs Forecast")
    print("-" * 60)
    print("Fetching wind power production data...")

    try:
        wind_data = ercot.get_wpp_hourly_average_actual_forecast(size=10)
        print("✓ Retrieved wind power production data")
        print(format_response(wind_data))
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # =========================================================================
    # Example 6: Get List of Available Products
    # =========================================================================
    print("-" * 60)
    print("Example 6: Available ERCOT Data Products")
    print("-" * 60)
    print("Fetching list of available products...")

    try:
        products = ercot.get_list_for_products()
        print("✓ Retrieved product list")

        # Products response structure is different - it contains a list of products
        if isinstance(products, dict):
            # Check for common response structures
            if "products" in products:
                product_list = products["products"]
                print(f"  Total products available: {len(product_list)}")
                print("  First 3 products:")
                for prod in product_list[:3]:
                    name = prod.get("name", prod.get("emilId", "Unknown"))
                    desc = prod.get("description", "No description")[:50]
                    print(f"    - {name}: {desc}...")
            else:
                print(format_response(products))
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
