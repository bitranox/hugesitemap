"""Tests for the lxml sitemap writer (build, validate, atomic write, split).

Assertions parse the written files with the stdlib ElementTree (an independent
parser) to confirm the lxml-produced output is well-formed and correctly shaped.
"""

from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from hugesitemap.adapters.sitemap_lxml import SITEMAP_NS, write_sitemap
from hugesitemap.domain.model import SitemapDocument, SitemapEntry

if TYPE_CHECKING:
    from pathlib import Path

NS = {"sm": SITEMAP_NS}
XSI = "http://www.w3.org/2001/XMLSchema-instance"


def _entry(loc: str, *, changefreq: str | None = None) -> SitemapEntry:
    return SitemapEntry(
        loc=loc,
        lastmod=datetime(2012, 7, 11, 14, 16, 20, tzinfo=timezone.utc),
        priority=0.5,
        changefreq=changefreq,
    )


def _doc(*locs: str) -> SitemapDocument:
    return SitemapDocument(entries=tuple(_entry(loc) for loc in locs))


def test_single_urlset_is_wellformed(tmp_path: Path) -> None:
    out = tmp_path / "sitemap.xml"
    written = write_sitemap(documents=[_doc("https://x.test/a/")], output_path=out, base_url="https://x.test/")
    assert written == [out]
    root = ET.parse(str(out)).getroot()
    assert root.tag == f"{{{SITEMAP_NS}}}urlset"
    assert root.findtext("sm:url/sm:loc", namespaces=NS) == "https://x.test/a/"
    assert root.findtext("sm:url/sm:lastmod", namespaces=NS) == "2012-07-11T14:16:20Z"
    assert root.findtext("sm:url/sm:priority", namespaces=NS) == "0.5000"


def test_schema_location_header(tmp_path: Path) -> None:
    out = tmp_path / "sitemap.xml"
    write_sitemap(documents=[_doc("https://x.test/a/")], output_path=out, base_url="https://x.test/")
    root = ET.parse(str(out)).getroot()
    assert (root.get(f"{{{XSI}}}schemaLocation") or "").startswith(SITEMAP_NS)


def test_changefreq_emitted_when_present(tmp_path: Path) -> None:
    out = tmp_path / "sitemap.xml"
    doc = SitemapDocument(entries=(_entry("https://x.test/i.html", changefreq="yearly"),))
    write_sitemap(documents=[doc], output_path=out, base_url="https://x.test/")
    root = ET.parse(str(out)).getroot()
    assert root.findtext("sm:url/sm:changefreq", namespaces=NS) == "yearly"


def test_gzip_output(tmp_path: Path) -> None:
    out = tmp_path / "sitemap.xml"
    written = write_sitemap(
        documents=[_doc("https://x.test/a/")], output_path=out, base_url="https://x.test/", gzip=True
    )
    gz = tmp_path / "sitemap.xml.gz"
    assert written == [gz]
    assert gz.exists()
    body = gzip.decompress(gz.read_bytes())
    assert b"urlset" in body


def test_split_writes_index_and_children(tmp_path: Path) -> None:
    out = tmp_path / "sitemap.xml"
    written = write_sitemap(
        documents=[_doc("https://x.test/a/"), _doc("https://x.test/b/")],
        output_path=out,
        base_url="https://x.test/",
    )
    child1 = tmp_path / "sitemap1.xml"
    child2 = tmp_path / "sitemap2.xml"
    assert written == [child1, child2, out]
    index_root = ET.parse(str(out)).getroot()
    assert index_root.tag == f"{{{SITEMAP_NS}}}sitemapindex"
    locs = [node.text for node in index_root.findall("sm:sitemap/sm:loc", namespaces=NS)]
    assert locs == ["https://x.test/sitemap1.xml", "https://x.test/sitemap2.xml"]


def test_no_temp_files_left_behind(tmp_path: Path) -> None:
    out = tmp_path / "sitemap.xml"
    write_sitemap(documents=[_doc("https://x.test/a/")], output_path=out, base_url="https://x.test/")
    assert not list(tmp_path.glob("*.tmp"))
