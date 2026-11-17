create table dim_show(
    show_key integer primary key,
    show_id integer unique not null,
    name text not null,
    type text,
    language text,
    status text,
    network_name text not null,
    network_country text not null,
    imdb_id text not null,
    url text
);

-- NULL in network/imdb means absence (e.g., streaming shows without TV network or unlinked IMDb), not unknown data
insert into dim_show(show_key,
    show_id, name, type, language, status,network_name,
    network_country, imdb_id, url)
select
    row_number() over (order by show_id) as show_key,
    show_id, name, type, language, status,
    coalesce(network_name, 'no network') as network_name,
    coalesce(network_country, 'no country') as network_country,
    coalesce(imdb_id, 'no imdb') as imdb_id,
    url
from silver_shows;
