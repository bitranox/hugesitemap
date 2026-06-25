"""Tests for the multi-site loader (reads [[site]] from a layered Config)."""

from __future__ import annotations

from typing import Any

import pytest
from lib_layered_config import Config

from hugesitemap.adapters.config.site_loader import load_sites
from hugesitemap.domain.errors import ConfigurationError

MEDIA: dict[str, Any] = {
    "name": "media",
    "base_url": "https://media.test/",
    "output_path": "/out/media.xml",
    "directory": [{"path": "/data/a000", "url": "https://media.test/a000/"}],
    "url": [{"loc": "https://media.test/index.html", "changefreq": "yearly", "priority": 0.1}],
    "filters": {"drop": ["*~", "re:/\\.[^/]*"]},
}
WWW: dict[str, Any] = {"name": "www", "base_url": "https://www.test/", "output_path": "/out/www.xml"}


def _config(*sites: dict[str, Any]) -> Config:
    return Config({"site": list(sites)}, {})


def _config_with(defaults: dict[str, Any], *sites: dict[str, Any]) -> Config:
    return Config({"sitemap": defaults, "site": list(sites)}, {})


def test_loads_multiple_sites() -> None:
    sites = load_sites(_config(MEDIA, WWW))
    assert [s.name for s in sites] == ["media", "www"]
    media = sites[0]
    assert media.base_url == "https://media.test/"
    assert media.directories[0].path == "/data/a000"
    assert media.explicit_urls[0].changefreq == "yearly"
    assert media.filters.drop == ["*~", r"re:/\.[^/]*"]


def test_no_site_key_returns_empty() -> None:
    assert load_sites(Config({}, {})) == []


def test_site_not_a_list_raises() -> None:
    with pytest.raises(ConfigurationError, match="array of tables"):
        load_sites(Config({"site": {"name": "x"}}, {}))


def test_invalid_site_raises() -> None:
    with pytest.raises(ConfigurationError, match=r"Invalid \[\[site\]\] #1"):
        load_sites(_config({"name": "broken"}))  # missing base_url/output_path


def test_unknown_key_rejected() -> None:
    bad = {"name": "x", "base_url": "https://x/", "output_path": "/o", "bogus": 1}
    with pytest.raises(ConfigurationError, match=r"Invalid \[\[site\]\]"):
        load_sites(_config(bad))


def test_duplicate_names_rejected() -> None:
    with pytest.raises(ConfigurationError, match="Duplicate site name"):
        load_sites(_config(WWW, WWW))


def test_defaults_applied() -> None:
    sites = load_sites(_config(WWW))
    site = sites[0]
    assert site.gzip is False
    assert site.default_priority == 0.5
    assert site.directories == []
    assert site.filters.drop == []


# --- global [sitemap] defaults --------------------------------------------


def test_global_defaults_inherited_by_sites() -> None:
    defaults = {"gzip": True, "default_priority": 0.7, "filters": {"drop": ["*~"]}}
    sites = load_sites(_config_with(defaults, WWW))
    site = sites[0]
    assert site.gzip is True
    assert site.default_priority == 0.7
    assert site.filters.drop == ["*~"]  # inherited; site has no filters of its own


def test_site_overrides_global_scalars() -> None:
    defaults = {"gzip": True, "default_priority": 0.7}
    override = {**WWW, "gzip": False, "default_priority": 0.2}
    sites = load_sites(_config_with(defaults, override))
    assert sites[0].gzip is False
    assert sites[0].default_priority == 0.2


def test_global_filters_extend_site_filters() -> None:
    defaults = {"filters": {"drop": ["*~", "*.log*"]}}
    site = {**WWW, "filters": {"drop": ["*.tmp*"]}}
    sites = load_sites(_config_with(defaults, site))
    # Global patterns first, then the site's own.
    assert sites[0].filters.drop == ["*~", "*.log*", "*.tmp*"]


def test_global_filters_apply_when_site_has_none() -> None:
    defaults = {"filters": {"drop": ["*~"]}}
    sites = load_sites(_config_with(defaults, WWW))
    assert sites[0].filters.drop == ["*~"]


def test_no_global_filters_leaves_site_filters_untouched() -> None:
    sites = load_sites(_config_with({"gzip": True}, {**WWW, "filters": {"drop": ["*.tmp*"]}}))
    assert sites[0].filters.drop == ["*.tmp*"]


def test_invalid_global_section_raises() -> None:
    with pytest.raises(ConfigurationError, match=r"Invalid \[sitemap\] section"):
        load_sites(_config_with({"bogus": 1}, WWW))


def test_global_section_must_be_table() -> None:
    with pytest.raises(ConfigurationError, match="must be a table"):
        load_sites(Config({"sitemap": [1, 2], "site": [WWW]}, {}))
