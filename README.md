# The tv-pulse project

A data engineering practice project that covers three medallion layers: it extracts data, transforms it and builds analytics-ready tables, so analytical queries and dashboards can be built on top of it. It uses such helpful tools as:

- Ruff for linting and formatting
- Mypy for type checking
- Pytest for testing
- Pre-commit for checks before every commit
- GitHub Actions for CI

In addition, released under the MIT License _(see LICENSE)_

### For what
A data pipeline that collects TV show data from TVmaze API and builds analytics-ready tables

### Architecture

Flowchart schema
```mermaid
flowchart LR
    API([TVmaze API]) -->|JSON / ingest/shows.py| Bronze[(Bronze Layer)]
    Bronze -->|Parquet / transform/shows_silver.py| Silver[(Silver Layer)]
    Silver -->|SQLite / load.py + sql/gold| Gold[(Gold Layer)]
    Gold -->|SQL views / sql/marts| Marts([Data Marts])
```

Folders tree
```text
tv-pulse/
├── .github/workflows/     CI (GitHub Actions)
├── data/                  not in git: bronze/, silver/, gold/tv_pulse.db
├── sql/
│   ├── gold/              star schema tables
│   ├── checks/            data quality checks
│   └── marts/             analytical views
├── src/tv_pulse/
│   ├── config.py          paths and API settings
│   ├── ingest/            API -> Bronze
│   ├── transform/         Bronze -> Silver
│   └── gold/              Silver -> SQLite, SQL runner
├── tests/
├── .pre-commit-config.yaml
├── pyproject.toml
└── README.md
```

### Schema of the pipeline
Bronze (JSON) -> Silver (Parquet) -> Gold (SQLite, star schema)

- Bronze - the first layer. Raw data from the API is saved here unchanged in JSON format, so it can always be reprocessed without new requests
- Silver - the middle layer with all transformation functions: renaming, types, cleaning and validation. In the end the data is saved in Parquet format
- Gold - the last layer with a star schema and data quality checks. Analytical marts with window functions are built on top of the star schema

_Tables of gold (and their grain):_

- dim_genre - all unique genres (grain: one row per unique genre)
- dim_show - all shows and information about them (grain: one row per show)
- dim_date - a calendar with every day between the earliest and the latest date (premiered, ended, ingested), plus -1 for unknown dates (grain: one row per calendar day)
- bridge_show_genre - a bridge n:m linking shows and genres (grain: one row per show and genre pair)
- fact_show_snapshot - measures of shows (rating, weight, runtime) (grain: one row per show per ingestion snapshot date)

### Description about SQL marts
Marts are SQL views built on top of the star schema (`sql/marts/`). They answer simple analytical questions about the real data and are rebuilt together with Gold by `python -m tv_pulse.gold.build`

1. top_shows_by_genre - the first mart with the window function row_number, which gives the top three shows inside every genre by rating (ties are broken by title)
2. genre_vs_overall - compares the average rating of every genre with the overall average. The overall average is taken from the fact table directly, not through the bridge, otherwise multi-genre shows would be counted several times
3. yearly_trend - average rating by premiere year: lag shows the previous year with data and the change, and a 3-year rolling average (range frame) is calculated for every year
4. show_vs_network - compares every show rating with the average rating of its network (shows without a network and networks with a single show are excluded)
5. rating_quartiles - the final mart divides all rated shows into four groups by ntile (quartile 1 has the highest ratings, groups can differ by one show)

### Helpful commands to execute the pipeline and tests
Run all commands from the project root. The first pipeline command needs internet access, because it calls the TVmaze API. The `data/` folder is not stored in the repository.

0. pip install -e ".[dev]"
1. python -m tv_pulse.ingest.shows
2. python -m tv_pulse.transform.shows_silver
3. python -m tv_pulse.gold.build
4. pytest -v

### Pagination and configs
Added a single `config.py` module to keep all project paths and API settings in one place instead of hardcoded values:

- Paths are calculated from the project root, so the pipeline works from any folder
- All configured pages of the TVmaze API are loaded and transformed (controlled by `MAX_PAGES`), with a pause between requests
- Silver reads all pages of the latest ingestion date and stops if a page is missing
- API fetching, pagination and retries are covered by tests

### Retries
A request is repeated up to `MAX_ATTEMPTS` times with a growing pause (1, 2, 4 seconds...) on HTTP 429, 5xx, timeouts and connection errors. Other errors (for example 400) stop the run at once, and a 404 means the end of the list. If all attempts fail, the run stops with a clear error. Pages saved before the failure stay in Bronze, and a rerun overwrites them with the same data.

### Limitations
- Silver and Gold are built from the latest Bronze ingestion date only, so the fact table has one snapshot date for now
- Marts expect a single snapshot date; a filter for the latest snapshot is needed when several ingestions appear
- Planned: a manifest file written after a complete ingestion, so Silver reads only complete runs (now leftover pages of an earlier run on the same date can be mixed into Silver)
- The `Retry-After` header and responses with an invalid JSON body are not handled
- The `main` functions are not covered by tests
- Explicit SQL integrity checks are kept even though SQLite enforces foreign keys when enabled, as preparation for cloud data warehouses (Redshift, BigQuery, Snowflake) where foreign keys are not enforced

### Results
Calculated on the data loaded with `MAX_PAGES = 5` (ingestion date 2026-11-27), so it is only a part of the TVmaze catalog.

- Total loaded shows: 1208
- Show-genre pairs: 2477
- Premiere years span: 60 years
- Shows without rating: 152
- Overall average rating: 7.41
- Peak premiere year by average rating: 1997 (12 rated shows, average 7.86)
- Top-3 shows in Drama: Breaking Bad, Band of Brothers, Firefly

Genres with the highest average rating (genres with at least 10 rated shows):

| Genre | Rated shows | Average rating |
|---|---|---|
| War | 18 | 7.91 |
| Espionage | 13 | 7.83 |
| Medical | 25 | 7.77 |
| Anime | 11 | 7.76 |

### Source of data
Data provided by [TvmazeAPI](https://www.tvmaze.com/api), licensed under CC BY-SA 4.0

Status: completed v1

### Next steps
Planned updates:

- Orchestrating the pipeline with Apache Airflow
- Spark / Databricks for bigger volumes of data
