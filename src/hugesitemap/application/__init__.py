"""Application layer - use cases and port definitions.

Contains use cases that orchestrate domain logic and port protocols that
define the interfaces for adapter implementations.

Contents:
    * :mod:`.ports` - Callable Protocol definitions for adapter functions
    * :mod:`.generate` - The GenerateSitemap use case and its DTOs
"""

from __future__ import annotations

from .generate import (
    DirectoryRequest,
    GenerateRequest,
    GenerateResult,
    generate_sitemap,
)
from .ports import (
    ContentSource,
    DeployConfiguration,
    DisplayConfig,
    GetConfig,
    GetDefaultConfigPath,
    InitLogging,
    LoadSites,
    SitemapWriter,
)

__all__ = [
    "ContentSource",
    "DeployConfiguration",
    "DirectoryRequest",
    "DisplayConfig",
    "GenerateRequest",
    "GenerateResult",
    "GetConfig",
    "GetDefaultConfigPath",
    "InitLogging",
    "LoadSites",
    "SitemapWriter",
    "generate_sitemap",
]
