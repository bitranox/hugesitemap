"""The ``generate`` CLI command: build sitemaps for configured sites.

Reads the ``[[site]]`` entries from the layered configuration, selects the
requested ones with ``--site`` (default ``all``), maps each onto the
application's :class:`GenerateRequest`, and runs the :func:`generate_sitemap`
use case with the wired content-source and writer services. Configuration and
I/O errors are reported with a clear message and a meaningful exit code.

Contents:
    * :func:`cli_generate` - the ``generate`` command.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import lib_log_rich.runtime
import rich_click as click

from hugesitemap.application.generate import (
    DirectoryRequest,
    GenerateRequest,
    GenerateResult,
    generate_sitemap,
)
from hugesitemap.domain.errors import ConfigurationError, SitemapValidationError
from hugesitemap.domain.filters import FilterSpec
from hugesitemap.domain.model import SitemapEntry

from ..constants import CLICK_CONTEXT_SETTINGS
from ..context import get_cli_context
from ..exit_codes import ExitCode
from ..typed_click import option

if TYPE_CHECKING:
    from hugesitemap.adapters.config.site_loader import SiteConfig
    from hugesitemap.composition import AppServices

logger = logging.getLogger(__name__)

ALL_SITES = "all"
"""``--site`` token selecting every configured site."""


def _build_request(site: SiteConfig, *, gzip: bool, dry_run: bool) -> GenerateRequest:
    """Map a validated SiteConfig onto an application GenerateRequest."""
    directories = tuple(
        DirectoryRequest(root=d.path, url_prefix=d.url, directory_urls=d.directory_urls) for d in site.directories
    )
    explicit = tuple(
        SitemapEntry(loc=u.loc, lastmod=None, priority=u.priority, changefreq=u.changefreq) for u in site.explicit_urls
    )
    filter_spec = FilterSpec(
        keep_patterns=tuple(site.filters.keep),
        patterns=tuple(site.filters.ignore),
        keep_file=site.filters.keep_file,
        ignore_file=site.filters.ignore_file,
        nested_keep_filename=site.filters.nested_keep_filename,
        nested_ignore_filename=site.filters.nested_ignore_filename,
    )
    return GenerateRequest(
        base_url=site.base_url,
        output_path=site.output_path,
        gzip=gzip or site.gzip,
        default_priority=site.default_priority,
        directories=directories,
        explicit_entries=explicit,
        filter_spec=filter_spec,
        directory_urls=site.directory_urls,
        dry_run=dry_run,
    )


def _select_sites(sites: list[SiteConfig], requested: str) -> list[SiteConfig]:
    """Return the sites named by ``requested`` (comma-separated, or ``all``).

    Raises:
        ConfigurationError: If no sites are configured or a requested name is
            not present.
    """
    if not sites:
        raise ConfigurationError("No sites configured. Add at least one [[site]] entry to the configuration.")
    names = [token.strip() for token in requested.split(",") if token.strip()]
    if not names or ALL_SITES in names:
        return sites
    by_name = {site.name: site for site in sites}
    unknown = [name for name in names if name not in by_name]
    if unknown:
        available = ", ".join(sorted(by_name)) or "(none)"
        raise ConfigurationError(f"Unknown site(s): {', '.join(unknown)}. Available: {available}.")
    return [by_name[name] for name in names]


@click.command("generate", context_settings=CLICK_CONTEXT_SETTINGS)
@option(
    "--site",
    "site_selector",
    default=ALL_SITES,
    show_default=True,
    metavar="NAME[,NAME...]|all",
    help="Comma-separated site names to generate, or 'all' (default).",
)
@option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Walk and validate but do not write any files.",
)
@option(
    "--gzip",
    is_flag=True,
    default=False,
    help="Write gzip-compressed sitemap output (overrides config when set).",
)
@click.pass_context
def cli_generate(ctx: click.Context, site_selector: str, dry_run: bool, gzip: bool) -> None:
    """Generate sitemap.xml for the configured sites selected by --site.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli_generate, ["--help"])
        >>> result.exit_code
        0
    """
    cli_ctx = get_cli_context(ctx)
    services = cli_ctx.services
    with lib_log_rich.runtime.bind(job_id="cli-generate", extra={"command": "generate"}):
        try:
            sites = _select_sites(services.load_sites(cli_ctx.config), site_selector)
        except ConfigurationError as exc:
            logger.error("Configuration error: %s", exc)
            click.echo(f"\nError: {exc}", err=True)
            raise SystemExit(ExitCode.CONFIG_ERROR) from exc

        for site in sites:
            _generate_one(services, site, gzip=gzip, dry_run=dry_run)


def _generate_one(services: AppServices, site: SiteConfig, *, gzip: bool, dry_run: bool) -> None:
    """Generate and report a single site, mapping errors to exit codes."""
    try:
        result = generate_sitemap(
            _build_request(site, gzip=gzip, dry_run=dry_run),
            content_source=services.content_source,
            write_sitemap=services.write_sitemap,
        )
    except SitemapValidationError as exc:
        logger.error("Sitemap validation failed for %s: %s", site.name, exc)
        click.echo(f"\nError [{site.name}]: {exc}", err=True)
        raise SystemExit(ExitCode.GENERAL_ERROR) from exc
    except ConfigurationError as exc:
        logger.error("Configuration error for %s: %s", site.name, exc)
        click.echo(f"\nError [{site.name}]: {exc}", err=True)
        raise SystemExit(ExitCode.CONFIG_ERROR) from exc
    _report(site, result, dry_run=dry_run)


def _report(site: SiteConfig, result: GenerateResult, *, dry_run: bool) -> None:
    """Echo a human-readable summary of one site's generate result."""
    if dry_run:
        click.echo(f"[{site.name}] Would write {result.url_count} URLs (dry-run, split={result.was_split}).")
        return
    files = ", ".join(str(path) for path in result.paths_written)
    click.echo(f"[{site.name}] Wrote {result.url_count} URLs to {files} (split={result.was_split}).")


__all__ = ["cli_generate"]
