create view  mart_top_shows_by_genre as
    with ranked as(
        select
            dim_show.show_key,
            dim_show.show_id,
            dim_show.name,
            dim_genre.genre_key,
            dim_genre.genre,
            fact_show_snapshot.rating_avg,
            -- choose the row_number over dense_rance because of not getting genres to take the same place
            row_number() over(
                partition by dim_genre.genre
                order by fact_show_snapshot.rating_avg desc, dim_show.name, dim_show.show_id asc)
            as top_shows
        from dim_show
        inner join bridge_show_genre
        on dim_show.show_key = bridge_show_genre.show_key
        inner join dim_genre
        on dim_genre.genre_key = bridge_show_genre.genre_key
        inner join fact_show_snapshot
        on fact_show_snapshot.show_key = dim_show.show_key
        where rating_avg is not null
    )
select
    genre,
    show_id,
    name,
    rating_avg,
    top_shows
from  ranked
where top_shows <= 3
order by genre, top_shows;
