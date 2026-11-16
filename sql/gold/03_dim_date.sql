create table dim_date(
    date_key integer primary key,
    full_date text unique,
    year integer,
    month integer,
    quarter integer,
    decade integer,
    day_name text
);

insert into dim_date (date_key, full_date, year, month, quarter, decade, day_name)
with recursive
    all_dates as(
        select premiered as d from silver_shows where premiered is not null
        union all
        select ended as d from silver_shows where ended is not null
        union all
        select ingested_at as d from silver_shows where ingested_at is not null
    ),
    bound as (
        select max(date(d)) as max_date, min(date(d)) as min_date from all_dates
    ),
    calendar(d, max_date) as(
        select min_date, max_date from bound
        union all
        select date(d, '+1 day'), max_date from calendar
        where d < max_date
)
select cast(strftime('%Y%m%d', d) as integer) as date_key,
d as full_date,
cast(strftime('%Y', d) as integer) as year,
cast(strftime('%m', d) as integer) as month,
((cast(strftime('%m', d) as integer) - 1) / 3 + 1 ) as quarter,
(cast(strftime('%Y', d) as integer) / 10 * 10) as decade,
case cast(strftime('%w', d) as integer) when 0 then 'Sunday' when 1 then 'Monday' when 2 then 'Tuesday'
    when 3 then 'Wednesday' when 4 then 'Thursday' when 5 then 'Friday'
    when 6 then 'Saturday' end as day_name
from calendar;

-- Text attributes use 'unknown' for grouping consistency (like dim_show); numeric/date fields stay NULL
insert into dim_date (date_key, full_date, year, month, quarter, decade, day_name)
values (-1, null, null, null, null, null, 'unknown');
