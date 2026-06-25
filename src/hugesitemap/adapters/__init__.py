"""Adapters layer - infrastructure and framework integrations.

Contains adapter implementations that connect the application to external
systems and frameworks (CLI, configuration, filesystem, lxml, logging).

Contents:
    * :mod:`.config` - Configuration loading, deployment, display, site loader
    * :mod:`.filesystem` - Directory walking into sitemap entries
    * :mod:`.sitemap_lxml` - lxml sitemap writer with validation
    * :mod:`.logging` - Logging setup with lib_log_rich
    * :mod:`.cli` - Click CLI framework integration
"""

from __future__ import annotations

__all__: list[str] = []
