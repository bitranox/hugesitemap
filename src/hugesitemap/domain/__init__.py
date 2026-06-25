"""Domain layer - pure business logic with no I/O or framework dependencies.

Contains value objects, enumerations, pure helpers, and domain services that
form the core of the sitemap generator. No module here performs I/O or imports
a framework.

Contents:
    * :mod:`.model` - Sitemap value objects (entries, documents, index entries)
    * :mod:`.enums` - Domain enumerations (ChangeFreq, OutputFormat, DeployTarget)
    * :mod:`.errors` - Domain exception types
    * :mod:`.filters` - Ordered wildcard/regexp drop-filter engine
    * :mod:`.formatting` - ISO8601, priority, and URL formatting helpers
    * :mod:`.limits` - Sitemap size limits and entry chunking
"""

from __future__ import annotations

from .enums import ChangeFreq, DeployTarget, OutputFormat
from .errors import ConfigurationError, SitemapValidationError
from .filters import Matcher, compile_filters, is_dropped
from .formatting import format_priority, iso8601_z, join_url, mtime_to_utc
from .limits import MAX_BYTES, MAX_URLS
from .model import SitemapDocument, SitemapEntry, SitemapIndexEntry

__all__ = [
    # Model
    "SitemapDocument",
    "SitemapEntry",
    "SitemapIndexEntry",
    # Enums
    "ChangeFreq",
    "DeployTarget",
    "OutputFormat",
    # Errors
    "ConfigurationError",
    "SitemapValidationError",
    # Filters
    "Matcher",
    "compile_filters",
    "is_dropped",
    # Formatting
    "format_priority",
    "iso8601_z",
    "join_url",
    "mtime_to_utc",
    # Limits
    "MAX_BYTES",
    "MAX_URLS",
]
