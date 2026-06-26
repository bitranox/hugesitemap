"""Application ports - callable Protocol definitions for adapter functions.

Each Protocol class defines a ``__call__`` method whose signature matches the
corresponding adapter function. Existing module-level functions satisfy these
protocols automatically via structural subtyping (PEP 544).

System Role:
    Sits between domain and adapters. Infrastructure types (``Config``,
    ``SiteConfig``) are imported under ``TYPE_CHECKING`` only so that
    import-linter layer contracts remain satisfied at runtime.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ..domain.enums import DeployTarget, OutputFormat
from ..domain.filters import FilterSpec
from ..domain.model import SitemapDocument, SitemapEntry

if TYPE_CHECKING:
    from lib_layered_config import Config

    from ..adapters.config.site_loader import SiteConfig


class GetConfig(Protocol):
    """Load layered configuration with application defaults."""

    def __call__(
        self, *, profile: str | None = ..., start_dir: str | None = ..., dotenv_path: str | None = ...
    ) -> Config: ...


class GetDefaultConfigPath(Protocol):
    """Return the path to the bundled default configuration file."""

    def __call__(self) -> Path: ...


class DeployConfiguration(Protocol):
    """Deploy default configuration to specified target layers."""

    def __call__(
        self,
        *,
        targets: Sequence[DeployTarget],
        force: bool = ...,
        profile: str | None = ...,
        set_permissions: bool = ...,
        dir_mode: int | None = ...,
        file_mode: int | None = ...,
    ) -> list[Path]: ...


class DisplayConfig(Protocol):
    """Display the provided configuration in the requested format."""

    def __call__(
        self, config: Config, *, output_format: OutputFormat = ..., section: str | None = ..., profile: str | None = ...
    ) -> None: ...


class InitLogging(Protocol):
    """Initialize lib_log_rich runtime with the provided configuration."""

    def __call__(self, config: Config) -> None: ...


class LoadSites(Protocol):
    """Read and validate all configured sites from the layered ``Config``."""

    def __call__(self, config: Config) -> list[SiteConfig]: ...


class ContentSource(Protocol):
    """Walk one configured directory and yield sitemap entries.

    Emits both directory URLs (trailing slash) and file URLs, mapping each
    on-disk relative path under ``root`` to a URL under ``url_prefix`` and
    excluding any path matched by ``filter_spec`` (gitignore semantics).
    """

    def __call__(
        self,
        *,
        root: str,
        url_prefix: str,
        filter_spec: FilterSpec,
        default_priority: float,
    ) -> Iterable[SitemapEntry]: ...


class SitemapWriter(Protocol):
    """Serialize sitemap documents to disk with validation.

    Consumes ``documents`` lazily (it must not call ``len()`` or index them) so
    the caller can stream one chunk at a time. Writes a single ``<urlset>`` when
    exactly one document is produced, or numbered child sitemaps plus a
    ``<sitemapindex>`` at ``output_path`` when more than one is. Returns the
    paths actually written.
    """

    def __call__(
        self,
        *,
        documents: Iterable[SitemapDocument],
        output_path: Path,
        base_url: str,
        gzip: bool = ...,
    ) -> list[Path]: ...


__all__ = [
    "ContentSource",
    "DeployConfiguration",
    "DisplayConfig",
    "GetConfig",
    "GetDefaultConfigPath",
    "InitLogging",
    "LoadSites",
    "SitemapWriter",
]
