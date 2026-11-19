create view mart_top_shows_by_genre as
    with ranked as(
        select
            dim_show.show_id,
            dim_show.name,
            dim_genre.genre,
            fact_show_snapshot.rating_avg,
            -- ROW_NUMBER guarantees exactly three rows per genre, with ties broken by title, then by show_id
            row_number() over(
                partition by dim_genre.genre
                order by fact_show_snapshot.rating_avg desc, dim_show.name, dim_show.show_id asc)
            as rank_in_genre
        from dim_show
        inner join bridge_show_genre
        on dim_show.show_key = bridge_show_genre.show_key
        inner join dim_genre
        on dim_genre.genre_key = bridge_show_genre.genre_key
        inner join fact_show_snapshot
        on fact_show_snapshot.show_key = dim_show.show_key
        -- Exclude unrated shows so NULL ratings do not pollute top rankings
        where fact_show_snapshot.rating_avg is not null
    )
select
    genre,
    show_id,
    name,
    rating_avg,
    rank_in_genre
from  ranked
where rank_in_genre <= 3;
