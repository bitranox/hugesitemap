"""Pure description of which paths a site selects into its sitemap.

The actual matching is performed with full git ``.gitignore`` semantics by the
``igittigitt`` library, which lives in the adapter layer (see
``adapters/gitignore_filter.py``). The domain only owns the *shape* of a filter
- a value object naming the rule sources - so it stays free of I/O and
third-party imports.

A :class:`FilterSpec` has two symmetric sides:

* an **include / allowlist** side (``keep_patterns`` + ``keep_file`` +
  ``nested_keep_filename``). When any of these is set the spec runs in include
  mode: only paths the include side keeps survive.
* an **ignore / deny** side (``patterns`` + ``ignore_file`` +
  ``nested_ignore_filename``). It subtracts from whatever survived the include
  side. With no include side every path is considered.

Within each side the three sources apply in precedence order - inline patterns,
then the rule file, then the per-directory nested files - and later sources win
(git's last-matching-rule rule; a deeper nested file beats a shallower one).
Across the two sides the **ignore side wins**: a path the include side kept is
still dropped if the ignore side matches it.

Contents:
    * :class:`FilterSpec` - the immutable filter description.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilterSpec:
    """Immutable description of a site's path-selection rules.

    The include side (``keep_*``) selects the allowlist; the ignore side
    subtracts from it. Each side has inline patterns, an optional rule file, and
    an optional per-directory nested filename, applied in that order (later wins).

    Attributes:
        keep_patterns: Inline allowlist patterns. Non-empty (or any other
            ``keep_*`` field set) switches the spec to include mode.
        patterns: Inline ``.gitignore`` ignore patterns.
        keep_file: Optional path to an allowlist rule file.
        ignore_file: Optional path to an ignore rule file.
        nested_keep_filename: Optional per-directory allowlist filename to
            discover within the tree (for example ``.sitemapinclude``).
        nested_ignore_filename: Optional per-directory ignore filename to
            discover within the tree (for example ``.sitemapignore``).

    Example:
        >>> spec = FilterSpec(patterns=("*~", ".*"))
        >>> spec.patterns
        ('*~', '.*')
        >>> FilterSpec().is_empty
        True
        >>> spec.is_empty
        False
        >>> FilterSpec(keep_patterns=("*.html",)).is_empty
        False
    """

    keep_patterns: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    keep_file: str | None = None
    ignore_file: str | None = None
    nested_keep_filename: str | None = None
    nested_ignore_filename: str | None = None

    @property
    def is_empty(self) -> bool:
        """Return whether the spec selects nothing (no rule source set)."""
        return not any(
            (
                self.keep_patterns,
                self.patterns,
                self.keep_file,
                self.ignore_file,
                self.nested_keep_filename,
                self.nested_ignore_filename,
            )
        )


__all__ = [
    "FilterSpec",
]
