"""Exit codes and stderr through the real ``main()`` entry point.

``CliRunner.invoke(cli, ...)`` calls the click command tree directly and never runs
``main()``'s ``standalone_mode=False`` handling, which is where a bare ``SystemExit`` from a
command falls into the catch-all branch and is printed to stderr as ``SystemExit: N`` - text
a user reads as a crash. These tests go through ``main()`` itself, as a console script does,
with the services replaced at the composition seam.
"""

from __future__ import annotations

import dataclasses
import os
from typing import TYPE_CHECKING, Any

import click
import pytest
from lib_layered_config import Config

from hugesitemap.adapters.cli.main import main
from hugesitemap.composition import AppServices, build_testing
from hugesitemap.domain.errors import SitemapValidationError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def _services(data: dict[str, Any], **overrides: Any) -> Callable[[], AppServices]:
    config = Config(data, {})

    def get_config(**_kwargs: Any) -> Config:
        return config

    def build() -> AppServices:
        return dataclasses.replace(build_testing(), get_config=get_config, **overrides)

    return build


def _raising(error: Exception) -> Callable[..., Any]:
    def raise_it(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    return raise_it


def _one_site(tmp_path: Path) -> dict[str, Any]:
    return {
        "site": [
            {
                "name": "media",
                "base_url": "https://media.test/",
                "output_path": str(tmp_path / "sitemap.xml"),
                "url": [{"loc": "https://media.test/index.html"}],
            }
        ]
    }


@pytest.mark.os_agnostic
def test_generate_without_sites_exits_78_without_printing_systemexit(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["generate"], services_factory=_services({}))

    err = capsys.readouterr().err
    assert exit_code == 78
    assert "No sites configured" in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
def test_a_sitemap_validation_failure_exits_1_without_printing_systemexit(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    services = _services(_one_site(tmp_path), write_sitemap=_raising(SitemapValidationError("not well-formed")))
    exit_code = main(["generate"], services_factory=services)

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "Error [media]: not well-formed" in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
def test_a_sitemap_that_cannot_be_written_exits_with_the_platform_permission_code(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """The writer's PermissionError reaches main()'s exit-code mapping, which is per platform.

    lib_cli_exit_tools maps PermissionError to EACCES (13) on POSIX and to ERROR_ACCESS_DENIED (5)
    on Windows; generate has no explicit mapping of its own, unlike config-deploy.
    """
    services = _services(_one_site(tmp_path), write_sitemap=_raising(PermissionError("denied")))
    exit_code = main(["generate"], services_factory=services)

    err = capsys.readouterr().err
    assert exit_code == (13 if os.name == "posix" else 5)
    assert "denied" in err


@pytest.mark.os_agnostic
def test_a_config_display_error_exits_22_without_printing_systemexit(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["config"], services_factory=_services({}, display_config=_raising(ValueError("boom"))))

    err = capsys.readouterr().err
    assert exit_code == 22
    assert "boom" in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("error", "expected"),
    [(PermissionError("denied"), 13), (OSError("disk full"), 1)],
    ids=["permission-denied", "general-error"],
)
def test_a_deploy_failure_exits_with_its_code_without_printing_systemexit(
    capsys: pytest.CaptureFixture[str], error: Exception, expected: int
) -> None:
    services = _services({}, deploy_configuration=_raising(error))
    exit_code = main(["config-deploy", "--target", "user"], services_factory=services)

    err = capsys.readouterr().err
    assert exit_code == expected
    assert str(error) in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
def test_a_deliberate_exit_inside_deploy_keeps_its_own_code(capsys: pytest.CaptureFixture[str]) -> None:
    """click's Exit is a RuntimeError; the deploy failure branch must let it through unrelabelled."""
    services = _services({}, deploy_configuration=_raising(click.exceptions.Exit(78)))
    exit_code = main(["config-deploy", "--target", "user"], services_factory=services)

    err = capsys.readouterr().err
    assert exit_code == 78
    assert "Failed to deploy configuration" not in err


@pytest.mark.os_agnostic
def test_a_generate_examples_failure_exits_1_without_printing_systemexit(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("not a directory", encoding="utf-8")

    exit_code = main(
        ["config-generate-examples", "--destination", str(blocker / "sub")], services_factory=_services({})
    )

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "Error:" in err
    assert "SystemExit" not in err


@pytest.mark.os_agnostic
def test_a_successful_command_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["info"], services_factory=_services({}))

    assert exit_code == 0
    assert "Info for hugesitemap" in capsys.readouterr().out
