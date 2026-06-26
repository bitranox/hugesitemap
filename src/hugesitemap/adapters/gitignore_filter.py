"""igittigitt-backed path filter: git-compatible ``.gitignore`` matching.

Builds an :class:`igittigitt.IgnoreParser` from a domain :class:`FilterSpec`
and exposes a tiny :class:`GitignoreFilter` with a single ``is_ignored`` query.
``igittigitt`` is fully typed (ships ``py.typed``), so it is imported directly;
this module is the one place the rest of the package routes path-exclusion
decisions through, keeping the library at a single, reviewable boundary.

Matching uses git semantics: rules are anchored at ``root``, directory patterns
prune whole subtrees, a file under an excluded directory cannot be re-included,
and later rule sources win. ``igittigitt`` decides file-vs-directory by stat, so
the paths passed to :meth:`GitignoreFilter.is_ignored` must be real, absolute
on-disk paths under ``root``.

Contents:
    * :class:`GitignoreFilter` - wraps a parser behind ``is_ignored``.
    * :func:`build_filter` - assemble a filter from a :class:`FilterSpec`.
"""

from __future__ import annotations

from pathlib import Path

import igittigitt

from ..domain.errors import ConfigurationError
from ..domain.filters import FilterSpec


class GitignoreFilter:
    """A path-exclusion predicate backed by a parsed ``igittigitt`` ruleset."""

    __slots__ = ("_parser",)

    def __init__(self, parser: igittigitt.IgnoreParser) -> None:
        self._parser = parser

    def is_ignored(self, abspath: str) -> bool:
        """Return whether ``abspath`` is excluded.

        Args:
            abspath: An absolute, on-disk path under the configured root.

        Returns:
            ``True`` when git would ignore the path under the configured rules.
        """
        return self._parser.match(abspath)


def build_filter(spec: FilterSpec, *, root: str) -> GitignoreFilter:
    """Assemble a :class:`GitignoreFilter` for one directory root.

    Rule sources are added in precedence order (later wins): inline
    ``spec.patterns``, then ``spec.ignore_file``, then any per-directory
    ``spec.nested_filename`` files discovered within the tree.

    Args:
        spec: The site's filter description.
        root: Absolute on-disk directory the patterns are anchored at.

    Returns:
        A ready-to-query :class:`GitignoreFilter`.

    Raises:
        ConfigurationError: If ``spec.ignore_file`` is set but does not exist.
    """
    parser = igittigitt.IgnoreParser()
    for pattern in spec.patterns:
        parser.add_rule(pattern, base_path=root)
    if spec.ignore_file is not None:
        ignore_file = Path(spec.ignore_file)
        if not ignore_file.is_file():
            raise ConfigurationError(f"Filter ignore_file not found: {spec.ignore_file}")
        parser.parse_rule_file(ignore_file, base_dir=root)
    if spec.nested_filename is not None:
        parser.parse_rule_files(base_dir=root, filename=spec.nested_filename, add_default_patterns=False)
    return GitignoreFilter(parser)


__all__ = ["GitignoreFilter", "build_filter"]
