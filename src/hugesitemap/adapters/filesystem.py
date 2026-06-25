"""Filesystem content source: walk a directory tree into sitemap entries.

Implements the :class:`ContentSource` port. For each configured directory it
emits a directory URL (trailing slash, the directory's own mtime) and a file
URL per surviving file, mapping on-disk relative paths to URLs under the
directory's URL prefix and dropping any path matched by the ordered filter
engine. Dropped directories are pruned from the walk so their contents are
never visited.

Contents:
    * :func:`walk_directory` - the ContentSource implementation.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from hugesitemap.domain.filters import Matcher, is_dropped
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


def _dir_dropped(rel: str, matchers: tuple[Matcher, ...]) -> bool:
    """Return whether a subdirectory (and its whole subtree) is dropped.

    A directory is tested in both bare and trailing-slash forms so patterns
    that target a directory's contents (for example ``*/zsvc/z_content/*``)
    prune the directory itself, not just the files beneath it.
    """
    return is_dropped(rel, matchers) or is_dropped(rel + "/", matchers)


def walk_directory(
    *,
    root: str,
    url_prefix: str,
    matchers: tuple[Matcher, ...],
    default_priority: float,
) -> Iterator[SitemapEntry]:
    """Yield directory and file entries for one configured directory.

    Args:
        root: On-disk directory to walk.
        url_prefix: URL prefix that ``root`` maps to.
        matchers: Compiled drop filters applied to relative paths.
        default_priority: Priority assigned to every emitted entry.

    Yields:
        :class:`SitemapEntry` objects for surviving directories and files,
        in deterministic (sorted) order.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        return

    for dirpath_str, dirnames, filenames in os.walk(root_path):
        dirnames.sort()
        filenames.sort()
        dirpath = Path(dirpath_str)
        relative = dirpath.relative_to(root_path)
        rel_posix = "" if relative == Path() else relative.as_posix()

        # Prune dropped subdirectories so os.walk never descends into them.
        dirnames[:] = [
            name for name in dirnames if not _dir_dropped(f"{rel_posix}/{name}" if rel_posix else name, matchers)
        ]

        yield _entry_for(dirpath, _dir_loc(url_prefix, rel_posix), default_priority)

        for name in filenames:
            file_rel = f"{rel_posix}/{name}" if rel_posix else name
            if is_dropped(file_rel, matchers):
                continue
            yield _entry_for(dirpath / name, join_url(url_prefix, file_rel), default_priority)


__all__ = ["walk_directory"]
