"""Sitemap size limits from the sitemaps.org protocol.

The protocol caps a single sitemap at 50,000 URLs and 50 MiB uncompressed. The
URL cap is enforced by the streaming chunker in the GenerateSitemap use case
(``application/generate.py``); the byte cap is the writer adapter's concern (it
depends on serialized size).

Contents:
    * :data:`MAX_URLS` - maximum URLs per sitemap document.
    * :data:`MAX_BYTES` - maximum uncompressed bytes per sitemap document.
"""

from __future__ import annotations

MAX_URLS = 50_000
"""Maximum number of ``<url>`` entries permitted in a single sitemap."""

MAX_BYTES = 50 * 1024 * 1024
"""Maximum uncompressed size (50 MiB) of a single sitemap document."""

__all__ = [
    "MAX_BYTES",
    "MAX_URLS",
]
