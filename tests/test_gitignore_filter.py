"""Tests for the igittigitt-backed path filter adapter.

The filter decides, with full git ``.gitignore`` semantics, whether an on-disk
path is excluded from the sitemap. Patterns are anchored at the directory root,
so an absolute path under ``root`` is what gets matched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hugesitemap.adapters.gitignore_filter import build_filter
from hugesitemap.domain.errors import ConfigurationError
from hugesitemap.domain.filters import FilterSpec


def _tree(root: Path) -> None:
    (root / "sub").mkdir(parents=True)
    (root / "zsvc" / "z_content").mkdir(parents=True)
    (root / "doc.pdf").write_bytes(b"pdf")
    (root / "notes.txt").write_bytes(b"txt")
    (root / ".hidden").write_bytes(b"x")
    (root / "sub" / "keep.html").write_bytes(b"x")
    (root / "sub" / "skip.txt").write_bytes(b"x")
    (root / "zsvc" / "z_content" / "s.pdf").write_bytes(b"x")


def test_inline_patterns_match_files(tmp_path: Path) -> None:
    _tree(tmp_path)
    flt = build_filter(FilterSpec(patterns=("*.txt", ".*")), root=str(tmp_path))
    assert flt.is_ignored(str(tmp_path / "notes.txt"))
    assert flt.is_ignored(str(tmp_path / ".hidden"))
    assert not flt.is_ignored(str(tmp_path / "doc.pdf"))


def test_directory_pattern_prunes_whole_subtree(tmp_path: Path) -> None:
    _tree(tmp_path)
    flt = build_filter(FilterSpec(patterns=("zsvc/",)), root=str(tmp_path))
    # The directory itself matches, so the walk can prune it ...
    assert flt.is_ignored(str(tmp_path / "zsvc"))
    # ... and everything beneath an excluded directory is excluded too (git rule).
    assert flt.is_ignored(str(tmp_path / "zsvc" / "z_content" / "s.pdf"))


def test_negation_reincludes(tmp_path: Path) -> None:
    _tree(tmp_path)
    # Ignore everything, keep directories to descend, re-include html.
    flt = build_filter(FilterSpec(patterns=("*", "!*/", "!*.html")), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "sub" / "keep.html"))
    assert flt.is_ignored(str(tmp_path / "notes.txt"))
    assert not flt.is_ignored(str(tmp_path / "sub"))  # dir kept so the walk reaches html


def test_keep_allowlist_keeps_only_matches(tmp_path: Path) -> None:
    _tree(tmp_path)
    flt = build_filter(FilterSpec(keep_patterns=("*.html",)), root=str(tmp_path))
    # Only the kept kind of file survives; everything else is excluded.
    assert not flt.is_ignored(str(tmp_path / "sub" / "keep.html"))
    assert flt.is_ignored(str(tmp_path / "doc.pdf"))
    assert flt.is_ignored(str(tmp_path / "notes.txt"))
    # An unanchored keep pattern could match in any directory, so directories are
    # kept for descent (the walk still visits them to find the matching files).
    assert not flt.is_ignored(str(tmp_path / "sub"))
    assert not flt.is_ignored(str(tmp_path / "zsvc"))


def test_keep_anchored_subtree_prunes_others(tmp_path: Path) -> None:
    _tree(tmp_path)
    # Anchored allowlist: index only the sub/ subtree, prune everything else.
    flt = build_filter(FilterSpec(keep_patterns=("sub/**",)), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "sub"))
    assert not flt.is_ignored(str(tmp_path / "sub" / "keep.html"))
    assert flt.is_ignored(str(tmp_path / "zsvc"))  # outside the kept subtree -> pruned
    assert flt.is_ignored(str(tmp_path / "doc.pdf"))


def test_keep_then_ignore_subtracts(tmp_path: Path) -> None:
    _tree(tmp_path)
    # Allowlist PDFs, then subtract the zsvc subtree.
    flt = build_filter(FilterSpec(keep_patterns=("*.pdf",), patterns=("zsvc/",)), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "doc.pdf"))  # kept
    assert flt.is_ignored(str(tmp_path / "zsvc"))  # subtracted by ignore even though it holds a pdf
    assert flt.is_ignored(str(tmp_path / "notes.txt"))  # not in the allowlist


def test_keep_keeps_parent_dirs_of_deep_match(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "deep.pdf").write_bytes(b"x")
    flt = build_filter(FilterSpec(keep_patterns=("*.pdf",)), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "a"))  # ancestor kept so the walk reaches deep.pdf
    assert not flt.is_ignored(str(tmp_path / "a" / "b"))
    assert not flt.is_ignored(str(tmp_path / "a" / "b" / "deep.pdf"))


def test_keep_file_is_read(tmp_path: Path) -> None:
    _tree(tmp_path)
    rules = tmp_path / "rules.sitemapinclude"
    rules.write_text("*.pdf\n")  # allowlist only PDFs
    flt = build_filter(FilterSpec(keep_file=str(rules)), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "doc.pdf"))
    assert flt.is_ignored(str(tmp_path / "notes.txt"))


def test_missing_keep_file_raises_configuration_error(tmp_path: Path) -> None:
    spec = FilterSpec(keep_file=str(tmp_path / "nope.sitemapinclude"))
    with pytest.raises(ConfigurationError):
        build_filter(spec, root=str(tmp_path))


def test_nested_keep_files_are_discovered(tmp_path: Path) -> None:
    _tree(tmp_path)
    # A per-directory allowlist file inside sub/ keeps only html there.
    (tmp_path / "sub" / ".sitemapinclude").write_text("*.html\n")
    flt = build_filter(FilterSpec(nested_keep_filename=".sitemapinclude"), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "sub" / "keep.html"))
    assert flt.is_ignored(str(tmp_path / "sub" / "skip.txt"))


def test_keep_file_then_ignore_subtracts(tmp_path: Path) -> None:
    _tree(tmp_path)
    keep = tmp_path / "rules.sitemapinclude"
    keep.write_text("*.pdf\n")
    # Allowlist PDFs via keep_file, then subtract the zsvc subtree via ignore.
    flt = build_filter(FilterSpec(keep_file=str(keep), patterns=("zsvc/",)), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "doc.pdf"))
    assert flt.is_ignored(str(tmp_path / "zsvc"))  # ignore wins over keep


def test_empty_spec_ignores_nothing(tmp_path: Path) -> None:
    _tree(tmp_path)
    flt = build_filter(FilterSpec(), root=str(tmp_path))
    assert not flt.is_ignored(str(tmp_path / "notes.txt"))
    assert not flt.is_ignored(str(tmp_path / ".hidden"))


def test_ignore_file_is_read(tmp_path: Path) -> None:
    _tree(tmp_path)
    rules = tmp_path / "rules.gitignore"
    rules.write_text("*.txt\n*.pdf\n")
    flt = build_filter(FilterSpec(ignore_file=str(rules)), root=str(tmp_path))
    assert flt.is_ignored(str(tmp_path / "notes.txt"))
    assert flt.is_ignored(str(tmp_path / "doc.pdf"))
    assert not flt.is_ignored(str(tmp_path / "sub" / "keep.html"))


def test_missing_ignore_file_raises_configuration_error(tmp_path: Path) -> None:
    spec = FilterSpec(ignore_file=str(tmp_path / "nope.gitignore"))
    with pytest.raises(ConfigurationError):
        build_filter(spec, root=str(tmp_path))


def test_nested_ignore_files_are_discovered(tmp_path: Path) -> None:
    _tree(tmp_path)
    (tmp_path / "sub" / ".sitemapignore").write_text("keep.html\n")
    flt = build_filter(FilterSpec(nested_ignore_filename=".sitemapignore"), root=str(tmp_path))
    assert flt.is_ignored(str(tmp_path / "sub" / "keep.html"))
    assert not flt.is_ignored(str(tmp_path / "doc.pdf"))


def test_nested_rules_override_inline(tmp_path: Path) -> None:
    _tree(tmp_path)
    # Inline ignores all html; a nested file re-includes one with a negation.
    (tmp_path / "sub" / ".sitemapignore").write_text("!keep.html\n")
    flt = build_filter(
        FilterSpec(patterns=("*.html",), nested_ignore_filename=".sitemapignore"),
        root=str(tmp_path),
    )
    assert not flt.is_ignored(str(tmp_path / "sub" / "keep.html"))
