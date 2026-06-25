"""Port behavioral contract tests - verify in-memory adapter implementations.

Tests exercise in-memory adapters only - production adapters are tested via the
filesystem/lxml/CLI integration tests. Static type conformance is enforced by
pyright via the composition-root assertions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from lib_layered_config import Config

from hugesitemap.adapters.memory import (
    InMemoryContentSource,
    SitemapWriterSpy,
    content_source_empty,
    get_config_in_memory,
    get_default_config_path_in_memory,
    init_logging_in_memory,
    load_sites_in_memory,
)
from hugesitemap.domain.filters import compile_filters
from hugesitemap.domain.model import SitemapDocument, SitemapEntry

if TYPE_CHECKING:
    from hugesitemap.application.ports import (
        ContentSource,
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadSites,
        SitemapWriter,
    )


# ======================== In-Memory Adapter Contract Tests ========================


@pytest.fixture
def get_config_impl() -> GetConfig:
    """Provide in-memory GetConfig implementation."""
    return get_config_in_memory


@pytest.fixture
def get_default_config_path_impl() -> GetDefaultConfigPath:
    """Provide in-memory GetDefaultConfigPath implementation."""
    return get_default_config_path_in_memory


@pytest.fixture
def content_source_impl() -> ContentSource:
    """Provide in-memory ContentSource implementation."""
    return content_source_empty


@pytest.fixture
def write_sitemap_impl() -> SitemapWriter:
    """Provide in-memory SitemapWriter spy."""
    return SitemapWriterSpy()


@pytest.fixture
def load_sites_impl() -> LoadSites:
    """Provide in-memory LoadSites implementation."""
    return load_sites_in_memory


@pytest.fixture
def init_logging_impl() -> InitLogging:
    """Provide in-memory InitLogging implementation."""
    return init_logging_in_memory


@pytest.mark.os_agnostic
def test_get_config_returns_config_with_dict(get_config_impl: GetConfig) -> None:
    """GetConfig must return a Config whose as_dict() yields a dict."""
    config = get_config_impl()
    assert isinstance(config, Config)
    assert isinstance(config.as_dict(), dict)


@pytest.mark.os_agnostic
def test_get_default_config_path_returns_toml_path(get_default_config_path_impl: GetDefaultConfigPath) -> None:
    """GetDefaultConfigPath must return a Path ending in .toml."""
    path = get_default_config_path_impl()
    assert isinstance(path, Path)
    assert path.suffix == ".toml"


@pytest.mark.os_agnostic
def test_content_source_returns_iterable_of_entries() -> None:
    """ContentSource must return entries registered for a root."""
    entry = SitemapEntry(loc="https://x.test/a/", lastmod=None, priority=0.5)
    source = InMemoryContentSource({"/data/a": [entry]})
    result = list(
        source(root="/data/a", url_prefix="https://x.test/a/", matchers=compile_filters(()), default_priority=0.5)
    )
    assert result == [entry]


@pytest.mark.os_agnostic
def test_empty_content_source_yields_nothing(content_source_impl: ContentSource) -> None:
    """The default in-memory ContentSource yields no entries."""
    result = list(
        content_source_impl(root="/x", url_prefix="https://x/", matchers=compile_filters(()), default_priority=0.5)
    )
    assert result == []


@pytest.mark.os_agnostic
def test_writer_spy_records_calls_and_returns_path(write_sitemap_impl: SitemapWriter) -> None:
    """SitemapWriter spy records the call and returns the output path."""
    out = Path("/out/sitemap.xml")
    result = write_sitemap_impl(documents=[SitemapDocument()], output_path=out, base_url="https://x/")
    assert result == [out]


@pytest.mark.os_agnostic
def test_load_sites_reads_site_array(load_sites_impl: LoadSites) -> None:
    """LoadSites must read and validate the [[site]] array from a Config."""
    config = Config({"site": [{"name": "x", "base_url": "https://x.test/", "output_path": "/o.xml"}]}, {})
    result = load_sites_impl(config)
    assert [s.name for s in result] == ["x"]


@pytest.mark.os_agnostic
def test_load_sites_empty_without_site_key(load_sites_impl: LoadSites) -> None:
    """LoadSites returns an empty list when no sites are configured."""
    assert load_sites_impl(Config({}, {})) == []


@pytest.mark.os_agnostic
def test_init_logging_does_not_raise(init_logging_impl: InitLogging) -> None:
    """InitLogging must not raise when called with a Config."""
    config = Config({}, {})
    init_logging_impl(config)


# ======================== Composition Wiring Tests ========================


@pytest.mark.os_agnostic
def test_build_production_returns_fully_populated_app_services() -> None:
    """build_production() must return AppServices with all fields populated."""
    from hugesitemap.composition import AppServices, build_production

    services = build_production()
    assert isinstance(services, AppServices)
    for field_obj in services.__dataclass_fields__:
        assert getattr(services, field_obj) is not None


@pytest.mark.os_agnostic
def test_build_testing_returns_fully_populated_app_services() -> None:
    """build_testing() must return AppServices with all in-memory implementations."""
    from hugesitemap.composition import AppServices, build_testing

    services = build_testing()
    assert isinstance(services, AppServices)
    for field_obj in services.__dataclass_fields__:
        assert getattr(services, field_obj) is not None


@pytest.mark.os_agnostic
def test_build_production_services_are_callable() -> None:
    """All services from build_production() must be callable."""
    from hugesitemap.composition import build_production

    services = build_production()
    for field_name in services.__dataclass_fields__:
        assert callable(getattr(services, field_name))


@pytest.mark.os_agnostic
def test_build_testing_services_are_callable() -> None:
    """All services from build_testing() must be callable."""
    from hugesitemap.composition import build_testing

    services = build_testing()
    for field_name in services.__dataclass_fields__:
        assert callable(getattr(services, field_name))
