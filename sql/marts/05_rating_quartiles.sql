-- Quartile 1 represents the highest ratings; remainder rows from uneven division go to the first bucket
-- NTILE splits by row position rather than value, so tied ratings (ordered by show_id) can land in adjacent quartiles
create view mart_rating_quartiles as
select
dim_show.show_id,
dim_show.name,
dim_show.network_name,
fact_show_snapshot.rating_avg,
ntile(4) over(order by rating_avg desc, show_id asc) as rating_quartile
from dim_show
inner join fact_show_snapshot
on fact_show_snapshot.show_key = dim_show.show_key
where fact_show_snapshot.rating_avg is not null;
