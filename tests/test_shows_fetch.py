from typing import Any, cast

import pytest
import requests

from tv_pulse.config import BASE_URL, REQUEST_TIMEOUT
from tv_pulse.ingest.shows import PageFetchError, get_page, iter_pages


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
    def __init__(self, outcomes: list[FakeResponse | Exception]) -> None:
        self.last_url: str | None = None
        self.last_timeout: float | None = None
        self.outcomes: list[FakeResponse | Exception] = outcomes
        self.calls: int = 0

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.calls += 1
        self.last_url = url
        self.last_timeout = timeout
        item = self.outcomes.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_session(
    outcomes: list[FakeResponse | Exception],
) -> tuple[FakeSession, requests.Session]:
    fake_session = FakeSession(outcomes)
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


def test_get_page_returns_none_on_404() -> None:
    fake_session, session = make_session([FakeResponse(404)])
    sleeper = SleepRecorder()

    result = get_page(3, session=session, sleep_fn=sleeper)

    assert result is None
    assert fake_session.calls == 1
    assert sleeper.calls == []


def test_get_page_returns_data_and_passes_params() -> None:
    payload = [{"id": 1, "name": "Test Show"}]
    fake_session, session = make_session([FakeResponse(200, payload)])

    result = get_page(3, session=session)

    assert result == payload
    assert fake_session.last_url == f"{BASE_URL}/shows?page=3"
    assert fake_session.last_timeout == REQUEST_TIMEOUT


def test_get_page_429_twice_then_200_exponential_backoff() -> None:
    payload = [{"id": 1, "name": "Show 1"}]
    fake_session, session = make_session(
        [FakeResponse(429), FakeResponse(429), FakeResponse(200, payload)]
    )
    sleeper = SleepRecorder()

    result = get_page(0, session=session, max_attempts=3, base_pause=1.0, sleep_fn=sleeper)

    assert result == payload
    assert fake_session.calls == 3
    assert sleeper.calls == [1.0, 2.0]


def test_get_page_always_500_raises_page_fetch_error() -> None:
    fake_session, session = make_session([FakeResponse(500), FakeResponse(500), FakeResponse(500)])
    sleeper = SleepRecorder()

    with pytest.raises(PageFetchError, match=r"page 2.*HTTP 500"):
        get_page(2, session=session, max_attempts=3, base_pause=1.0, sleep_fn=sleeper)

    assert fake_session.calls == 3
    assert sleeper.calls == [1.0, 2.0]


@pytest.mark.parametrize(
    "transient_outcome",
    [
        FakeResponse(429),
        FakeResponse(500),
        FakeResponse(502),
        FakeResponse(503),
        requests.Timeout("timed out"),
        requests.ConnectionError("connection reset"),
    ],
)
def test_get_page_retries_transient_errors(
    transient_outcome: FakeResponse | Exception,
) -> None:
    payload = [{"id": 1, "name": "Show 1"}]
    fake_session, session = make_session([transient_outcome, FakeResponse(200, payload)])
    sleeper = SleepRecorder()

    result = get_page(0, session=session, base_pause=1.0, sleep_fn=sleeper)

    assert result == payload
    assert fake_session.calls == 2
    assert sleeper.calls == [1.0]


@pytest.mark.parametrize("status_code", [400, 401, 403, 499])
def test_get_page_does_not_retry_non_404_client_errors(status_code: int) -> None:
    fake_session, session = make_session([FakeResponse(status_code)])
    sleeper = SleepRecorder()

    with pytest.raises(requests.HTTPError):
        get_page(0, session=session, max_attempts=3, base_pause=1.0, sleep_fn=sleeper)

    assert fake_session.calls == 1
    assert sleeper.calls == []


def test_get_page_exhausted_timeouts_raises_page_fetch_error() -> None:
    fake_session, session = make_session(
        [
            requests.Timeout("timeout 1"),
            requests.Timeout("timeout 2"),
            requests.Timeout("timeout 3"),
        ]
    )
    sleeper = SleepRecorder()

    with pytest.raises(PageFetchError) as exc_info:
        get_page(4, session=session, max_attempts=3, base_pause=1.0, sleep_fn=sleeper)

    assert exc_info.value.page == 4
    assert exc_info.value.last_error == "timeout 3"
    assert fake_session.calls == 3
    assert sleeper.calls == [1.0, 2.0]


def test_iter_pages_preserves_earlier_pages_on_failure() -> None:
    def flaky_fetch(page: int) -> list[dict[str, Any]] | None:
        if page == 0:
            return [{"id": 1, "name": "Page 0 Show"}]
        raise PageFetchError(page=page, max_attempts=3, last_error="HTTP 500")

    gen = iter_pages(flaky_fetch, max_pages=5, pause=0)
    first = next(gen)

    with pytest.raises(PageFetchError) as exc_info:
        next(gen)

    assert first == (0, [{"id": 1, "name": "Page 0 Show"}])
    assert exc_info.value.page == 1
