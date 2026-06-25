# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""Thin typed adapter over the ``deflate`` (libdeflate) gzip API.

libdeflate is used (over stdlib ``gzip`` and ``isal``) because the sitemap
``.gz`` is a write-once, serve-many artifact where compression *ratio* is the
optimisation target and speed is irrelevant: at max level it produces the
smallest standard-gzip output of the available libraries. ``gzip_compress``
emits a self-describing gzip container that crawlers and ``gzip``/``zcat`` read
back without any side information.

``deflate.gzip_compress`` returns a ``bytearray``; this wrapper normalises it to
immutable ``bytes`` so the rest of the package works with a single byte type.

The ``deflate`` C extension ships no type information on some supported Python
versions (e.g. 3.10/3.11), so pyright reports its members as partially unknown.
The deflate-related rules are therefore disabled at the top of this single
boundary file; every other module imports the typed ``gzip_compress`` wrapper
and stays strict-clean.

Contents:
    * :data:`GZIP_MAX_LEVEL` - libdeflate's maximum compression level.
    * :func:`gzip_compress` - compress bytes to standard gzip format.
"""

from __future__ import annotations

import deflate as _deflate

GZIP_MAX_LEVEL = 12
"""libdeflate's maximum gzip compression level (highest ratio)."""


def gzip_compress(data: bytes, level: int = GZIP_MAX_LEVEL) -> bytes:
    """Compress ``data`` to standard gzip format using libdeflate.

    Args:
        data: Raw bytes to compress.
        level: libdeflate compression level (1-12); defaults to the maximum.

    Returns:
        Standard gzip-framed bytes (readable by ``gzip``/``zcat`` and crawlers).
    """
    # libdeflate returns a bytearray; normalise to immutable bytes for callers.
    return bytes(_deflate.gzip_compress(data, level))


__all__ = ["GZIP_MAX_LEVEL", "gzip_compress"]
