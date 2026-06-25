"""In-memory adapter implementations for testing.

Provides lightweight implementations of the application ports that operate
entirely in memory -- no filesystem, no lxml, no logging framework.

Contents:
    * :mod:`.config` - In-memory configuration adapters
    * :mod:`.sitemap` - In-memory content source, writer spy, site-config loader
    * :mod:`.logging` - In-memory logging adapter
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import (
    deploy_configuration_in_memory,
    display_config_in_memory,
    get_config_in_memory,
    get_default_config_path_in_memory,
)
from .logging import init_logging_in_memory
from .sitemap import (
    InMemoryContentSource,
    SitemapWriterSpy,
    content_source_empty,
    load_sites_in_memory,
)

# Static conformance assertions
if TYPE_CHECKING:
    from hugesitemap.application.ports import (
        ContentSource,
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadSites,
        SitemapWriter,
    )

    _assert_get_config: GetConfig = get_config_in_memory
    _assert_get_default_config_path: GetDefaultConfigPath = get_default_config_path_in_memory
    _assert_init_logging: InitLogging = init_logging_in_memory
    _assert_load_sites: LoadSites = load_sites_in_memory
    _assert_content_source: ContentSource = content_source_empty
    _assert_writer: SitemapWriter = SitemapWriterSpy()

__all__ = [
    "InMemoryContentSource",
    "SitemapWriterSpy",
    "content_source_empty",
    "deploy_configuration_in_memory",
    "display_config_in_memory",
    "get_config_in_memory",
    "get_default_config_path_in_memory",
    "init_logging_in_memory",
    "load_sites_in_memory",
]
