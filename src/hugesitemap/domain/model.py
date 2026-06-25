"""Pure value objects describing sitemap contents.

Frozen dataclasses with no I/O or framework dependencies. They model the
sitemaps.org 0.9 data shape: individual URL entries, a single ``<urlset>``
document, and an index child reference used when output is split.

Contents:
    * :class:`SitemapEntry` - one ``<url>`` entry.
    * :class:`SitemapDocument` - one ``<urlset>`` worth of entries.
    * :class:`SitemapIndexEntry` - one ``<sitemap>`` child in an index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SitemapEntry:
    """A single sitemap URL entry.

    Attributes:
        loc: Absolute URL of the entry.
        lastmod: Last-modification time (UTC), or ``None`` to omit.
        priority: Crawl priority in the 0.0-1.0 range.
        changefreq: Optional change-frequency hint, or ``None`` to omit.

    Example:
        >>> from datetime import datetime, timezone
        >>> entry = SitemapEntry(
        ...     loc="https://media.example.com/a000/",
        ...     lastmod=datetime(2012, 7, 11, 14, 16, 20, tzinfo=timezone.utc),
        ...     priority=0.5,
        ... )
        >>> entry.changefreq is None
        True
    """

    loc: str
    lastmod: datetime | None
    priority: float
    changefreq: str | None = None


@dataclass(frozen=True, slots=True)
class SitemapDocument:
    """One ``<urlset>`` document: an ordered collection of entries.

    Attributes:
        entries: The URL entries, in emission order.

    Example:
        >>> SitemapDocument(entries=()).entries
        ()
    """

    entries: tuple[SitemapEntry, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SitemapIndexEntry:
    """A child sitemap reference inside a ``<sitemapindex>``.

    Attributes:
        loc: Absolute URL of the child sitemap file.
        lastmod: Newest entry time within that child (UTC), or ``None``.

    Example:
        >>> SitemapIndexEntry(loc="https://media.example.com/sitemap1.xml", lastmod=None).loc
        'https://media.example.com/sitemap1.xml'
    """

    loc: str
    lastmod: datetime | None


__all__ = [
    "SitemapDocument",
    "SitemapEntry",
    "SitemapIndexEntry",
]
