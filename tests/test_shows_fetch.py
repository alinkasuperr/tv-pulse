from typing import Any, cast

import pytest
import requests

from tv_pulse.config import BASE_URL, REQUEST_TIMEOUT
from tv_pulse.ingest.shows import get_page, iter_pages


class FakeResponse:
    def __init__(self, status_code: int, payload: list[dict[str, Any]] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or []

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> list[dict[str, Any]]:
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.last_url: str | None = None
        self.last_timeout: float | None = None

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.last_url = url
        self.last_timeout = timeout
        return self.response


def make_session(
    status_code: int, payload: list[dict[str, Any]] | None = None
) -> tuple[FakeSession, requests.Session]:
    fake_session = FakeSession(FakeResponse(status_code, payload))
    return fake_session, cast(requests.Session, fake_session)


class FakeApi:
    def __init__(self, pages: dict[int, list[dict[str, Any]]]) -> None:
        self.pages = pages
        self.calls: list[int] = []

    def __call__(self, page: int) -> list[dict[str, Any]] | None:
        self.calls.append(page)
        return self.pages.get(page)


class SleepRecorder:
    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def test_get_page_returns_none_on_404() -> None:
    _, session = make_session(404)
    assert get_page(3, session=session) is None


def test_get_page_returns_data_and_passes_params() -> None:
    payload = [{"id": 1, "name": "Test Show"}]
    fake_session, session = make_session(200, payload)

    result = get_page(3, session=session)

    assert result == payload
    assert fake_session.last_url == f"{BASE_URL}/shows?page=3"
    assert fake_session.last_timeout == REQUEST_TIMEOUT


def test_get_page_raises_on_500() -> None:
    _, session = make_session(500)
    with pytest.raises(requests.HTTPError):
        get_page(0, session=session)


def test_iter_pages_stops_at_end() -> None:
    pages = {
        0: [{"id": 1, "name": "Show 1"}],
        1: [{"id": 2, "name": "Show 2"}],
    }
    api = FakeApi(pages)

    result = dict(iter_pages(api, max_pages=10, pause=0))

    assert result == pages
    assert api.calls == [0, 1, 2]


def test_iter_pages_stops_on_empty_list() -> None:
    api = FakeApi({0: [{"id": 1}], 1: []})

    result = dict(iter_pages(api, max_pages=10, pause=0))

    assert result == {0: [{"id": 1}]}
    assert api.calls == [0, 1]


def test_iter_pages_stops_at_max_pages() -> None:
    api = FakeApi({p: [{"id": p}] for p in range(100)})

    result = list(iter_pages(api, max_pages=3, pause=0))

    assert len(result) == 3
    assert api.calls == [0, 1, 2]


def test_iter_pages_pause_between_requests() -> None:
    api = FakeApi({p: [{"id": p}] for p in range(100)})
    sleeper = SleepRecorder()

    list(iter_pages(api, max_pages=3, pause=0.5, sleep_fn=sleeper))

    assert sleeper.calls == [0.5, 0.5]


def test_iter_pages_no_pause_when_zero() -> None:
    api = FakeApi({p: [{"id": p}] for p in range(100)})
    sleeper = SleepRecorder()

    list(iter_pages(api, max_pages=3, pause=0, sleep_fn=sleeper))

    assert sleeper.calls == []


def test_iter_pages_empty_on_immediate_404() -> None:
    api = FakeApi({})

    result = list(iter_pages(api, max_pages=5, pause=0))

    assert result == []
    assert api.calls == [0]


def test_iter_pages_is_lazy_and_pauses_only_between_steps() -> None:
    api = FakeApi({p: [{"id": p}] for p in range(100)})
    sleeper = SleepRecorder()

    gen = iter_pages(api, max_pages=5, pause=0.5, sleep_fn=sleeper)

    first = next(gen)
    assert first == (0, [{"id": 0}])
    assert api.calls == [0]
    assert sleeper.calls == []

    second = next(gen)
    assert second == (1, [{"id": 1}])
    assert api.calls == [0, 1]
    assert sleeper.calls == [0.5]
