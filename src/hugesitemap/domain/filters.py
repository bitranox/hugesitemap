"""Pure description of which paths a site excludes from its sitemap.

The actual matching is performed with full git ``.gitignore`` semantics by the
``igittigitt`` library, which lives in the adapter layer (see
``adapters/gitignore_filter.py``). The domain only owns the *shape* of a filter
- a value object naming the rule sources - so it stays free of I/O and
third-party imports.

A :class:`FilterSpec` carries three rule sources, applied in precedence order
(later sources win, exactly like git's last-matching-rule rule):

1. ``patterns`` - inline ``.gitignore`` patterns, anchored at the directory root.
2. ``ignore_file`` - an optional path to a ``.gitignore``-format file.
3. ``nested_filename`` - an optional per-directory ignore filename (for example
   ``.sitemapignore``) discovered throughout the scanned tree, git-style.

Contents:
    * :class:`FilterSpec` - the immutable filter description.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilterSpec:
    """Immutable description of a site's path-exclusion rules.

    Attributes:
        patterns: Inline ``.gitignore`` patterns, anchored at the directory root.
        ignore_file: Optional path to a ``.gitignore``-format rule file.
        nested_filename: Optional per-directory ignore filename to discover
            within each scanned tree (for example ``.sitemapignore``); ``None``
            disables nested discovery.

    Example:
        >>> spec = FilterSpec(patterns=("*~", ".*"))
        >>> spec.patterns
        ('*~', '.*')
        >>> FilterSpec().is_empty
        True
        >>> spec.is_empty
        False
    """

    patterns: tuple[str, ...] = ()
    ignore_file: str | None = None
    nested_filename: str | None = None

    @property
    def is_empty(self) -> bool:
        """Return whether the spec selects nothing (no rule source set)."""
        return not self.patterns and self.ignore_file is None and self.nested_filename is None


__all__ = [
    "FilterSpec",
]
