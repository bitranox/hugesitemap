"""Domain-specific exceptions for typed error handling at boundaries."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Missing, invalid, or incomplete configuration.

    Raised when required configuration values are absent, malformed, or
    logically inconsistent. Typically caught at CLI boundaries to provide
    user-friendly error messages.

    Example:
        >>> from hugesitemap.domain.errors import ConfigurationError
        >>> err = ConfigurationError("No SMTP hosts configured")
        >>> str(err)
        'No SMTP hosts configured'
    """


class SitemapValidationError(Exception):
    """Generated sitemap XML failed validation.

    Raised when the writer re-parses the serialized sitemap and the result is
    not well-formed, or when a structural invariant (URL count, namespace) is
    violated before the live file is replaced.

    Example:
        >>> from hugesitemap.domain.errors import SitemapValidationError
        >>> err = SitemapValidationError("Re-parsed sitemap is not well-formed")
        >>> str(err)
        'Re-parsed sitemap is not well-formed'
    """


__all__ = [
    "ConfigurationError",
    "SitemapValidationError",
]
