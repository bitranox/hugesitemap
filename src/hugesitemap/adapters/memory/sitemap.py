"""In-memory fakes for the sitemap ports, for fast tests.

Provides a configurable content source, a writer spy that records calls instead
of touching disk, and a canned site-config loader. These let the use case and
CLI be exercised without a filesystem or lxml.

Contents:
    * :class:`InMemoryContentSource` - returns preset entries per root.
    * :func:`content_source_empty` - a content source that yields nothing.
    * :class:`SitemapWriterSpy` - records write calls, returns the output path.
    * :func:`load_site_config_in_memory` - returns a minimal canned SiteConfig.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from hugesitemap.adapters.config.site_loader import SiteConfig, load_sites

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lib_layered_config import Config

    from hugesitemap.domain.filters import FilterSpec
    from hugesitemap.domain.model import SitemapDocument, SitemapEntry


class InMemoryContentSource:
    """A content source returning preset entries keyed by on-disk root."""

    def __init__(self, entries_by_root: dict[str, list[SitemapEntry]] | None = None) -> None:
        self.entries_by_root = entries_by_root or {}

    def __call__(
        self,
        *,
        root: str,
        url_prefix: str,
        filter_spec: FilterSpec,
        default_priority: float,
        directory_urls: bool = True,
    ) -> list[SitemapEntry]:
        """Return the entries registered for ``root`` (empty if none)."""
        return list(self.entries_by_root.get(root, []))


def content_source_empty(
    *,
    root: str,
    url_prefix: str,
    filter_spec: FilterSpec,
    default_priority: float,
    directory_urls: bool = True,
) -> list[SitemapEntry]:
    """A content source that yields nothing (default for build_testing)."""
    return []


@dataclass
class _WriteCall:
    """A single recorded :class:`SitemapWriterSpy` invocation."""

    documents: tuple[SitemapDocument, ...]
    output_path: Path
    base_url: str
    gzip: bool


def _no_calls() -> list[_WriteCall]:
    """Typed empty default for the spy's ``calls`` list."""
    return []


@dataclass
class SitemapWriterSpy:
    """Records write calls without touching disk; returns the output path."""

    calls: list[_WriteCall] = field(default_factory=_no_calls)

    def __call__(
        self,
        *,
        documents: Iterable[SitemapDocument],
        output_path: Path,
        base_url: str,
        gzip: bool = False,
    ) -> list[Path]:
        """Record the call (materialising the stream) and return ``[output_path]``."""
        self.calls.append(_WriteCall(tuple(documents), Path(output_path), base_url, gzip))
        return [Path(output_path)]


def load_sites_in_memory(config: Config) -> list[SiteConfig]:
    """Read sites from an in-memory ``Config`` using the real validation logic.

    Delegates to :func:`load_sites` so injected test configurations containing a
    ``[[site]]`` array are validated exactly as in production, with no I/O.
    """
    return load_sites(config)


__all__ = [
    "InMemoryContentSource",
    "SitemapWriterSpy",
    "content_source_empty",
    "load_sites_in_memory",
]
