import sqlite3

import pytest


def test_dim_genre_row_count(gold_conn: sqlite3.Connection) -> None:
    query = "select count(*) from dim_genre"
    result = gold_conn.execute(query).fetchone()[0]

    assert result == 4


def test_dim_genre_keys_sequential(gold_conn: sqlite3.Connection) -> None:
    query = "select genre_key from dim_genre order by genre_key"
    result = gold_conn.execute(query).fetchall()
    res = [row[0] for row in result]

    assert res == [1, 2, 3, 4]


def test_dim_genre_alphabet_order(gold_conn: sqlite3.Connection) -> None:
    query = "select genre from dim_genre order by genre_key"
    result = gold_conn.execute(query).fetchall()

    res = [row[0] for row in result]

    assert res == ["Comedy", "Drama", "Horror", "Sci-Fi"]


def test_dim_genre_unique_constraint(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        gold_conn.execute("insert into dim_genre (genre_key, genre) values (99, 'Drama')")


def test_dim_show_row_count(gold_conn: sqlite3.Connection) -> None:
    result = gold_conn.execute("select count(*) from dim_show").fetchone()[0]
    result_silver = gold_conn.execute("select count(*) from silver_shows").fetchone()[0]

    assert result == result_silver


def test_dim_show_id_unique(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="show_id"):
        gold_conn.execute(
            "insert into dim_show (show_id, show_key, name, network_name, "
            "network_country, imdb_id) "
            "values (1, 99, 'Test', 'Net', 'Country', 'tt000')"
        )


def test_dim_show_keys_sequential(gold_conn: sqlite3.Connection) -> None:
    result = gold_conn.execute("select show_key from dim_show order by show_id").fetchall()
    res = [row[0] for row in result]

    assert res == [1, 2, 3, 4]


def test_dim_show_missing_nulls(gold_conn: sqlite3.Connection) -> None:
    result_network = gold_conn.execute(
        "select network_name from dim_show where show_id = 2"
    ).fetchone()[0]
    result_country = gold_conn.execute(
        "select network_country from dim_show where show_id = 2"
    ).fetchone()[0]
    result_imdb = gold_conn.execute("select imdb_id from dim_show where show_id = 3").fetchone()[0]
    result = gold_conn.execute(
        "select count(*) from dim_show where network_name is null or network_country"
        " is null or imdb_id is null"
    ).fetchone()[0]

    assert result_network == "no network"
    assert result_country == "no country"
    assert result_imdb == "no imdb"
    assert result == 0


def test_dim_show_cyrillic(gold_conn: sqlite3.Connection) -> None:
    result = gold_conn.execute("select name from dim_show where show_id = 2").fetchone()[0]

    assert result == "Дивні дива"


def test_dim_show_not_null_constraint(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="network_name"):
        gold_conn.execute(
            "insert into dim_show (show_key, show_id, name, network_name"
            ", network_country, imdb_id) values (99, 999, 'Test'"
            ", NULL, 'Country', 'tt000')"
        )
