-- Weighted rolling 3-year average (sum of ratings / sum of shows in window) accounts for varying show counts per year
create view mart_yearly_trend as
    with yearly_stats as(
    select
        dim_date.year,
        count(fact_show_snapshot.rating_avg) as shows_count,
        sum(fact_show_snapshot.rating_avg) as rating_sum,
        avg(fact_show_snapshot.rating_avg) as avg_rating
    from dim_date
    inner join fact_show_snapshot
    on dim_date.date_key = fact_show_snapshot.premiered_date_key
    where fact_show_snapshot.premiered_date_key != -1 and fact_show_snapshot.rating_avg is not null
    group by dim_date.year
)
select
    year,
    shows_count,
    rating_sum,
    round(avg_rating, 2) as rating_avg,
    lag(year) over(order by year) as prev_year,
    lag(avg_rating) over(order by year) as prev_year_rating,
    round(avg_rating - lag(avg_rating) over(order by year), 2) as diff_year_rating,
    round(sum(rating_sum) over(order by year range between 2 preceding  and current row)
     / sum(shows_count) over(order by year range between 2 preceding  and current row), 2) as rolling_avg
from yearly_stats;
