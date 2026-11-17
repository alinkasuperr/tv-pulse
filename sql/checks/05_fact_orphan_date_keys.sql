-- In SQLite, foreign keys prevent orphans when enabled, but cloud data warehouses (Redshift, BigQuery, Snowflake) do not enforce FKs, making these checks the primary defense
-- Returns the number of violating rows found (0 means no violations)
select count(*)
from fact_show_snapshot f
left join dim_date d_snap
on f.snapshot_date_key = d_snap.date_key
left join dim_date d_prem
on f.premiered_date_key = d_prem.date_key
left join dim_date d_end
on f.ended_date_key = d_end.date_key
where d_snap.date_key is Null or d_prem.date_key is Null or d_end.date_key is Null;
