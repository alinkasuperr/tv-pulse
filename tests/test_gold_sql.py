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
