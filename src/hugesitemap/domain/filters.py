"""Pure ordered filter engine for selecting which paths enter the sitemap.

Reproduces the old ``sitemap_gen.py`` filter behaviour: an ordered list of
drop patterns, each either a shell wildcard (``fnmatch``) or a regular
expression prefixed with ``re:``. A path is dropped when any pattern matches.
Patterns match against the path relative to its directory root, normalised to
forward slashes with a leading ``/`` so anchored regexps such as
``re:/\\.[^/]*`` (hidden dotfiles) and wildcards such as ``*/zsvc/z_content/*``
behave as in the original tool.

Contents:
    * :data:`REGEX_PREFIX` - marker that selects regexp matching.
    * :class:`Matcher` - a single compiled drop pattern.
    * :func:`compile_filters` - compile raw patterns into matchers.
    * :func:`is_dropped` - decide whether a relative path is dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatch
from re import Pattern

REGEX_PREFIX = "re:"
"""Pattern prefix selecting regular-expression matching instead of wildcard."""


@dataclass(frozen=True, slots=True)
class Matcher:
    """A single compiled drop pattern.

    Exactly one of ``regexp``/``wildcard`` is active: when ``regexp`` is set the
    pattern used the ``re:`` prefix and ``wildcard`` is unused (empty string);
    otherwise ``wildcard`` holds the shell pattern.

    Attributes:
        raw: The original pattern string (for diagnostics).
        regexp: Compiled regexp for ``re:``-prefixed patterns, else ``None``.
        wildcard: The shell wildcard pattern (empty when ``regexp`` is set).
    """

    raw: str
    regexp: Pattern[str] | None
    wildcard: str

    def matches(self, candidate: str) -> bool:
        """Return whether ``candidate`` matches this pattern.

        Args:
            candidate: Leading-slash, forward-slash relative path.

        Returns:
            ``True`` if the pattern matches.
        """
        if self.regexp is not None:
            return self.regexp.search(candidate) is not None
        return fnmatch(candidate, self.wildcard)


def compile_filters(patterns: tuple[str, ...]) -> tuple[Matcher, ...]:
    """Compile raw drop patterns into ordered :class:`Matcher` objects.

    Args:
        patterns: Drop patterns, wildcard unless prefixed with ``re:``.

    Returns:
        A tuple of matchers in the original order.

    Example:
        >>> matchers = compile_filters(("*~", "re:/\\\\.[^/]*"))
        >>> len(matchers)
        2
        >>> matchers[1].regexp is not None
        True
    """
    compiled: list[Matcher] = []
    for pattern in patterns:
        if pattern.startswith(REGEX_PREFIX):
            expr = pattern[len(REGEX_PREFIX) :]
            compiled.append(Matcher(raw=pattern, regexp=re.compile(expr), wildcard=""))
        else:
            compiled.append(Matcher(raw=pattern, regexp=None, wildcard=pattern))
    return tuple(compiled)


def is_dropped(relpath: str, matchers: tuple[Matcher, ...]) -> bool:
    """Return whether a relative path is dropped by any matcher.

    The path is normalised to a leading-slash, forward-slash form before
    matching so anchored patterns behave consistently across operating systems.

    Args:
        relpath: Path relative to the directory root (any slash style).
        matchers: Compiled matchers from :func:`compile_filters`.

    Returns:
        ``True`` if any matcher matches (the path is dropped).

    Example:
        >>> matchers = compile_filters(("*.txt*", "re:/\\\\.[^/]*"))
        >>> is_dropped("sub/notes.txt", matchers)
        True
        >>> is_dropped(".hidden", matchers)
        True
        >>> is_dropped("sub/file.pdf", matchers)
        False
    """
    candidate = "/" + relpath.replace("\\", "/").lstrip("/")
    return any(matcher.matches(candidate) for matcher in matchers)


__all__ = [
    "Matcher",
    "REGEX_PREFIX",
    "compile_filters",
    "is_dropped",
]
