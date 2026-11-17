-- Returns the absolute row count difference between the two tables (0 means exact match)
select abs((select count(*) from bridge_show_genre) - (select count(*) from silver_show_genre));
