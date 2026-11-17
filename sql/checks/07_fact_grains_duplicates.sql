-- Returns the number of violating rows found (0 means no violations)
select count(*)
from (select show_key, snapshot_date_key from fact_show_snapshot group by show_key, snapshot_date_key having count(*)>1);
