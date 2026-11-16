create table fact_show_snapshot(
    show_key integer not null references dim_show(show_key),
    snapshot_date_key integer not null references dim_date(date_key),
    premiered_date_key integer not null references dim_date(date_key),
    ended_date_key integer not null references dim_date(date_key),
    rating_avg real,
    weight integer,
    runtime_min integer,
    average_runtime_min integer,
    primary key(show_key, snapshot_date_key)
);

-- Unlike dimensions (where NULLs are replaced with text placeholders to avoid empty groups),
-- fact measures stay NULL when missing: a missing rating is not 0, and SQL AVG() ignores NULLs whereas 0 would skew the average.
-- Using a single -1 key for both "unknown" (premiered) and "ongoing/not yet ended" (ended) is an intentional simplification for this project
insert into fact_show_snapshot(show_key, snapshot_date_key, premiered_date_key, ended_date_key, rating_avg, weight, runtime_min, average_runtime_min)
select dim_show.show_key,
    cast(strftime('%Y%m%d', ingested_at) as integer) as snapshot_date_key,
    coalesce(cast(strftime('%Y%m%d', premiered) as integer), -1) as premiered_date_key,
    coalesce(cast(strftime('%Y%m%d',ended) as integer), -1) as ended_date_key,
    rating_avg,
    weight,
    runtime_min,
    average_runtime_min
from silver_shows
join dim_show
on silver_shows.show_id = dim_show.show_id;
