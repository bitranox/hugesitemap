"""Tests for the filesystem content source (os.walk -> sitemap entries)."""

from __future__ import annotations

import os
from pathlib import Path

from hugesitemap.adapters.filesystem import walk_directory
from hugesitemap.domain.filters import Matcher, compile_filters

PREFIX = "https://media.test/a000/"


def _build_tree(root: Path) -> None:
    (root / "000").mkdir(parents=True)
    (root / "000" / "doc.pdf").write_bytes(b"pdf")
    (root / "000" / "notes.txt").write_bytes(b"txt")
    (root / "000" / ".hidden").write_bytes(b"x")
    (root / "zsvc" / "z_content").mkdir(parents=True)
    (root / "zsvc" / "z_content" / "skip.pdf").write_bytes(b"x")
    (root / "top.pdf").write_bytes(b"x")


def _locs(root: Path, matchers: tuple[Matcher, ...]) -> set[str]:
    entries = list(walk_directory(root=str(root), url_prefix=PREFIX, matchers=matchers, default_priority=0.5))
    return {e.loc for e in entries}


def test_emits_directory_and_file_urls(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    locs = _locs(tmp_path, compile_filters(()))
    assert PREFIX in locs  # root directory URL (trailing slash)
    assert f"{PREFIX}000/" in locs  # subdirectory URL
    assert f"{PREFIX}000/doc.pdf" in locs  # file URL
    assert f"{PREFIX}top.pdf" in locs


def test_directory_urls_have_trailing_slash(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    entries = list(
        walk_directory(root=str(tmp_path), url_prefix=PREFIX, matchers=compile_filters(()), default_priority=0.5)
    )
    dir_entries = [e for e in entries if e.loc.endswith("/")]
    assert any(e.loc == PREFIX for e in dir_entries)
    assert all(e.changefreq is None for e in entries)


def test_filters_drop_files_and_prune_dirs(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    matchers = compile_filters((r"re:/\.[^/]*", "*.txt*", "*/zsvc/z_content/*"))
    locs = _locs(tmp_path, matchers)
    assert f"{PREFIX}000/notes.txt" not in locs
    assert not any(".hidden" in loc for loc in locs)
    assert not any("z_content" in loc for loc in locs)
    assert f"{PREFIX}000/doc.pdf" in locs


def test_lastmod_reflects_mtime(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    target = tmp_path / "top.pdf"
    os.utime(target, (1341994580, 1341994580))
    entries = list(
        walk_directory(root=str(tmp_path), url_prefix=PREFIX, matchers=compile_filters(()), default_priority=0.5)
    )
    entry = next(e for e in entries if e.loc == f"{PREFIX}top.pdf")
    assert entry.lastmod is not None
    assert entry.lastmod.year == 2012


def test_missing_root_yields_nothing(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    entries = list(
        walk_directory(root=str(missing), url_prefix=PREFIX, matchers=compile_filters(()), default_priority=0.5)
    )
    assert entries == []


def test_priority_is_default(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    entries = list(
        walk_directory(root=str(tmp_path), url_prefix=PREFIX, matchers=compile_filters(()), default_priority=0.5)
    )
    assert all(e.priority == 0.5 for e in entries)
