"""Filesystem content source: walk a directory tree into sitemap entries.

Implements the :class:`ContentSource` port. For each configured directory it
emits a directory URL (trailing slash, the directory's own mtime) and a file
URL per surviving file, mapping on-disk relative paths to URLs under the
directory's URL prefix and excluding any path matched by the gitignore-style
filter. Excluded directories are pruned from the walk so their contents are
never visited.

Contents:
    * :func:`walk_directory` - the ContentSource implementation.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from hugesitemap.adapters.gitignore_filter import build_filter
from hugesitemap.domain.filters import FilterSpec
from hugesitemap.domain.formatting import join_url, mtime_to_utc
from hugesitemap.domain.model import SitemapEntry


def _dir_loc(url_prefix: str, rel_posix: str) -> str:
    """Build a directory URL, guaranteeing a trailing slash."""
    loc = join_url(url_prefix, rel_posix)
    return loc if loc.endswith("/") else loc + "/"


def _entry_for(path: Path, loc: str, default_priority: float) -> SitemapEntry:
    """Build a :class:`SitemapEntry` using ``path``'s mtime."""
    lastmod = mtime_to_utc(path.stat().st_mtime)
    return SitemapEntry(loc=loc, lastmod=lastmod, priority=default_priority, changefreq=None)


def walk_directory(
    *,
    root: str,
    url_prefix: str,
    filter_spec: FilterSpec,
    default_priority: float,
) -> Iterator[SitemapEntry]:
    """Yield directory and file entries for one configured directory.

    Args:
        root: On-disk directory to walk.
        url_prefix: URL prefix that ``root`` maps to.
        filter_spec: Gitignore-style exclusion rules anchored at ``root``.
        default_priority: Priority assigned to every emitted entry.

    Yields:
        :class:`SitemapEntry` objects for surviving directories and files,
        in deterministic (sorted) order.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        return

    # When the site configures no filters, skip building a parser and the
    # per-path is_ignored() stat entirely; nothing is ever excluded.
    path_filter = None if filter_spec.is_empty else build_filter(filter_spec, root=str(root_path))

    for dirpath_str, dirnames, filenames in os.walk(root_path):
        dirnames.sort()
        filenames.sort()
        dirpath = Path(dirpath_str)
        relative = dirpath.relative_to(root_path)
        rel_posix = "" if relative == Path() else relative.as_posix()

        # Prune excluded subdirectories so os.walk never descends into them.
        if path_filter is not None:
            dirnames[:] = [name for name in dirnames if not path_filter.is_ignored(str(dirpath / name))]

        yield _entry_for(dirpath, _dir_loc(url_prefix, rel_posix), default_priority)

        for name in filenames:
            full = dirpath / name
            if path_filter is not None and path_filter.is_ignored(str(full)):
                continue
            file_rel = f"{rel_posix}/{name}" if rel_posix else name
            yield _entry_for(full, join_url(url_prefix, file_rel), default_priority)


__all__ = ["walk_directory"]
