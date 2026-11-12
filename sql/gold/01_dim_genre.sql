create table dim_genre(
genre_key integer primary key,
genre text not null unique
);

-- keys are stable only within a single run; in production storage, they are stored separately
insert into dim_genre (genre_key, genre)
select row_number() over (order by genre) as genre_key, genre
from (
select distinct genre
from silver_show_genre
);
