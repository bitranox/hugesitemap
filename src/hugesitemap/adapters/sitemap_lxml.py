"""lxml-backed sitemap writer with re-parse validation and atomic replace.

Implements the :class:`SitemapWriter` port. Builds a ``<urlset>`` with lxml
using the sitemaps.org 0.9 namespace and ``xsi:schemaLocation``. When more than
one document is supplied it writes numbered child sitemaps plus a
``<sitemapindex>`` at the output path. Every file is validated by re-parsing the
serialized bytes before being moved into place with an atomic rename, and may be
gzip-compressed (via libdeflate at maximum ratio; see :mod:`.typed_deflate`).

Contents:
    * :func:`write_sitemap` - the SitemapWriter implementation.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from itertools import chain
from pathlib import Path

from hugesitemap.domain.errors import SitemapValidationError
from hugesitemap.domain.formatting import format_priority, iso8601_z, join_url
from hugesitemap.domain.model import SitemapDocument, SitemapEntry, SitemapIndexEntry

from . import typed_lxml as xml
from .typed_deflate import gzip_compress

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = f"{SITEMAP_NS} {SITEMAP_NS}/sitemap.xsd"

_NSMAP: dict[str | None, str] = {None: SITEMAP_NS, "xsi": XSI_NS}


def _sm(tag: str) -> str:
    """Return a Clark-notation qualified name in the sitemap namespace."""
    return f"{{{SITEMAP_NS}}}{tag}"


def _build_urlset(document: SitemapDocument) -> bytes:
    """Build the bytes of a ``<urlset>`` document."""
    root = xml.new_element(_sm("urlset"), _NSMAP)
    xml.set_attribute(root, f"{{{XSI_NS}}}schemaLocation", SCHEMA_LOCATION)
    for entry in document.entries:
        url = xml.child(root, _sm("url"))
        xml.set_text(xml.child(url, _sm("loc")), entry.loc)
        if entry.lastmod is not None:
            xml.set_text(xml.child(url, _sm("lastmod")), iso8601_z(entry.lastmod))
        if entry.changefreq is not None:
            xml.set_text(xml.child(url, _sm("changefreq")), entry.changefreq)
        xml.set_text(xml.child(url, _sm("priority")), format_priority(entry.priority))
    return xml.serialize(root)


def _build_index(children: Sequence[SitemapIndexEntry]) -> bytes:
    """Build the bytes of a ``<sitemapindex>`` document."""
    root = xml.new_element(_sm("sitemapindex"), _NSMAP)
    xml.set_attribute(root, f"{{{XSI_NS}}}schemaLocation", SCHEMA_LOCATION)
    for entry in children:
        node = xml.child(root, _sm("sitemap"))
        xml.set_text(xml.child(node, _sm("loc")), entry.loc)
        if entry.lastmod is not None:
            xml.set_text(xml.child(node, _sm("lastmod")), iso8601_z(entry.lastmod))
    return xml.serialize(root)


def _max_lastmod(entries: Sequence[SitemapEntry]) -> datetime | None:
    """Return the newest entry mtime, or ``None`` if none carry one."""
    stamps = [entry.lastmod for entry in entries if entry.lastmod is not None]
    return max(stamps) if stamps else None


def _gz_path(path: Path) -> Path:
    """Return the gzip variant of a path (``sitemap.xml`` -> ``sitemap.xml.gz``)."""
    return path.with_name(path.name + ".gz")


def _atomic_write(target: Path, xml_bytes: bytes, *, gzip: bool) -> None:
    """Validate, then write ``xml_bytes`` to ``target`` via an atomic rename.

    Args:
        target: Final destination path.
        xml_bytes: Serialized (uncompressed) XML to validate and write.
        gzip: Whether to gzip-compress the payload on disk.

    Raises:
        SitemapValidationError: If the serialized XML is not well-formed.
    """
    try:
        xml.parse(xml_bytes)
    except xml.XmlSyntaxError as exc:
        raise SitemapValidationError(f"Generated sitemap is not well-formed: {exc}") from exc
    payload = gzip_compress(xml_bytes) if gzip else xml_bytes
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_bytes(payload)
    tmp.replace(target)


def write_sitemap(
    *,
    documents: Iterable[SitemapDocument],
    output_path: Path,
    base_url: str,
    gzip: bool = False,
) -> list[Path]:
    """Write sitemap documents to disk, consuming them lazily.

    ``documents`` is pulled one at a time (never fully buffered), so the caller
    can stream arbitrarily large sites at bounded memory. With exactly one
    document the output is a single ``<urlset>`` at ``output_path``; with more,
    each becomes a numbered child (``sitemap1.xml`` ...) and a ``<sitemapindex>``
    is written at ``output_path`` referencing them by ``base_url``.

    Args:
        documents: Iterable of sitemap documents (at least one expected).
        output_path: Destination path for the urlset or the index.
        base_url: Site base URL, used to build child sitemap URLs on split.
        gzip: Whether to gzip-compress every written file.

    Returns:
        The list of paths written, children first then the index.

    Raises:
        SitemapValidationError: If any serialized document is not well-formed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stream = iter(documents)
    first = next(stream, SitemapDocument())
    second = next(stream, None)

    if second is None:
        target = _gz_path(output_path) if gzip else output_path
        _atomic_write(target, _build_urlset(first), gzip=gzip)
        return [target]

    written: list[Path] = []
    children: list[SitemapIndexEntry] = []
    for number, document in enumerate(chain((first, second), stream), start=1):
        child_path = output_path.with_name(f"{output_path.stem}{number}{output_path.suffix}")
        target = _gz_path(child_path) if gzip else child_path
        _atomic_write(target, _build_urlset(document), gzip=gzip)
        written.append(target)
        children.append(SitemapIndexEntry(loc=join_url(base_url, target.name), lastmod=_max_lastmod(document.entries)))

    index_target = _gz_path(output_path) if gzip else output_path
    _atomic_write(index_target, _build_index(children), gzip=gzip)
    written.append(index_target)
    return written


__all__ = [
    "SCHEMA_LOCATION",
    "SITEMAP_NS",
    "XSI_NS",
    "write_sitemap",
]
