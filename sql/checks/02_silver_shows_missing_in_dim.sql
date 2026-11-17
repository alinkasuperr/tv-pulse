-- Returns the number of violating rows found (0 means no violations)
select count(*)
from silver_shows left join dim_show
on silver_shows.show_id = dim_show.show_id
where dim_show.show_id is Null;
