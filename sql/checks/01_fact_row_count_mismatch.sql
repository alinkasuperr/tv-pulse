-- Returns the absolute row count difference between the two tables (0 means exact match)
select abs((select count(*) from fact_show_snapshot) - (select count(*) from silver_shows));
