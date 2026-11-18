-- Overall average is computed directly from fact_show_snapshot (5.78) rather than via bridge_show_genre
-- (which would skew it to 5.37 by counting multi-genre shows multiple times)
create view mart_genre_vs_overall as
    with genre_stats as(
        select
            dim_genre.genre,
            count(*) as shows_count,
            avg(fact_show_snapshot.rating_avg) as genre_avg
        from bridge_show_genre
        inner join fact_show_snapshot
        on bridge_show_genre.show_key = fact_show_snapshot.show_key
        inner join dim_genre
        on dim_genre.genre_key = bridge_show_genre.genre_key
        where fact_show_snapshot.rating_avg is not null
        group by genre
    ),
    overall_stats as(
        select
            avg(rating_avg) as overall_avg
        from fact_show_snapshot
        where fact_show_snapshot.rating_avg is not null
    )
select
    genre,
    shows_count,
    round(genre_avg, 2) as genre_avg,
    round(overall_avg, 2) as overall_avg,
    round(genre_avg - overall_avg, 2) as diff_avg
from genre_stats
cross join overall_stats;
