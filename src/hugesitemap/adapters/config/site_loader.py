"""Per-site sitemap configuration: pydantic models and multi-site loader.

Site definitions live in the layered application configuration as an array of
tables (``[[site]]``), so all sites are described in one place and discovered
through ``lib_layered_config`` (no separate ``--config`` file, no profiles).
:func:`load_sites` reads and validates them from the merged ``Config``. Any
problem raises :class:`ConfigurationError` with a message suitable for direct
display at the CLI boundary.

Contents:
    * :class:`DirectorySpec` - one ``[[site.directory]]`` block.
    * :class:`ExplicitUrl` - one ``[[site.url]]`` block.
    * :class:`FilterConfig` - the ``[site.filters]`` block.
    * :class:`SiteConfig` - one ``[[site]]`` entry.
    * :func:`load_sites` - read + validate all sites from a ``Config``.
"""

from __future__ import annotations

from typing import Any, cast

from lib_layered_config import Config
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from hugesitemap.domain.errors import ConfigurationError


class DirectorySpec(BaseModel):
    """A configured directory: on-disk path mapped to a URL prefix."""

    model_config = ConfigDict(extra="forbid")

    path: str
    url: str


class ExplicitUrl(BaseModel):
    """An explicit ``[[site.url]]`` entry with its own metadata."""

    model_config = ConfigDict(extra="forbid")

    loc: str
    changefreq: str | None = None
    priority: float = 0.5


class FilterConfig(BaseModel):
    """The ``[site.filters]`` / ``[sitemap.filters]`` block.

    Filtering uses git ``.gitignore`` semantics (via ``igittigitt``).

    The include side (``keep*``) and ignore side are symmetric: each has inline
    patterns, a rule file, and a per-directory nested filename.

    Attributes:
        keep: Inline allowlist patterns. When any ``keep*`` field is set the site
            runs in include mode: only matching paths are indexed, and the ignore
            rules then subtract. Empty (default) means deny mode - every path is
            indexed unless an ignore rule drops it.
        ignore: Inline ``.gitignore`` ignore patterns, anchored at each root.
        keep_file: Optional path to an allowlist rule file.
        ignore_file: Optional path to a ``.gitignore``-format ignore rule file.
        nested_keep_filename: Optional per-directory allowlist filename discovered
            throughout each scanned tree (for example ``.sitemapinclude``).
        nested_ignore_filename: Optional per-directory ignore filename discovered
            throughout each scanned tree (for example ``.sitemapignore``).
    """

    model_config = ConfigDict(extra="forbid")

    keep: list[str] = Field(default_factory=list)
    ignore: list[str] = Field(default_factory=list)
    keep_file: str | None = None
    ignore_file: str | None = None
    nested_keep_filename: str | None = None
    nested_ignore_filename: str | None = None


def _no_directories() -> list[DirectorySpec]:
    """Typed empty default for the ``directories`` field."""
    return []


def _no_urls() -> list[ExplicitUrl]:
    """Typed empty default for the ``explicit_urls`` field."""
    return []


class SiteConfig(BaseModel):
    """A single site's sitemap configuration (one ``[[site]]`` entry).

    Attributes:
        name: Unique site identifier used by the ``--site`` selector.
        base_url: Site base URL (trailing slash recommended).
        output_path: Destination path for the generated ``sitemap.xml``.
        gzip: Whether to write gzip-compressed output.
        default_priority: Priority for every walked entry.
        directories: ``[[site.directory]]`` blocks (TOML key ``directory``).
        explicit_urls: ``[[site.url]]`` blocks (TOML key ``url``).
        filters: The ``[site.filters]`` block.
        directory_urls: Emit directory listing URLs (default ``true``); set
            ``false`` for a files-only sitemap.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    base_url: str
    output_path: str
    gzip: bool = False
    default_priority: float = 0.5
    directory_urls: bool = True
    directories: list[DirectorySpec] = Field(default_factory=_no_directories, alias="directory")
    explicit_urls: list[ExplicitUrl] = Field(default_factory=_no_urls, alias="url")
    filters: FilterConfig = Field(default_factory=FilterConfig)


class SitemapDefaults(BaseModel):
    """Global defaults from the ``[sitemap]`` section, shared by every site.

    Scalars use **override** semantics: ``gzip`` and ``default_priority`` are
    taken from here when a site omits them, and a site value wins when present.

    Filters use **extend** semantics (a deliberate choice, not replace): the
    global ``[sitemap.filters].ignore`` patterns are prepended to every site's
    own ``[site.filters].ignore`` (global first, then the site's own). Because
    gitignore matching is last-match-wins, prepending lets a site re-include a
    globally-ignored path with a ``!`` negation. ``ignore_file`` and
    ``nested_ignore_filename`` fall back to the global value when the site omits
    them.

    The global ``keep`` allowlist extends the same way (global ``keep`` prepended
    to each site's own). Note that setting a global ``keep`` switches **every**
    site into allowlist mode (only matching paths are indexed), so use it only as
    a deliberate site-wide policy.

    Rationale for extend over replace: sites share a common base of junk patterns
    (``*~``, hidden dotfiles, ``*.txt`` ...) and each adds only a few extras.
    Replace semantics would force every site to repeat the whole base just to add
    one pattern - the duplication this section exists to remove.

    Attributes:
        gzip: Default gzip setting for sites that omit ``gzip``.
        default_priority: Default priority for sites that omit ``default_priority``.
        directory_urls: Default for sites that omit ``directory_urls``.
        filters: Filters prepended to / inherited by every site's own filters.
    """

    model_config = ConfigDict(extra="forbid")

    gzip: bool = False
    default_priority: float = 0.5
    directory_urls: bool = True
    filters: FilterConfig = Field(default_factory=FilterConfig)


def _load_global_defaults(config: Config) -> SitemapDefaults:
    """Read and validate the optional ``[sitemap]`` global-defaults section."""
    raw: Any = config.get("sitemap")
    if raw is None:
        return SitemapDefaults()
    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration key 'sitemap' must be a table ([sitemap]).")
    try:
        return SitemapDefaults.model_validate(raw)
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid [sitemap] section: {exc}") from exc


def _with_scalar_defaults(item: Any, defaults: SitemapDefaults) -> Any:
    """Fill a raw site mapping with the global scalar defaults it did not set.

    Only the scalars ``gzip``, ``default_priority``, and ``directory_urls`` are
    touched (override semantics); filters are merged separately after validation.
    Non-mapping items are returned unchanged so per-site schema validation rejects
    them clearly.
    """
    if not isinstance(item, dict):
        return item
    merged: dict[str, Any] = dict(cast("dict[str, Any]", item))
    merged.setdefault("gzip", defaults.gzip)
    merged.setdefault("default_priority", defaults.default_priority)
    merged.setdefault("directory_urls", defaults.directory_urls)
    return merged


def _extend_filters(site: SiteConfig, defaults: SitemapDefaults) -> SiteConfig:
    """Merge the global filters into a site's own filters.

    Extend, not replace (deliberate; see :class:`SitemapDefaults`): the resolved
    ignore list is ``global ignore + site ignore`` (global first, so a site can
    override a global pattern with a ``!`` negation). ``ignore_file`` and
    ``nested_ignore_filename`` use the site value, falling back to the global.
    """
    glob = defaults.filters
    merged = FilterConfig(
        keep=[*glob.keep, *site.filters.keep],
        ignore=[*glob.ignore, *site.filters.ignore],
        keep_file=site.filters.keep_file or glob.keep_file,
        ignore_file=site.filters.ignore_file or glob.ignore_file,
        nested_keep_filename=site.filters.nested_keep_filename or glob.nested_keep_filename,
        nested_ignore_filename=site.filters.nested_ignore_filename or glob.nested_ignore_filename,
    )
    if merged == site.filters:
        return site
    return site.model_copy(update={"filters": merged})


def load_sites(config: Config) -> list[SiteConfig]:
    """Read and validate all ``[[site]]`` entries from the merged configuration.

    Args:
        config: The layered application configuration.

    Global defaults from the ``[sitemap]`` section are applied to each site:
    ``gzip``/``default_priority`` are inherited unless the site overrides them,
    and the global ignore filters are prepended to each site's own filters (see
    :class:`SitemapDefaults`).

    Returns:
        The validated sites in declaration order (empty if none are configured).

    Raises:
        ConfigurationError: If ``sitemap`` is not a table, ``site`` is not an
            array of tables, an entry fails schema validation, or two entries
            share a name.
    """
    defaults = _load_global_defaults(config)
    raw: Any = config.get("site")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ConfigurationError("Configuration key 'site' must be an array of tables ([[site]]).")

    sites: list[SiteConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(cast("list[Any]", raw)):
        try:
            site = SiteConfig.model_validate(_with_scalar_defaults(item, defaults))
        except ValidationError as exc:
            raise ConfigurationError(f"Invalid [[site]] #{index + 1}: {exc}") from exc
        if site.name in seen:
            raise ConfigurationError(f"Duplicate site name: {site.name!r}")
        seen.add(site.name)
        sites.append(_extend_filters(site, defaults))
    return sites


__all__ = [
    "DirectorySpec",
    "ExplicitUrl",
    "FilterConfig",
    "SiteConfig",
    "SitemapDefaults",
    "load_sites",
]
