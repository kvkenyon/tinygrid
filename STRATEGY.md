# Strategy: Historical Data & Differentiation for Tinygrid

## Executive Summary
To compete with Grid Status's paid offering ("pre-built historical database"), Tinygrid should adopt a **"Client-Side Data Warehousing"** approach. Instead of managing expensive database servers (Postgres/Snowflake), we will pre-process ERCOT historical data into highly optimized **Parquet** files stored in **Cloudflare R2** (zero egress fees). The `tinygrid` Python client will be updated to transparently fetch and query these files using **DuckDB**, offering performance comparable to paid APIs at a fraction of the cost.

## 1. Architecture: The "Serverless" Historical Database

### Storage Layer: S3-Compatible Object Storage (Parquet)
We will store historical data in an S3-compatible bucket (Cloudflare R2 recommended for free egress).

**Schema Structure:**
```text
s3://tinygrid-ercot/
  ├── real_time_spp/
  │   └── year=2023/month=12/day=01/data.parquet
  ├── real_time_lmp_bus/
  │   └── year=2023/month=12/day=01/part-001.parquet
  ├── dam_spp/
  │   └── year=2023/month=12/day=01/data.parquet
  └── ...
```

**Why Parquet?**
-   **Compression**: 10x smaller than CSV.
-   **Speed**: Columnar storage means fast reads for specific columns (e.g., just "LZ_HOUSTON" prices).
-   **Queryability**: Directly queryable by DuckDB, Polars, and AWS Athena/BigQuery.

### Access Layer: The `tinygrid` Client
The Python client becomes the query engine. We leverage **DuckDB** (pip installable, fast in-process SQL OLAP db) inside the library.

**Workflow:**
1.  User calls `ercot.get_spp(start="2022-01-01", end="2022-01-05")`.
2.  `tinygrid` detects this is "historical" (> 90 days or not in live API).
3.  Instead of hitting ERCOT's slow Archive API (zips), it generates S3 URLs:
    -   `s3://tinygrid-ercot/real_time_spp/year=2022/month=01/day=01/data.parquet`
    -   ...
4.  `tinygrid` uses DuckDB (or Pandas with pyarrow) to download and filter these files in parallel.
5.  Data is returned as a Pandas DataFrame, matching the live API format.

**Cost to Us**: $0 compute (client pays), ~$5/month storage.
**Cost to User**: Free (public bucket) or Freemium (presigned URLs).

## 2. Implementation Plan

### Phase 1: Ingestion & Backfill (The "Factory")
We need a robust pipeline to scrape ERCOT and build the Parquet lake.

**Stack**: Python script running on GitHub Actions (scheduled daily) or a small VPS.
**Tasks**:
1.  **Backfill**: Script to iterate 2011-2023, call `ERCOTArchive` (existing logic), download zips, convert to Parquet, upload to R2.
2.  **Daily Cron**: Script to run daily at ~2 AM CST.
    -   Fetch "Yesterday's" data from ERCOT Public API (while it's still there).
    -   **Capture Ephemeral Data**: This is key. Capture data that ERCOT deletes (e.g., real-time fuel mix, outages) and save to Parquet. This builds our unique moat.

### Phase 2: Client Upgrade
Update `tinygrid` library to prefer the S3 Parquet lake over ERCOT's Archive API.

-   Add dependency: `duckdb` or `pyarrow`.
-   Implement `ParquetArchive` class implementing the same interface as `ERCOTArchive`.
-   Add configuration: `ERCOT(use_cloud_archive=True)`.

### Phase 3: Differentiation Features

1.  **In-Process SQL**: Allow users to run SQL on the data locally.
    ```python
    ercot.query("SELECT avg(price) FROM 's3://.../spp.parquet' WHERE zone='LZ_HOUSTON'")
    ```
2.  **Ephemeral Data Replay**: "See the grid as it was". Replay real-time conditions (SCED bindings, outages) that are lost in official archives.
3.  **BigQuery/Snowflake Integration**: Since the data is in Parquet/S3, we can easily offer "External Tables" for enterprise users to mount our bucket into their warehouse.

## 3. Comparison to Grid Status

| Feature | Grid Status (Paid) | Tinygrid (Proposed) |
| :--- | :--- | :--- |
| **Historical Data** | Hosted Database | S3 Parquet Lake |
| **Access Method** | REST API / Snowflake | Python Client (DuckDB) / S3 Direct |
| **Cost Model** | Contact Sales | Free / Low Fixed Cost |
| **Performance** | API Latency | Network Bandwidth + Local CPU (Fast) |
| **Ephemeral Data** | Yes | Yes (if we start capturing now) |
| **Bus-Level LMPs** | Since Dec 2023 | Since Dec 2023 (same constraint) |

## 4. Immediate Next Steps
1.  **Proof of Concept**: Write `scripts/archive_to_parquet.py` to demonstrate downloading one day of archive, converting to Parquet, and querying with DuckDB.
2.  **Storage Setup**: Set up Cloudflare R2 bucket.
3.  **Client Integration**: Prototype `ParquetArchive` in `tinygrid`.
