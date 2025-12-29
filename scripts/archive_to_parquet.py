import pandas as pd
import duckdb
import os
import shutil
from pathlib import Path

# Setup paths
DATA_DIR = Path("data_lake")
if DATA_DIR.exists():
    shutil.rmtree(DATA_DIR)
DATA_DIR.mkdir(parents=True)

print("=== 1. Simulating ERCOT Archive Download ===")
# Simulate downloading data for 3 days
dates = pd.date_range("2023-01-01", "2023-01-03", freq="D")
dfs = []

for date in dates:
    print(f"Processing {date.date()}...")
    # Create dummy SPP data
    df = pd.DataFrame({
        "DeliveryDate": [date.date()] * 24,
        "DeliveryHour": range(1, 25),
        "SettlementPoint": ["LZ_HOUSTON"] * 24,
        "SettlementPointPrice": [50.0 + i for i in range(24)],
        "DSTFlag": ["N"] * 24
    })
    
    # 2. Write to Parquet (Partitioned)
    # Structure: data_lake/spp/year=YYYY/month=MM/day=DD/data.parquet
    output_path = DATA_DIR / "spp" / f"year={date.year}" / f"month={date.month:02d}" / f"day={date.day:02d}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write parquet using pyarrow engine
    file_path = output_path / "data.parquet"
    df.to_parquet(file_path, engine="pyarrow", index=False)
    print(f"  Saved to {file_path}")

print("\n=== 2. Querying with DuckDB (Client-Side) ===")
print("Simulating tinygrid client fetching data for Jan 2-3...")

# DuckDB can query hive-partitioned parquet files directly using glob patterns
# In a real S3 scenario, we'd use 's3://bucket/spp/**/data.parquet'
# For local fs, we use the path.

query = """
SELECT 
    DeliveryDate, 
    avg(SettlementPointPrice) as avg_price
FROM read_parquet('data_lake/spp/*/*/*/data.parquet', hive_partitioning=1)
WHERE DeliveryDate >= '2023-01-02'
GROUP BY DeliveryDate
ORDER BY DeliveryDate
"""

con = duckdb.connect()
result = con.execute(query).df()
print("\nQuery Result:")
print(result)

print("\n=== 3. Benefits ===")
print(f"Total Lake Size: {sum(f.stat().st_size for f in DATA_DIR.rglob('*.parquet')) / 1024:.2f} KB (Tiny!)")
print("1. Zero Database Cost (Just S3 storage)")
print("2. Fast Queries (Columnar scan)")
print("3. Unified Interface (Client sees a DataFrame)")
