"""igittigitt-backed path filter: git-compatible ``.gitignore`` matching.

Builds igittigitt parsers from a domain :class:`FilterSpec` and exposes a tiny
:class:`GitignoreFilter` with a single ``is_ignored`` query. ``igittigitt`` is
fully typed (ships ``py.typed``), so it is imported directly; this module is the
one place the rest of the package routes path-selection decisions through,
keeping the library at a single, reviewable boundary.

A filter combines two optional, symmetric sides with git semantics:

* an **include** side (:class:`igittigitt.IncludeParser`) built from
  ``spec.keep_patterns`` / ``keep_file`` / ``nested_keep_filename`` - when present,
  only paths it keeps survive (allowlist); it is directory-aware, so a directory
  whose descendants could match is kept and the walk descends into it;
* an **ignore** side (:class:`igittigitt.IgnoreParser`) built from
  ``spec.patterns`` / ``ignore_file`` / ``nested_ignore_filename`` - it subtracts
  paths from whatever the include side allowed.

Within each side the three sources are added inline-then-file-then-nested so later
sources win. A path is excluded when the include side rejects it (not in the
allowlist) or the ignore side matches it - so the ignore side wins across the two.
``igittigitt`` decides file-vs-directory by stat, so the paths passed to
:meth:`GitignoreFilter.is_ignored` must be real, absolute on-disk paths under
``root``.

Contents:
    * :class:`GitignoreFilter` - wraps the parsers behind ``is_ignored``.
    * :func:`build_filter` - assemble a filter from a :class:`FilterSpec`.
"""

from __future__ import annotations

from pathlib import Path

import igittigitt

from ..domain.errors import ConfigurationError
from ..domain.filters import FilterSpec


class GitignoreFilter:
    """A path-selection predicate backed by parsed ``igittigitt`` rulesets."""

    __slots__ = ("_ignore", "_include")

    def __init__(
        self,
        *,
        include: igittigitt.IncludeParser | None,
        ignore: igittigitt.IgnoreParser | None,
    ) -> None:
        self._include = include
        self._ignore = ignore

    def is_ignored(self, abspath: str) -> bool:
        """Return whether ``abspath`` is excluded from the sitemap.

        Args:
            abspath: An absolute, on-disk path under the configured root.

        Returns:
            ``True`` when the path is not in the allowlist (if one is set) or is
            matched by the ignore rules.
        """
        if self._include is not None and not self._include.match(abspath):
            return True
        return self._ignore is not None and self._ignore.match(abspath)


def _require_file(path: str, *, key: str) -> Path:
    """Return ``path`` as a :class:`Path`, or raise if it is not an existing file."""
    rule_file = Path(path)
    if not rule_file.is_file():
        raise ConfigurationError(f"Filter {key} not found: {path}")
    return rule_file


def _build_ignore(spec: FilterSpec, *, root: str) -> igittigitt.IgnoreParser | None:
    """Build the ignore (deny) parser, or ``None`` when no ignore source is set."""
    if not spec.patterns and spec.ignore_file is None and spec.nested_ignore_filename is None:
        return None
    parser = igittigitt.IgnoreParser()
    for pattern in spec.patterns:
        parser.add_rule(pattern, base_path=root)
    if spec.ignore_file is not None:
        parser.parse_rule_file(_require_file(spec.ignore_file, key="ignore_file"), base_dir=root)
    if spec.nested_ignore_filename is not None:
        parser.parse_rule_files(base_dir=root, filename=spec.nested_ignore_filename, add_default_patterns=False)
    return parser


def _build_include(spec: FilterSpec, *, root: str) -> igittigitt.IncludeParser | None:
    """Build the include (allowlist) parser, or ``None`` when no keep source is set."""
    if not spec.keep_patterns and spec.keep_file is None and spec.nested_keep_filename is None:
        return None
    parser = igittigitt.IncludeParser()
    for pattern in spec.keep_patterns:
        parser.add_rule(pattern, base_path=root)
    if spec.keep_file is not None:
        parser.parse_rule_file(_require_file(spec.keep_file, key="keep_file"), base_dir=root)
    if spec.nested_keep_filename is not None:
        parser.parse_rule_files(base_dir=root, filename=spec.nested_keep_filename, add_default_patterns=False)
    return parser


def build_filter(spec: FilterSpec, *, root: str) -> GitignoreFilter:
    """Assemble a :class:`GitignoreFilter` for one directory root.

    Each side adds its sources inline-then-file-then-nested (later winning): the
    include side from ``keep_patterns`` / ``keep_file`` / ``nested_keep_filename``,
    the ignore side from ``patterns`` / ``ignore_file`` / ``nested_ignore_filename``.
    The ignore side then subtracts from whatever the include side allowed.

    Args:
        spec: The site's filter description.
        root: Absolute on-disk directory the patterns are anchored at.

    Returns:
        A ready-to-query :class:`GitignoreFilter`.

    Raises:
        ConfigurationError: If ``spec.keep_file`` or ``spec.ignore_file`` is set
            but does not exist.
    """
    return GitignoreFilter(
        include=_build_include(spec, root=root),
        ignore=_build_ignore(spec, root=root),
    )


__all__ = ["GitignoreFilter", "build_filter"]
