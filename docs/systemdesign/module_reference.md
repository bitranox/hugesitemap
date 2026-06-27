# Module Reference: Architecture & File Index

## Status

Complete (current codebase)

---

## Related Files

### Domain Layer
- `src/hugesitemap/domain/model.py` - Sitemap value objects (SitemapEntry, SitemapDocument, SitemapIndexEntry)
- `src/hugesitemap/domain/enums.py` - Type-safe enums (ChangeFreq, OutputFormat, DeployTarget)
- `src/hugesitemap/domain/errors.py` - Domain exception types (ConfigurationError, SitemapValidationError)
- `src/hugesitemap/domain/filters.py` - Path-exclusion value object (FilterSpec; gitignore semantics)
- `src/hugesitemap/domain/formatting.py` - ISO8601, priority, and URL formatting helpers
- `src/hugesitemap/domain/limits.py` - Sitemap size limits and entry chunking
- `src/hugesitemap/domain/__init__.py` - Domain exports

### Application Layer
- `src/hugesitemap/application/ports.py` - Callable Protocol definitions for adapter functions
- `src/hugesitemap/application/generate.py` - The GenerateSitemap use case and its request/response DTOs
- `src/hugesitemap/application/__init__.py` - Application exports

### Adapters Layer
- `src/hugesitemap/adapters/filesystem.py` - Filesystem content source (walk_directory)
- `src/hugesitemap/adapters/gitignore_filter.py` - igittigitt-backed path filter (build_filter, GitignoreFilter)
- `src/hugesitemap/adapters/sitemap_lxml.py` - lxml-backed sitemap writer (write_sitemap)
- `src/hugesitemap/adapters/typed_lxml.py` - Typed facade over the untyped lxml.etree surface
- `src/hugesitemap/adapters/typed_deflate.py` - Typed facade over the deflate (libdeflate) gzip API
- `src/hugesitemap/adapters/config/loader.py` - Configuration loading with LRU caching + profile validation
- `src/hugesitemap/adapters/config/deploy.py` - Configuration deployment
- `src/hugesitemap/adapters/config/display.py` - Configuration display (delegates to lib_layered_config)
- `src/hugesitemap/adapters/config/overrides.py` - CLI `--set` override parsing and deep-merge
- `src/hugesitemap/adapters/config/permissions.py` - File permission defaults for deploy targets
- `src/hugesitemap/adapters/config/site_loader.py` - Per-site config models and multi-site loader (load_sites)
- `src/hugesitemap/adapters/logging/setup.py` - lib_log_rich initialization
- `src/hugesitemap/adapters/cli/` - CLI adapter package:
  - `__init__.py` - Public facade
  - `constants.py` - Shared Click constants
  - `exit_codes.py` - POSIX exit codes (ExitCode IntEnum)
  - `context.py` - Click context helpers (CLIContext)
  - `typed_click.py` - Typed wrappers for rich_click option/version_option decorators
  - `root.py` - Root command group with global options
  - `main.py` - CLI entry point and execution wrapper
  - `commands/info.py` - info, fail commands
  - `commands/config.py` - config, config-deploy, config-generate-examples commands
  - `commands/generate.py` - generate command
  - `commands/logging.py` - logdemo command

### Adapters Layer (In-Memory / Testing)
- `src/hugesitemap/adapters/memory/__init__.py` - Public facade for in-memory adapters
- `src/hugesitemap/adapters/memory/config.py` - In-memory config adapters
- `src/hugesitemap/adapters/memory/sitemap.py` - In-memory content source, writer spy, site-config loader
- `src/hugesitemap/adapters/memory/logging.py` - In-memory logging (no-op)

### Composition Layer
- `src/hugesitemap/composition/__init__.py` - Wires adapters to ports (AppServices, build_production, build_testing)

### Entry Points
- `src/hugesitemap/__main__.py` - Thin shim for `python -m`
- `src/hugesitemap/entry.py` - Console script entry point with production wiring
- `src/hugesitemap/__init__.py` - Public API exports
- `src/hugesitemap/__init__conf__.py` - Package metadata constants

### Configuration Defaults
- `src/hugesitemap/adapters/config/defaultconfig.toml` - Base defaults
- `src/hugesitemap/adapters/config/defaultconfig.d/30-sites.toml` - Sitemap site-definition schema (ships with no sites configured)
- `src/hugesitemap/adapters/config/defaultconfig.d/40-layered-config.toml` - lib_layered_config integration docs
- `src/hugesitemap/adapters/config/defaultconfig.d/90-logging.toml` - Logging defaults

---

## Architecture

### Layer Assignments

| Directory/Module                                      | Layer       | Responsibility                                           |
|-------------------------------------------------------|-------------|----------------------------------------------------------|
| `domain/`                                             | Domain      | Pure logic - no I/O, logging, or frameworks              |
| `application/ports.py`                                | Application | Protocol definitions for adapters                        |
| `application/generate.py`                             | Application | The GenerateSitemap use case and its DTOs                |
| `adapters/filesystem.py`                              | Adapters    | Walk a directory tree into sitemap entries               |
| `adapters/sitemap_lxml.py`                            | Adapters    | Serialize sitemap documents to disk with validation      |
| `adapters/typed_lxml.py`, `adapters/typed_deflate.py` | Adapters    | Typed facades over untyped third-party surfaces          |
| `adapters/config/`                                    | Adapters    | Configuration loading, deployment, display, site loading |
| `adapters/logging/`                                   | Adapters    | lib_log_rich initialization                              |
| `adapters/cli/`                                       | Adapters    | Click/rich_click CLI framework integration               |
| `adapters/memory/`                                    | Adapters    | In-memory implementations for testing                    |
| `composition/`                                        | Composition | Wires adapters to ports                                  |

### Import Enforcement

Layer boundaries enforced via `import-linter` contracts in `pyproject.toml`:
- **Domain is pure**: Cannot import from adapters or composition
- **Clean Architecture layers**: Validates dependency direction (composition -> adapters -> application -> domain)

Run `lint-imports` to verify compliance.

---

## Domain Layer Modules

### model.py - Sitemap value objects

Frozen dataclasses modeling the sitemaps.org 0.9 data shape. No I/O or framework dependencies.

| Type                | Description                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------------|
| `SitemapEntry`      | One `<url>` entry: `loc`, `lastmod` (UTC or None), `priority` (0.0-1.0), `changefreq` (or None) |
| `SitemapDocument`   | One `<urlset>` worth of entries, in emission order                                              |
| `SitemapIndexEntry` | One `<sitemap>` child reference inside a `<sitemapindex>`: `loc`, `lastmod`                     |

### enums.py - Type-safe enumerations

All enums inherit from `str` for direct comparison and Click integration.

| Enum           | Members                                                            |
|----------------|--------------------------------------------------------------------|
| `OutputFormat` | `HUMAN`, `JSON` - config display output formats                    |
| `ChangeFreq`   | sitemaps.org `<changefreq>` hint values (e.g. `YEARLY`, `MONTHLY`) |
| `DeployTarget` | `APP`, `HOST`, `USER` - config deployment target layers            |

### errors.py - Domain exceptions

| Exception                | Raised when                                                                           |
|--------------------------|---------------------------------------------------------------------------------------|
| `ConfigurationError`     | Required configuration values are absent, malformed, or inconsistent                  |
| `SitemapValidationError` | Generated sitemap XML fails re-parse validation or a structural invariant is violated |

### filters.py - Path-exclusion value object

A pure value object describing a site's exclusion rules. The actual matching uses
git `.gitignore` semantics and is performed by `igittigitt` in the adapter layer
(`adapters/gitignore_filter.py`), so the domain stays free of I/O and third-party
imports.

| Symbol       | Description                                                                                                                                                                                |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `FilterSpec` | Immutable rule description: include side (`keep_patterns`, `keep_file`, `nested_keep_filename`) and ignore side (`patterns`, `ignore_file`, `nested_ignore_filename`); `is_empty` property |

### formatting.py - Pure serialization helpers

| Function                    | Description                                                          |
|-----------------------------|----------------------------------------------------------------------|
| `mtime_to_utc(mtime)`       | Epoch seconds (an `os.stat` mtime) to a timezone-aware UTC datetime  |
| `iso8601_z(moment)`         | UTC datetime to `YYYY-MM-DDTHH:MM:SSZ`                               |
| `format_priority(value)`    | Float to a fixed 4-decimal string                                    |
| `join_url(prefix, relpath)` | Join a URL prefix with a relative path, collapsing duplicate slashes |

### limits.py - Size limits and chunking

The sitemaps.org protocol caps a single sitemap at 50,000 URLs and 50 MiB uncompressed.

| Symbol                                      | Description                                                                                    |
|---------------------------------------------|------------------------------------------------------------------------------------------------|
| `MAX_URLS`                                  | Maximum URLs per sitemap document                                                              |
| `MAX_BYTES`                                 | Maximum uncompressed bytes per sitemap document                                                |
| `chunk_entries(entries, max_urls=MAX_URLS)` | Split entries into URL-capped chunks (URL cap; the byte cap is enforced by the writer adapter) |

---

## Application Layer Modules

### ports.py - Callable Protocols

Each Protocol defines a `__call__` whose signature matches the corresponding adapter
function; existing module-level functions satisfy them via structural subtyping.
Infrastructure types (`Config`, `SiteConfig`) are imported under `TYPE_CHECKING` only.

| Protocol               | Adapter behaviour it abstracts                          |
|------------------------|---------------------------------------------------------|
| `GetConfig`            | Load the merged layered configuration                   |
| `GetDefaultConfigPath` | Locate the bundled default config file                  |
| `DeployConfiguration`  | Deploy configuration to target layers                   |
| `DisplayConfig`        | Render configuration for the `config` command           |
| `InitLogging`          | Initialize the logging runtime                          |
| `LoadSites`            | Read and validate `[[site]]` entries from a `Config`    |
| `ContentSource`        | Walk one configured directory and yield sitemap entries |
| `SitemapWriter`        | Serialize sitemap documents to disk with validation     |

### generate.py - The GenerateSitemap use case

Pure orchestration over the `ContentSource` and `SitemapWriter` ports. Imports only
domain types and stdlib; never touches the filesystem or lxml directly.

| Symbol                                                     | Description                                                                                                                                 |
|------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `DirectoryRequest`                                         | One on-disk root (`root`) mapped to a URL prefix (`url_prefix`)                                                                             |
| `GenerateRequest`                                          | Full input for one site: `base_url`, `output_path`, `gzip`, `default_priority`, `directories`, `explicit_entries`, `filter_spec`, `dry_run` |
| `GenerateResult`                                           | Outcome: `url_count`, `paths_written`, `was_split`                                                                                          |
| `generate_sitemap(request, content_source, write_sitemap)` | Walk directories, append explicit entries, split into protocol-compliant documents, and write (unless dry-run)                              |

---

## Adapters Layer Modules

### filesystem.py - Filesystem content source

Implements the `ContentSource` port. For each configured directory it emits a
directory URL (trailing slash, the directory's own mtime) and a file URL per
surviving file, dropping any path matched by the ordered filter engine. Dropped
directories are pruned so their contents are never visited.

| Function                                                       | Description                                                                     |
|----------------------------------------------------------------|---------------------------------------------------------------------------------|
| `walk_directory(root, url_prefix, matchers, default_priority)` | Yield directory and file `SitemapEntry` objects in deterministic (sorted) order |

### sitemap_lxml.py - lxml-backed sitemap writer

Implements the `SitemapWriter` port. Builds a `<urlset>` with the sitemaps.org 0.9
namespace and `xsi:schemaLocation`. With more than one document it writes numbered
child sitemaps plus a `<sitemapindex>`. Every file is validated by re-parsing the
serialized bytes before being moved into place with an atomic rename, and may be
gzip-compressed via libdeflate.

| Symbol                                                  | Description                                                                                     |
|---------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `SITEMAP_NS`, `XSI_NS`, `SCHEMA_LOCATION`               | Namespace and schema-location constants                                                         |
| `write_sitemap(documents, output_path, base_url, gzip)` | Write one or more documents; returns the list of paths written (children first, then the index) |

### typed_lxml.py - Typed facade over lxml.etree

lxml ships no type stubs. This module is the single, narrowly-scoped boundary where
the lxml-related pyright rules are turned off; every other module imports these
fully-typed wrappers and stays strict-clean.

Exports: `XmlElement`, `XmlSyntaxError`, `new_element`, `child`, `set_attribute`,
`set_text`, `serialize`, `parse`.

### typed_deflate.py - Typed facade over libdeflate

libdeflate is chosen (over stdlib `gzip` and `isal`) because the `.gz` sitemap is a
write-once, serve-many artifact where compression ratio is the optimisation target.

| Symbol                                      | Description                                                |
|---------------------------------------------|------------------------------------------------------------|
| `GZIP_MAX_LEVEL`                            | libdeflate's maximum compression level                     |
| `gzip_compress(data, level=GZIP_MAX_LEVEL)` | Compress bytes to standard gzip format (immutable `bytes`) |

### config/site_loader.py - Per-site sitemap configuration

Site definitions live in the layered configuration as an array of tables
(`[[site]]`). Pydantic models validate them; any problem raises `ConfigurationError`
with a CLI-ready message.

| Type                 | Description                                                                                                                    |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `DirectorySpec`      | One `[[site.directory]]` block                                                                                                 |
| `ExplicitUrl`        | One `[[site.url]]` block                                                                                                       |
| `FilterConfig`       | The `[site.filters]` block                                                                                                     |
| `SiteConfig`         | One `[[site]]` entry: `name`, `base_url`, `output_path`, `gzip`, `default_priority`, `directories`, `explicit_urls`, `filters` |
| `SitemapDefaults`    | Global `[sitemap]` defaults shared by every site (scalars override, filters extend)                                            |
| `load_sites(config)` | Read and validate all sites from a merged `Config`                                                                             |

### config/loader.py - Configuration loading

| Symbol                                       | Description                                                              |
|----------------------------------------------|--------------------------------------------------------------------------|
| `validate_profile(profile, max_length=None)` | Validate a profile name via `lib_layered_config.validate_profile_name()` |
| `get_default_config_path()`                  | Absolute path to the bundled `defaultconfig.toml` (cached)               |
| `get_config(...)`                            | Load the merged layered configuration (LRU-cached)                       |

### config/deploy.py - Configuration deployment

| Function                                                                              | Description                                                              |
|---------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| `deploy_configuration(targets, force, profile, set_permissions, dir_mode, file_mode)` | Copy the bundled defaults to app/host/user layers; returns created paths |

### config/display.py - Configuration display

| Function                                                           | Description                                                                                   |
|--------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `display_config(config, output_format, section, console, profile)` | Render configuration via lib_layered_config's Rich display, flushing pending log output first |

### config/overrides.py - `--set` override parsing

| Symbol                | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| `ConfigOverride`      | Parsed override: `section`, `key_path` tuple, coerced `value`    |
| `parse_override(raw)` | Split `SECTION.KEY[.SUBKEY...]=VALUE` into a `ConfigOverride`    |
| `coerce_value(raw)`   | Coerce a raw string via JSON parsing, falling back to the string |

### config/permissions.py - Deploy permission defaults

| Symbol                            | Description                                                          |
|-----------------------------------|----------------------------------------------------------------------|
| `PermissionDefaults`              | Validated, immutable per-layer permission modes plus an enabled flag |
| `parse_mode(value, default)`      | Parse a mode from an int or octal string (`"0o755"`, `"755"`)        |
| `get_permission_defaults(config)` | Load defaults from `[lib_layered_config.default_permissions]`        |

### logging/setup.py - Logging initialization

| Symbol                 | Description                                                                        |
|------------------------|------------------------------------------------------------------------------------|
| `LoggingConfigModel`   | Pydantic model for the `[lib_log_rich]` config section (extra fields pass through) |
| `init_logging(config)` | Idempotent lib_log_rich runtime initialization from layered config                 |

---

## Composition Layer

### composition/__init__.py - Dependency wiring

| Symbol                       | Description                                                                                                                                                                     |
|------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `AppServices`                | Container of wired services: `get_config`, `get_default_config_path`, `deploy_configuration`, `display_config`, `load_sites`, `content_source`, `write_sitemap`, `init_logging` |
| `build_production()`         | Wire production adapters into an `AppServices` container                                                                                                                        |
| `build_testing(writer=None)` | Wire in-memory adapters (optionally a `SitemapWriterSpy`) for tests                                                                                                             |

---

## Exit Codes

POSIX-conventional exit codes defined in `adapters/cli/exit_codes.py` (`ExitCode` IntEnum):

| Code | Name                | Usage                                        |
|------|---------------------|----------------------------------------------|
| 0    | `SUCCESS`           | Command completed successfully               |
| 1    | `GENERAL_ERROR`     | Unhandled exception, general failure         |
| 2    | `FILE_NOT_FOUND`    | File or directory not found                  |
| 13   | `PERMISSION_DENIED` | Cannot write to target directory             |
| 22   | `INVALID_ARGUMENT`  | Invalid CLI argument or section not found    |
| 69   | `SMTP_FAILURE`      | Service unavailable (EX_UNAVAILABLE)         |
| 78   | `CONFIG_ERROR`      | Missing or invalid configuration (EX_CONFIG) |
| 110  | `TIMEOUT`           | Operation timed out                          |
| 130  | `SIGNAL_INT`        | Interrupted (SIGINT/Ctrl+C), informational   |
| 141  | `BROKEN_PIPE`       | Output pipe closed, informational            |
| 143  | `SIGNAL_TERM`       | Terminated (SIGTERM), informational          |

Signal codes (130, 141, 143) are informational only; `lib_cli_exit_tools` handles
signal-to-exit-code translation.

---

## CLI Commands

Registered in `adapters/cli/root.py`: `info`, `generate`, `fail`, `config`,
`config-deploy`, `config-generate-examples`, `logdemo`.

### Root Command

**Command:** `hugesitemap`

| Option                         | Description                                     |
|--------------------------------|-------------------------------------------------|
| `--version`                    | Show version and exit                           |
| `--traceback / --no-traceback` | Show full Python traceback on errors            |
| `--profile NAME`               | Load configuration from a named profile         |
| `--set SECTION.KEY=VALUE`      | Override a configuration setting (repeatable)   |
| `--env-file PATH`              | Explicit `.env` file path (skips upward search) |
| `-h, --help`                   | Show help and exit                              |

### info

Print resolved package metadata.

**Exit codes:** 0

### generate

Generate `sitemap.xml` for the configured sites selected by `--site`. Reads the
`[[site]]` entries from the layered configuration, maps each onto a `GenerateRequest`,
and runs the `generate_sitemap` use case with the wired content-source and writer.

| Option                       | Description                                              |
|------------------------------|----------------------------------------------------------|
| `--site NAME[,NAME...]\|all` | Comma-separated site names, or `all` (default)           |
| `--dry-run`                  | Walk and validate but do not write any files             |
| `--gzip`                     | Write gzip-compressed output (overrides config when set) |

**Exit codes:** 0, 1, 13 (permission denied), 22 (no/unknown site), 78 (config error)

### fail

Trigger an intentional failure to test error handling.

**Exit codes:** 1

### config

Display the merged configuration from all sources (defaults -> app -> host -> user -> dotenv -> env).

| Option                   | Description                                        |
|--------------------------|----------------------------------------------------|
| `--format [human\|json]` | Output format (default: human)                     |
| `--section NAME`         | Show only a specific section (e.g. `lib_log_rich`) |
| `--profile NAME`         | Override the profile from the root command         |

**Exit codes:** 0, 22 (section not found)

### config-deploy

Deploy default configuration to system or user directories.

| Option                             | Description                                                               |
|------------------------------------|---------------------------------------------------------------------------|
| `--target [app\|host\|user]`       | Target layer(s) - required, repeatable                                    |
| `--force`                          | Overwrite existing files                                                  |
| `--profile NAME`                   | Deploy to a profile subdirectory                                          |
| `--permissions / --no-permissions` | Set Unix permissions (755/644 app/host, 700/600 user); enabled by default |
| `--dir-mode MODE`                  | Override directory mode (octal, e.g. `750` or `0o750`)                    |
| `--file-mode MODE`                 | Override file mode (octal, e.g. `640` or `0o640`)                         |

**Exit codes:** 0, 1, 13 (permission denied)

### config-generate-examples

Generate example configuration files.

| Option              | Description                 |
|---------------------|-----------------------------|
| `--destination DIR` | Target directory - required |
| `--force`           | Overwrite existing files    |

**Exit codes:** 0, 1

### logdemo

Run a logging demonstration via lib_log_rich's logdemo facility.

| Option         | Description                                 |
|----------------|---------------------------------------------|
| `--theme NAME` | Logging theme to preview (default: classic) |

**Exit codes:** 0

---

## Profile Validation

Profile names (`--profile`) are validated using `lib_layered_config.validate_profile_name()`.

### validate_profile()

**Location:** `adapters/config/loader.py`

```python
def validate_profile(profile: str, max_length: int | None = None) -> None:
    """Validate profile name using lib_layered_config."""
```

| Parameter    | Type          | Default  | Description                                 |
|--------------|---------------|----------|---------------------------------------------|
| `profile`    | `str`         | required | Profile name to validate                    |
| `max_length` | `int \| None` | 64       | Maximum length (DEFAULT_MAX_PROFILE_LENGTH) |

### Validation Rules

| Rule             | Description                                          |
|------------------|------------------------------------------------------|
| Maximum length   | 64 characters (configurable via `max_length`)        |
| Character set    | ASCII alphanumeric, hyphens (`-`), underscores (`_`) |
| Start character  | Must start with an alphanumeric character            |
| Empty string     | Rejected                                             |
| Windows reserved | CON, PRN, AUX, NUL, COM1-9, LPT1-9 rejected          |
| Path traversal   | `/`, `\`, `..` rejected                              |
| Control chars    | Rejected                                             |

### Error Handling

Raises `ValueError` with a descriptive message on invalid input.

---

## Site Configuration

Sites are defined in the layered configuration as an array of tables. `load_sites()`
in `adapters/config/site_loader.py` reads and validates them with Pydantic.

### SiteConfig fields (per `[[site]]`)

| Field              | Description                                          |
|--------------------|------------------------------------------------------|
| `name`             | Unique site identifier used by the `--site` selector |
| `base_url`         | Site base URL (trailing slash recommended)           |
| `output_path`      | Destination path for the generated `sitemap.xml`     |
| `gzip`             | Whether to write gzip-compressed output              |
| `default_priority` | Priority assigned to every walked entry              |
| `directories`      | `[[site.directory]]` blocks (`DirectorySpec`)        |
| `explicit_urls`    | `[[site.url]]` blocks (`ExplicitUrl`)                |
| `filters`          | The `[site.filters]` block (`FilterConfig`)          |

### Global defaults (`[sitemap]` / `SitemapDefaults`)

- **Scalars** (`gzip`, `default_priority`) use override semantics: a site value wins
  when present, otherwise the global default applies.
- **Filters** use extend semantics: the global `[sitemap.filters].ignore` patterns are
  prepended to each site's own `[site.filters].ignore` (global first, then the site's).

---

## Testing Infrastructure

### In-Memory Adapters

The `adapters/memory/` package provides lightweight implementations for testing:

| Module              | What it provides                                                                                                          |
|---------------------|---------------------------------------------------------------------------------------------------------------------------|
| `memory/config.py`  | `get_config_in_memory`, `get_default_config_path_in_memory`, `deploy_configuration_in_memory`, `display_config_in_memory` |
| `memory/sitemap.py` | `InMemoryContentSource`, `content_source_empty`, `SitemapWriterSpy`, `load_sites_in_memory`                               |
| `memory/logging.py` | `init_logging_in_memory` (no-op)                                                                                          |

Use `composition.build_testing()` to wire all in-memory adapters. The `SitemapWriterSpy`
records write calls instead of touching disk; `load_sites_in_memory` delegates to the
real `load_sites` so injected test configs are validated exactly as in production.

### Test Fixtures (conftest.py)

| Fixture                   | Purpose                                                     |
|---------------------------|-------------------------------------------------------------|
| `config_factory`          | Creates real `Config` instances from test data              |
| `source_info_factory`     | Creates `SourceInfo` dicts for provenance-tracking tests    |
| `inject_config`           | Injects a pre-built `Config` by monkeypatching `get_config` |
| `cli_runner`              | Fresh `CliRunner` per test                                  |
| `strip_ansi`              | Strips ANSI escape codes from output                        |
| `clear_config_cache`      | Clears the `get_config` LRU cache before each test          |
| `managed_traceback_state` | Resets/restores traceback configuration                     |

---

**Last Updated:** 2026-06-25 (sitemap generator rewrite)
