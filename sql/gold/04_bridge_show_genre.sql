create table bridge_show_genre(
    show_key integer not null references dim_show(show_key),
    genre_key integer not null references dim_genre(genre_key),
    primary key(show_key, genre_key)
);

-- Per-genre sums and averages are safe via the bridge, as each show appears once per genre.
-- Grand totals (overall sums and averages) distort both metrics by counting multi-genre shows multiple times; calculate those directly from the fact table
insert into bridge_show_genre(show_key, genre_key)
select distinct dim_show.show_key, dim_genre.genre_key
from silver_show_genre
join dim_show on silver_show_genre.show_id = dim_show.show_id
join dim_genre on silver_show_genre.genre = dim_genre.genre;
