"""End-to-end tests for the ``generate`` CLI command (real adapters).

Sites are injected through a layered ``Config`` (the production ``load_sites``
reads them), while the filesystem walker and lxml writer run for real.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from lib_layered_config import Config

from hugesitemap.adapters import cli as cli_mod
from hugesitemap.adapters.cli.exit_codes import ExitCode
from hugesitemap.composition import AppServices, build_production
from hugesitemap.domain.errors import SitemapValidationError
from hugesitemap.domain.model import SitemapDocument


def _site_dict(tmp_path: Path, name: str, *, gzip: bool = False) -> dict[str, Any]:
    data = tmp_path / name / "a000"
    data.mkdir(parents=True)
    (data / "doc.pdf").write_bytes(b"pdf")
    (data / "notes.txt").write_bytes(b"txt")
    out = tmp_path / "out" / f"{name}.xml"
    return {
        "name": name,
        "base_url": f"https://{name}.test/",
        "output_path": str(out),
        "gzip": gzip,
        "directory": [{"path": str(data), "url": f"https://{name}.test/a000/"}],
        "url": [{"loc": f"https://{name}.test/index.html", "changefreq": "yearly", "priority": 0.1}],
        "filters": {"ignore": ["*.txt"]},
    }


def _out(tmp_path: Path, name: str) -> Path:
    return tmp_path / "out" / f"{name}.xml"


@pytest.fixture
def factory_with_sites(
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], Callable[[], AppServices]],
) -> Callable[[list[dict[str, Any]]], Callable[[], AppServices]]:
    """Return a services factory whose config carries the given [[site]] list."""

    def _make(sites: list[dict[str, Any]]) -> Callable[[], AppServices]:
        return inject_config(config_factory({"site": sites}))

    return _make


@pytest.mark.os_agnostic
def test_generate_all_sites_by_default(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([_site_dict(tmp_path, "media"), _site_dict(tmp_path, "www")])
    result = cli_runner.invoke(cli_mod.cli, ["generate"], obj=factory)
    assert result.exit_code == 0, result.output
    assert _out(tmp_path, "media").exists()
    assert _out(tmp_path, "www").exists()
    assert "[media]" in result.output and "[www]" in result.output


@pytest.mark.os_agnostic
def test_generate_writes_expected_urls(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([_site_dict(tmp_path, "media")])
    result = cli_runner.invoke(cli_mod.cli, ["generate"], obj=factory)
    assert result.exit_code == 0, result.output
    body = _out(tmp_path, "media").read_text(encoding="utf-8")
    assert "https://media.test/a000/doc.pdf" in body
    assert "https://media.test/index.html" in body
    assert "notes.txt" not in body  # dropped by filter


@pytest.mark.os_agnostic
def test_generate_keep_mode_indexes_only_allowlisted_files(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    site = _site_dict(tmp_path, "media")
    site["filters"] = {"keep": ["*.pdf"]}  # allowlist: index only PDFs
    factory = factory_with_sites([site])
    result = cli_runner.invoke(cli_mod.cli, ["generate"], obj=factory)
    assert result.exit_code == 0, result.output
    body = _out(tmp_path, "media").read_text(encoding="utf-8")
    assert "https://media.test/a000/doc.pdf" in body  # kept
    assert "notes.txt" not in body  # not in the allowlist


@pytest.mark.os_agnostic
def test_generate_selects_named_sites(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([_site_dict(tmp_path, "media"), _site_dict(tmp_path, "www")])
    result = cli_runner.invoke(cli_mod.cli, ["generate", "--site", "www"], obj=factory)
    assert result.exit_code == 0, result.output
    assert _out(tmp_path, "www").exists()
    assert not _out(tmp_path, "media").exists()


@pytest.mark.os_agnostic
def test_generate_comma_separated_sites(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    sites = [_site_dict(tmp_path, "media"), _site_dict(tmp_path, "www"), _site_dict(tmp_path, "pics")]
    factory = factory_with_sites(sites)
    result = cli_runner.invoke(cli_mod.cli, ["generate", "--site", "media,pics"], obj=factory)
    assert result.exit_code == 0, result.output
    assert _out(tmp_path, "media").exists()
    assert _out(tmp_path, "pics").exists()
    assert not _out(tmp_path, "www").exists()


@pytest.mark.os_agnostic
def test_generate_dry_run_writes_nothing(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([_site_dict(tmp_path, "media")])
    result = cli_runner.invoke(cli_mod.cli, ["generate", "--dry-run"], obj=factory)
    assert result.exit_code == 0, result.output
    assert "dry-run" in result.output
    assert not _out(tmp_path, "media").exists()


@pytest.mark.os_agnostic
def test_generate_gzip(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([_site_dict(tmp_path, "media", gzip=True)])
    result = cli_runner.invoke(cli_mod.cli, ["generate"], obj=factory)
    assert result.exit_code == 0, result.output
    assert (tmp_path / "out" / "media.xml.gz").exists()


@pytest.mark.os_agnostic
def test_generate_unknown_site_exits_config_error(
    tmp_path: Path,
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([_site_dict(tmp_path, "media")])
    result = cli_runner.invoke(cli_mod.cli, ["generate", "--site", "nope"], obj=factory)
    assert result.exit_code == ExitCode.CONFIG_ERROR
    assert "Unknown site" in result.stderr


@pytest.mark.os_agnostic
def test_generate_no_sites_configured_exits_config_error(
    cli_runner: CliRunner,
    factory_with_sites: Callable[[list[dict[str, Any]]], Callable[[], AppServices]],
) -> None:
    factory = factory_with_sites([])
    result = cli_runner.invoke(cli_mod.cli, ["generate"], obj=factory)
    assert result.exit_code == ExitCode.CONFIG_ERROR
    assert "No sites configured" in result.stderr


@pytest.mark.os_agnostic
def test_generate_writer_validation_error_exits_general_error(
    tmp_path: Path,
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    clear_config_cache: None,
) -> None:
    """A SitemapValidationError from the writer exits GENERAL_ERROR (1) with a per-site message."""

    def _config(**_kwargs: Any) -> Config:
        return config_factory({"site": [_site_dict(tmp_path, "media")]})

    def _raising_writer(
        *,
        documents: Sequence[SitemapDocument],
        output_path: Path,
        base_url: str,
        gzip: bool = False,
    ) -> list[Path]:
        raise SitemapValidationError("re-parsed sitemap is not well-formed")

    services = dataclasses.replace(build_production(), get_config=_config, write_sitemap=_raising_writer)
    result = cli_runner.invoke(cli_mod.cli, ["generate"], obj=lambda: services)
    assert result.exit_code == ExitCode.GENERAL_ERROR
    assert "Error [media]" in result.stderr
