-- Exclude 'no network' placeholder and single-show networks (count < 2) where diff from network average is always zero noise
create view mart_show_vs_network as
    with cte as(
    select
        dim_show.show_id,
        dim_show.name,
        dim_show.network_name,
        fact_show_snapshot.rating_avg,
        avg(fact_show_snapshot.rating_avg) over(partition by dim_show.network_name) as rating_by_network,
        count(*) over(partition by dim_show.network_name) as network_shows_count
    from dim_show
    inner join fact_show_snapshot
    on dim_show.show_key = fact_show_snapshot.show_key
    where dim_show.network_name != 'no network' and fact_show_snapshot.rating_avg is not null
)
select
    show_id,
    name,
    network_name,
    rating_avg,
    round(rating_by_network, 2) as rating_by_network,
    round(rating_avg - rating_by_network, 2) as diff_from_network,
    network_shows_count
from cte
where network_shows_count >= 2;
