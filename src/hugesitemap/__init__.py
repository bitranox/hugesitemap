"""Public package surface exposing metadata, configuration, and the use case.

This module provides the stable public API for the package, routing imports
through the proper architectural layers:
- Application exports: the GenerateSitemap use case and its DTOs
- Composition exports: wired adapter services (configuration)
- Metadata: package information
"""

from __future__ import annotations

# Metadata
from .__init__conf__ import print_info

# Application exports (use case)
from .application.generate import (
    DirectoryRequest,
    GenerateRequest,
    GenerateResult,
    generate_sitemap,
)

# Composition exports (wired adapters)
from .composition import get_config

__all__ = [
    "DirectoryRequest",
    "GenerateRequest",
    "GenerateResult",
    "generate_sitemap",
    "get_config",
    "print_info",
]
