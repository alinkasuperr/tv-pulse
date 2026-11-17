# The tv-pulse project

A data engineering practice project that covers three medallion layers: it extracts data, transforms it and builds analytics-ready tables, so analytical queries and dashboards can be built on top of it. It uses such helpful tools as:

- Ruff for linting and formatting
- Mypy for type checking
- Pytest for testing
- Pre-commit for local checks before every commit
- GitHub Actions for CI

In addition, released under the MIT License _(see LICENSE)_

### For what
A data pipeline that collects TV show data from TVmaze API and builds analytics-ready tables

### Schema of the pipeline
Bronze (JSON) -> Silver (Parquet) -> Gold (SQLite, star schema)

- Bronze (JSON) - the first layer. Raw data from the API is saved here unchanged in JSON format, so it can always be reprocessed without new requests
- Silver (Parquet) - the middle layer with all transformation functions: renaming, types, cleaning and validation. In the end the data is saved in Parquet format
- Gold (SQLite) - the last layer with a star schema and data quality checks. Analytical marts with window functions are planned next

_Tables of gold (and their grain):_

- dim_genre - all unique genres (grain: one row per unique genre)
- dim_show - all shows and information about them (grain: one row per show)
- dim_date - a calendar with every day between the earliest and the latest date (premiered, ended, ingested), plus -1 for unknown dates (grain: one row per calendar day)
- bridge_show_genre - a bridge n:m linking shows and genres (grain: one row per show and genre pair)
- fact_show_snapshot - measures of shows (rating, weight, runtime) (grain: one row per show per ingestion snapshot date)

### Helpful commands to execute the pipeline and tests
Run all commands from the project root. The first pipeline command needs internet access, because it calls the TVmaze API. The `data/` folder is not stored in the repository.

0. pip install -e ".[dev]"
1. python -m tv_pulse.ingest.shows
2. python -m tv_pulse.transform.shows_silver
3. python -m tv_pulse.gold.build
4. pytest -v

### Limitations
- Only the first page of the TVmaze API is loaded and transformed for now
- Silver and Gold are built from the latest Bronze file only, so the fact table has one snapshot date for now
- File paths in the pipeline are relative to the project root
- Fetching from the API and the `main` functions are not covered by tests yet
- Explicit SQL integrity checks are kept even though SQLite enforces foreign keys when enabled, as preparation for cloud data warehouses (Redshift, BigQuery, Snowflake) where foreign keys are not enforced

### Source of data
Data provided by [TvmazeAPI](https://www.tvmaze.com/api), licensed under CC BY-SA 4.0

Status: work in progress
