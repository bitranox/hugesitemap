"""Composition root wiring adapters to application ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..adapters.config.deploy import deploy_configuration
from ..adapters.config.display import display_config

# Configuration services
from ..adapters.config.loader import get_config, get_default_config_path
from ..adapters.config.site_loader import load_sites

# Sitemap services
from ..adapters.filesystem import walk_directory

# Logging services
from ..adapters.logging.setup import init_logging
from ..adapters.sitemap_lxml import write_sitemap

# Static conformance assertions -- pyright verifies that each adapter function
# structurally satisfies its corresponding Protocol at type-check time.
if TYPE_CHECKING:
    from ..application.ports import (
        ContentSource,
        DeployConfiguration,
        DisplayConfig,
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadSites,
        SitemapWriter,
    )

    _assert_get_config: GetConfig = get_config
    _assert_get_default_config_path: GetDefaultConfigPath = get_default_config_path
    _assert_deploy_configuration: DeployConfiguration = deploy_configuration
    _assert_display_config: DisplayConfig = display_config
    _assert_load_sites: LoadSites = load_sites
    _assert_content_source: ContentSource = walk_directory
    _assert_write_sitemap: SitemapWriter = write_sitemap
    _assert_init_logging: InitLogging = init_logging


@dataclass(frozen=True, slots=True)
class AppServices:
    """Frozen container holding all application port implementations."""

    get_config: GetConfig
    get_default_config_path: GetDefaultConfigPath
    deploy_configuration: DeployConfiguration
    display_config: DisplayConfig
    load_sites: LoadSites
    content_source: ContentSource
    write_sitemap: SitemapWriter
    init_logging: InitLogging


def build_production() -> AppServices:
    """Wire production adapters into an AppServices container."""
    return AppServices(
        get_config=get_config,
        get_default_config_path=get_default_config_path,
        deploy_configuration=deploy_configuration,
        display_config=display_config,
        load_sites=load_sites,
        content_source=walk_directory,
        write_sitemap=write_sitemap,
        init_logging=init_logging,
    )


def build_testing(*, writer: SitemapWriter | None = None) -> AppServices:
    """Wire in-memory adapters into an AppServices container.

    Args:
        writer: Optional SitemapWriter (e.g. a ``SitemapWriterSpy``) to capture
            write calls. When None, a fresh spy is created.

    Returns:
        AppServices container with in-memory adapters.
    """
    from ..adapters.memory import (  # noqa: PLC0415 - keeps test-only doubles out of the production import path
        SitemapWriterSpy,
        content_source_empty,
        deploy_configuration_in_memory,
        display_config_in_memory,
        get_config_in_memory,
        get_default_config_path_in_memory,
        init_logging_in_memory,
        load_sites_in_memory,
    )

    return AppServices(
        get_config=get_config_in_memory,
        get_default_config_path=get_default_config_path_in_memory,
        deploy_configuration=deploy_configuration_in_memory,
        display_config=display_config_in_memory,
        load_sites=load_sites_in_memory,
        content_source=content_source_empty,
        write_sitemap=writer if writer is not None else SitemapWriterSpy(),
        init_logging=init_logging_in_memory,
    )


__all__ = [
    # Composition
    "AppServices",
    "build_production",
    "build_testing",
    "deploy_configuration",
    "display_config",
    # Configuration
    "get_config",
    "get_default_config_path",
    # Logging
    "init_logging",
    "load_sites",
    # Sitemap
    "walk_directory",
    "write_sitemap",
]
