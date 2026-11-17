-- In SQLite, foreign keys prevent orphans when enabled, but cloud data warehouses (Redshift, BigQuery, Snowflake) do not enforce FKs, making these checks the primary defense
-- Returns the number of violating rows found (0 means no violations)
select count(*)
from bridge_show_genre
left join dim_show on dim_show.show_key = bridge_show_genre.show_key
left join dim_genre on dim_genre.genre_key = bridge_show_genre.genre_key
where dim_show.show_key is Null or dim_genre.genre_key is Null;
