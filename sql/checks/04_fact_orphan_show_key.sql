-- In SQLite, foreign keys prevent orphans when enabled, but cloud data warehouses (Redshift, BigQuery, Snowflake) do not enforce FKs, making these checks the primary defense
-- Returns the number of violating rows found (0 means no violations)
select count(*)
from fact_show_snapshot left join dim_show
on fact_show_snapshot.show_key = dim_show.show_key
where dim_show.show_key is Null;
