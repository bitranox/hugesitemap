"""Domain error types: instantiation and message preservation."""

from __future__ import annotations

import pytest

from hugesitemap.domain.errors import ConfigurationError, SitemapValidationError


@pytest.mark.os_agnostic
def test_configuration_error_preserves_message() -> None:
    """Instantiation stores the message for display."""
    exc = ConfigurationError("Config file not found: media.toml")
    assert str(exc) == "Config file not found: media.toml"


@pytest.mark.os_agnostic
def test_sitemap_validation_error_preserves_message() -> None:
    """Instantiation stores the validation detail for display."""
    exc = SitemapValidationError("Generated sitemap is not well-formed")
    assert str(exc) == "Generated sitemap is not well-formed"


@pytest.mark.os_agnostic
def test_errors_are_distinct_types() -> None:
    """The two domain errors are unrelated exception types."""
    assert not issubclass(SitemapValidationError, ConfigurationError)
    assert issubclass(ConfigurationError, Exception)
