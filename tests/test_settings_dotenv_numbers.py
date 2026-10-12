"""Digit-only .env values reach every text setting as the text the operator wrote.

lib_layered_config's dotenv and environment layers turn an unquoted value into an int whenever that
number reads back as the same text (``2026`` stays ``2026``). A text setting must therefore accept
such a number and keep its digits; otherwise a perfectly ordinary ``.env`` line stops the command
with ``Input should be a valid string``.

These tests load a real ``.env`` through the real loader, so a change in the library's coercion
shows up here rather than on a user's machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import pytest
from pydantic import ValidationError

from hugesitemap.adapters.config.loader import get_config
from hugesitemap.adapters.config.site_loader import SitemapDefaults
from hugesitemap.adapters.logging.setup import LoggingConfigModel

if TYPE_CHECKING:
    from pathlib import Path

    from lib_layered_config import Config


@dataclass(frozen=True)
class _FilterCase:
    """One text filter setting fed a digit-only ``.env`` value."""

    env_key: str
    attr: str


_FILTER_CASES = [
    _FilterCase("SITEMAP__FILTERS__KEEP_FILE", "keep_file"),
    _FilterCase("SITEMAP__FILTERS__IGNORE_FILE", "ignore_file"),
    _FilterCase("SITEMAP__FILTERS__NESTED_KEEP_FILENAME", "nested_keep_filename"),
    _FilterCase("SITEMAP__FILTERS__NESTED_IGNORE_FILENAME", "nested_ignore_filename"),
]


def _load_dotenv(tmp_path: Path, *lines: str) -> Config:
    dotenv = tmp_path / ".env"
    dotenv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return get_config(dotenv_path=str(dotenv))


def _section(config: Config, name: str) -> dict[str, Any]:
    return cast("dict[str, Any]", config.get(name, default={}))


@pytest.mark.os_agnostic
@pytest.mark.parametrize("case", _FILTER_CASES, ids=lambda case: case.attr)
def test_digit_only_dotenv_value_reaches_a_filter_setting_as_its_text(
    tmp_path: Path, clear_config_cache: None, case: _FilterCase
) -> None:
    loaded = _section(_load_dotenv(tmp_path, f"{case.env_key}=2026"), "sitemap")
    # Premise: the library hands the value over as a number. Without it the test proves nothing.
    assert isinstance(loaded["filters"][case.attr], int)

    defaults = SitemapDefaults.model_validate(loaded)

    assert getattr(defaults.filters, case.attr) == "2026"


@pytest.mark.os_agnostic
def test_digit_only_dotenv_service_name_reaches_the_logging_model_as_its_text(
    tmp_path: Path, clear_config_cache: None
) -> None:
    loaded = _section(_load_dotenv(tmp_path, "LIB_LOG_RICH__SERVICE=4711"), "lib_log_rich")
    assert isinstance(loaded["service"], int)

    assert LoggingConfigModel.model_validate(loaded).service == "4711"


@pytest.mark.os_agnostic
def test_a_numeric_setting_still_reads_as_a_number(tmp_path: Path, clear_config_cache: None) -> None:
    loaded = _section(_load_dotenv(tmp_path, "SITEMAP__DEFAULT_PRIORITY=1"), "sitemap")

    assert SitemapDefaults.model_validate(loaded).default_priority == 1.0


@pytest.mark.os_agnostic
def test_a_setting_that_is_not_a_scalar_is_still_refused(tmp_path: Path, clear_config_cache: None) -> None:
    loaded = _section(_load_dotenv(tmp_path, "SITEMAP__GZIP=maybe"), "sitemap")

    with pytest.raises(ValidationError, match="gzip"):
        SitemapDefaults.model_validate(loaded)
