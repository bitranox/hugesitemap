"""The GenerateSitemap use case and its request/response DTOs.

Pure orchestration over the :class:`ContentSource` and :class:`SitemapWriter`
ports. This module imports only domain types and stdlib; it never touches the
filesystem or lxml directly, so the same use case runs against in-memory fakes
in tests and real adapters in production.

Memory: entries are streamed, never fully materialised. The use case yields
sitemap documents lazily (one chunk of at most :data:`MAX_URLS` entries at a
time) and the writer pulls them one by one, so peak memory is bounded by a
single chunk regardless of how many URLs the site has.

Contents:
    * :class:`DirectoryRequest` - one on-disk root mapped to a URL prefix.
    * :class:`GenerateRequest` - the full input for one site.
    * :class:`GenerateResult` - the outcome (URL count, paths, split flag).
    * :func:`generate_sitemap` - the use case.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ..domain.filters import FilterSpec
from ..domain.limits import MAX_URLS
from ..domain.model import SitemapDocument, SitemapEntry

if TYPE_CHECKING:
    from .ports import ContentSource, SitemapWriter


@dataclass(frozen=True, slots=True)
class DirectoryRequest:
    """One configured directory: an on-disk root and its URL prefix.

    Attributes:
        root: Absolute on-disk path to walk.
        url_prefix: URL prefix that ``root`` maps to.
    """

    root: str
    url_prefix: str


@dataclass(frozen=True, slots=True)
class GenerateRequest:
    """Everything the use case needs to generate one site's sitemap.

    Attributes:
        base_url: Site base URL (used to build child sitemap URLs on split).
        output_path: Destination path for ``sitemap.xml``.
        gzip: Whether to write gzip-compressed output.
        default_priority: Priority assigned to every walked entry.
        directories: Configured directories to walk.
        explicit_entries: Extra entries from ``[[url]]`` config blocks.
        filter_spec: Path-exclusion rules (gitignore semantics).
        dry_run: When true, walk and count but do not write.
    """

    base_url: str
    output_path: str
    gzip: bool
    default_priority: float
    directories: tuple[DirectoryRequest, ...]
    explicit_entries: tuple[SitemapEntry, ...] = ()
    filter_spec: FilterSpec = field(default_factory=FilterSpec)
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class GenerateResult:
    """The outcome of a generate run.

    Attributes:
        url_count: Total number of URL entries emitted.
        paths_written: Files written (empty on dry-run).
        was_split: Whether output was split into an index + children.
    """

    url_count: int
    paths_written: tuple[Path, ...] = field(default_factory=tuple)
    was_split: bool = False


@dataclass(slots=True)
class _StreamStats:
    """Mutable counters updated as the document stream is consumed."""

    urls: int = 0
    documents: int = 0


def _iter_entries(
    request: GenerateRequest,
    content_source: ContentSource,
) -> Iterator[SitemapEntry]:
    """Yield every entry for the request, one at a time (no materialisation)."""
    for directory in request.directories:
        yield from content_source(
            root=directory.root,
            url_prefix=directory.url_prefix,
            filter_spec=request.filter_spec,
            default_priority=request.default_priority,
        )
    yield from request.explicit_entries


def _stream_documents(
    request: GenerateRequest,
    content_source: ContentSource,
    stats: _StreamStats,
) -> Iterator[SitemapDocument]:
    """Yield sitemap documents lazily, each holding at most ``MAX_URLS`` entries.

    Buffers at most one chunk at a time and updates ``stats`` as it goes. Always
    yields at least one document (an empty ``<urlset>`` when there are no
    entries), so the writer always produces an output file.
    """
    buffer: list[SitemapEntry] = []
    for entry in _iter_entries(request, content_source):
        buffer.append(entry)
        stats.urls += 1
        if len(buffer) >= MAX_URLS:
            stats.documents += 1
            yield SitemapDocument(entries=tuple(buffer))
            buffer = []
    if buffer or stats.documents == 0:
        stats.documents += 1
        yield SitemapDocument(entries=tuple(buffer))


def generate_sitemap(
    request: GenerateRequest,
    *,
    content_source: ContentSource,
    write_sitemap: SitemapWriter,
) -> GenerateResult:
    """Generate a sitemap for one site.

    Streams every configured directory and the explicit URLs through
    ``content_source``, chunks them into protocol-compliant documents lazily,
    and writes them via ``write_sitemap`` unless ``request.dry_run`` is set.

    Args:
        request: The fully resolved generate request.
        content_source: Port that walks a directory into entries.
        write_sitemap: Port that serializes documents to disk.

    Returns:
        A :class:`GenerateResult` describing the run.
    """
    stats = _StreamStats()
    documents = _stream_documents(request, content_source, stats)

    if request.dry_run:
        for _document in documents:  # consume to count; nothing is written
            pass
        return GenerateResult(url_count=stats.urls, paths_written=(), was_split=stats.documents > 1)

    written = write_sitemap(
        documents=documents,
        output_path=Path(request.output_path),
        base_url=request.base_url,
        gzip=request.gzip,
    )
    return GenerateResult(url_count=stats.urls, paths_written=tuple(written), was_split=stats.documents > 1)


__all__ = [
    "DirectoryRequest",
    "GenerateRequest",
    "GenerateResult",
    "generate_sitemap",
]
