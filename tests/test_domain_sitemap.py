"""Unit tests for the pure sitemap domain layer."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hugesitemap.domain import (
    MAX_URLS,
    ChangeFreq,
    SitemapEntry,
    compile_filters,
    format_priority,
    is_dropped,
    iso8601_z,
    join_url,
    mtime_to_utc,
)

# --- formatting -----------------------------------------------------------


def test_mtime_to_utc_is_timezone_aware() -> None:
    moment = mtime_to_utc(1341994580.0)
    assert moment.tzinfo is timezone.utc
    assert moment.year == 2012


def test_iso8601_z_renders_trailing_z() -> None:
    moment = datetime(2012, 7, 11, 14, 16, 20, tzinfo=timezone.utc)
    assert iso8601_z(moment) == "2012-07-11T14:16:20Z"


def test_iso8601_z_assumes_naive_is_utc() -> None:
    assert iso8601_z(datetime(2020, 1, 2, 3, 4, 5)) == "2020-01-02T03:04:05Z"


def test_iso8601_z_converts_aware_to_utc() -> None:
    from datetime import timedelta

    plus_two = timezone(timedelta(hours=2))
    moment = datetime(2012, 7, 11, 16, 16, 20, tzinfo=plus_two)
    assert iso8601_z(moment) == "2012-07-11T14:16:20Z"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.5, "0.5000"), (1.0, "1.0000"), (0.1, "0.1000"), (0.12345, "0.1235")],
)
def test_format_priority_four_decimals(value: float, expected: str) -> None:
    assert format_priority(value) == expected


@pytest.mark.parametrize(
    ("prefix", "relpath", "expected"),
    [
        ("https://x.test/a000/", "000/f.pdf", "https://x.test/a000/000/f.pdf"),
        ("https://x.test/a000", "000/f.pdf", "https://x.test/a000/000/f.pdf"),
        ("https://x.test/a000/", "", "https://x.test/a000/"),
        ("https://x.test/a000", "/000/", "https://x.test/a000/000"),
    ],
)
def test_join_url(prefix: str, relpath: str, expected: str) -> None:
    assert join_url(prefix, relpath) == expected


_SEGMENT = st.text(alphabet="abcXYZ0123_-.", min_size=0, max_size=12)


@given(segment=_SEGMENT, relpath=_SEGMENT)
def test_join_url_no_double_slash_at_boundary(segment: str, relpath: str) -> None:
    # Clean, slash-free inputs: join_url must never introduce a doubled slash.
    prefix = "https://x.test/" + segment
    result = join_url(prefix, relpath)
    after_scheme = result.split("://", 1)[1]
    assert "//" not in after_scheme


# --- filters --------------------------------------------------------------


def test_wildcard_drop_matches_suffix() -> None:
    matchers = compile_filters(("*~",))
    assert is_dropped("file.txt~", matchers)
    assert not is_dropped("file.txt", matchers)


def test_regex_drop_matches_hidden_dotfiles() -> None:
    matchers = compile_filters((r"re:/\.[^/]*",))
    assert is_dropped(".hidden", matchers)
    assert is_dropped("sub/.secret", matchers)
    assert not is_dropped("sub/visible.pdf", matchers)


def test_filters_apply_in_order_any_match_drops() -> None:
    matchers = compile_filters(("*.txt*", "*.log*", "*/zsvc/z_content/*"))
    assert is_dropped("notes.txt", matchers)
    assert is_dropped("server.log.1", matchers)
    assert is_dropped("a000/zsvc/z_content/x.pdf", matchers)
    assert not is_dropped("a000/keep.pdf", matchers)


def test_empty_filters_drop_nothing() -> None:
    assert not is_dropped("anything/here.pdf", compile_filters(()))


def test_filters_normalise_backslashes() -> None:
    matchers = compile_filters(("*/zsvc/*",))
    assert is_dropped("a000\\zsvc\\file.pdf", matchers)


# --- limits ---------------------------------------------------------------


def _entry(loc: str = "u") -> SitemapEntry:
    return SitemapEntry(loc=loc, lastmod=None, priority=0.5)


def test_max_urls_is_protocol_value() -> None:
    assert MAX_URLS == 50_000


# --- model / enums --------------------------------------------------------


def test_sitemap_entry_is_frozen() -> None:
    entry = _entry()
    with pytest.raises((AttributeError, TypeError)):
        entry.loc = "other"  # type: ignore[misc]


def test_changefreq_values() -> None:
    assert ChangeFreq.YEARLY == "yearly"
    assert ChangeFreq.MONTHLY.value == "monthly"
