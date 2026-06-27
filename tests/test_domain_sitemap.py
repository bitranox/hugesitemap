"""Unit tests for the pure sitemap domain layer."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hugesitemap.domain import (
    MAX_URLS,
    ChangeFreq,
    FilterSpec,
    SitemapEntry,
    format_priority,
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


# --- filters (FilterSpec value object) ------------------------------------


def test_filter_spec_defaults_are_empty() -> None:
    spec = FilterSpec()
    assert spec.patterns == ()
    assert spec.ignore_file is None
    assert spec.nested_ignore_filename is None
    assert spec.is_empty


def test_filter_spec_with_any_source_is_not_empty() -> None:
    assert not FilterSpec(patterns=("*~",)).is_empty
    assert not FilterSpec(ignore_file="/etc/rules").is_empty
    assert not FilterSpec(nested_ignore_filename=".sitemapignore").is_empty


def test_filter_spec_is_frozen_and_hashable() -> None:
    spec = FilterSpec(patterns=("*.txt", ".*"))
    assert hash(spec) == hash(FilterSpec(patterns=("*.txt", ".*")))
    with pytest.raises(AttributeError):
        spec.patterns = ()  # type: ignore[misc]


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
