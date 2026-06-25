"""Pure formatting helpers for sitemap serialization.

These functions translate raw filesystem and numeric values into the exact
string and datetime shapes required by the sitemaps.org 0.9 protocol. They are
pure (no I/O, no framework dependencies) so they live in the domain layer and
can be exhaustively unit-tested.

Contents:
    * :func:`mtime_to_utc` - epoch seconds to a timezone-aware UTC datetime.
    * :func:`iso8601_z` - UTC datetime to ``YYYY-MM-DDTHH:MM:SSZ``.
    * :func:`format_priority` - float to a fixed 4-decimal string.
    * :func:`join_url` - join a URL prefix with a relative path.
"""

from __future__ import annotations

from datetime import datetime, timezone


def mtime_to_utc(mtime: float) -> datetime:
    """Convert epoch seconds (an ``os.stat`` mtime) to a UTC datetime.

    Args:
        mtime: Seconds since the Unix epoch, as returned by ``os.stat``.

    Returns:
        A timezone-aware :class:`datetime.datetime` in UTC.

    Example:
        >>> mtime_to_utc(1341994580.0).isoformat()
        '2012-07-11T08:16:20+00:00'
    """
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def iso8601_z(moment: datetime) -> str:
    """Render a datetime as full ISO8601 UTC with a trailing ``Z``.

    Naive datetimes are assumed to be UTC; aware datetimes are converted to UTC.

    Args:
        moment: The datetime to render.

    Returns:
        A string of the form ``YYYY-MM-DDTHH:MM:SSZ``.

    Example:
        >>> from datetime import datetime, timezone
        >>> iso8601_z(datetime(2012, 7, 11, 14, 16, 20, tzinfo=timezone.utc))
        '2012-07-11T14:16:20Z'
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_priority(value: float) -> str:
    """Render a priority as a fixed 4-decimal string (sitemaps.org range).

    Args:
        value: Priority between 0.0 and 1.0.

    Returns:
        The value formatted with exactly four decimal places.

    Example:
        >>> format_priority(0.5)
        '0.5000'
        >>> format_priority(1.0)
        '1.0000'
    """
    return f"{value:.4f}"


def join_url(prefix: str, relpath: str) -> str:
    """Join a URL prefix with a relative path, collapsing duplicate slashes.

    The relative path is expected to use forward slashes. A single ``/`` is
    placed between prefix and relpath; an empty ``relpath`` yields the prefix
    with a guaranteed trailing slash.

    Args:
        prefix: URL prefix, with or without a trailing slash.
        relpath: Forward-slash relative path (may be empty).

    Returns:
        The joined URL.

    Example:
        >>> join_url("https://media.example.com/a000/", "000/file.pdf")
        'https://media.example.com/a000/000/file.pdf'
        >>> join_url("https://media.example.com/a000", "")
        'https://media.example.com/a000/'
    """
    base = prefix.rstrip("/")
    tail = relpath.strip("/")
    if not tail:
        return f"{base}/"
    return f"{base}/{tail}"


__all__ = [
    "format_priority",
    "iso8601_z",
    "join_url",
    "mtime_to_utc",
]
