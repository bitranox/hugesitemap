"""Tests for the GenerateSitemap use case with in-memory fakes."""

from __future__ import annotations

from datetime import datetime, timezone

from hugesitemap.adapters.memory.sitemap import InMemoryContentSource, SitemapWriterSpy
from hugesitemap.application.generate import (
    DirectoryRequest,
    GenerateRequest,
    generate_sitemap,
)
from hugesitemap.domain.limits import MAX_URLS
from hugesitemap.domain.model import SitemapEntry


def _entry(loc: str) -> SitemapEntry:
    return SitemapEntry(loc=loc, lastmod=datetime(2020, 1, 1, tzinfo=timezone.utc), priority=0.5)


def _request(
    *,
    explicit_entries: tuple[SitemapEntry, ...] = (),
    dry_run: bool = False,
) -> GenerateRequest:
    return GenerateRequest(
        base_url="https://x.test/",
        output_path="/out/sitemap.xml",
        gzip=False,
        default_priority=0.5,
        directories=(DirectoryRequest(root="/data/a", url_prefix="https://x.test/a/"),),
        explicit_entries=explicit_entries,
        dry_run=dry_run,
    )


def test_walks_directories_and_writes() -> None:
    source = InMemoryContentSource({"/data/a": [_entry("https://x.test/a/1"), _entry("https://x.test/a/2")]})
    writer = SitemapWriterSpy()
    result = generate_sitemap(_request(), content_source=source, write_sitemap=writer)
    assert result.url_count == 2
    assert result.was_split is False
    assert len(writer.calls) == 1
    assert len(writer.calls[0].documents) == 1


def test_appends_explicit_entries() -> None:
    source = InMemoryContentSource({"/data/a": [_entry("https://x.test/a/1")]})
    writer = SitemapWriterSpy()
    request = _request(explicit_entries=(_entry("https://x.test/index.html"),))
    result = generate_sitemap(request, content_source=source, write_sitemap=writer)
    assert result.url_count == 2


def test_dry_run_does_not_write() -> None:
    source = InMemoryContentSource({"/data/a": [_entry("https://x.test/a/1")]})
    writer = SitemapWriterSpy()
    result = generate_sitemap(_request(dry_run=True), content_source=source, write_sitemap=writer)
    assert result.url_count == 1
    assert result.paths_written == ()
    assert writer.calls == []


def test_under_cap_yields_single_document() -> None:
    entries = [_entry(f"https://x.test/a/{n}") for n in range(5)]
    source = InMemoryContentSource({"/data/a": entries})
    writer = SitemapWriterSpy()
    result = generate_sitemap(_request(), content_source=source, write_sitemap=writer)
    assert result.url_count == 5
    assert result.was_split is False
    assert len(writer.calls[0].documents) == 1


def test_over_cap_streams_into_multiple_documents() -> None:
    # Exactly one past the protocol cap -> two documents: a full chunk + a single.
    entries = [_entry(f"https://x.test/a/{n}") for n in range(MAX_URLS + 1)]
    source = InMemoryContentSource({"/data/a": entries})
    writer = SitemapWriterSpy()
    result = generate_sitemap(_request(), content_source=source, write_sitemap=writer)
    assert result.url_count == MAX_URLS + 1
    assert result.was_split is True
    documents = writer.calls[0].documents
    assert [len(d.entries) for d in documents] == [MAX_URLS, 1]


def test_dry_run_reports_split_without_writing() -> None:
    entries = [_entry(f"https://x.test/a/{n}") for n in range(MAX_URLS + 1)]
    source = InMemoryContentSource({"/data/a": entries})
    writer = SitemapWriterSpy()
    result = generate_sitemap(_request(dry_run=True), content_source=source, write_sitemap=writer)
    assert result.url_count == MAX_URLS + 1
    assert result.was_split is True
    assert writer.calls == []
