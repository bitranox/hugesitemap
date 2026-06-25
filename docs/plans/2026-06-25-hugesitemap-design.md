# hugesitemap - Design

Date: 2026-06-25
This document is the validated design for the generator, integrating the
requirements into the clean-architecture CLI template.

## Goal

A modern Python CLI that scans a site's content directories and writes a valid
`sitemap.xml` (sitemaps.org 0.9), reproducing the old live behaviour, built to the template's
clean-architecture + TDD standards. Runs on an internal back-office host and writes via a
network (NFS) mount.

## Scope decisions (locked)

- Strip the demo scaffolding: remove email adapters/commands (`adapters/email`,
  `commands/email`, mail config, `btx_lib_mail`) and the greeting behavior (`build_greeting`,
  `cli_hello`). Keep the layered-config loader, logging setup, and CLI infrastructure.
- Directory URL `<lastmod>` uses the directory entry's own mtime (matches old `sitemap_gen.py`).
- No `Clock` port: sitemap-index child `<lastmod>` is the max child-entry mtime (deterministic,
  testable). Drops a port the spec listed speculatively (YAGNI).

## Configuration (single layered source, multiple sites)

Sites live in the layered application config (`lib_layered_config`) as an array of tables
(`[[site]]`), validated with pydantic. There is no separate `--config` file and no profiles:
all sites are described in one place and discovered through the normal layered locations
(`defaultconfig.d`, `/etc/xdg/hugesitemap/`, `~/.config/...`).

Constraint that shapes this: `lib_layered_config` deep-merges nested mappings but treats lists
as scalars (whole-list, last-writer-wins replacement - confirmed in `application/merge.py`). So
the entire `[[site]]` array must live in one layer (the deployed app config). `generate`
processes every site by default; `--site media,www` (or `--site all`) selects a subset.

### Global `[sitemap]` defaults: scalars override, filters extend (deliberate)

An optional `[sitemap]` table holds defaults shared by every site (`SitemapDefaults`):

- `gzip` and `default_priority` use **override** semantics: a site inherits the global value
  unless it sets its own (a site value always wins). This is the intuitive behaviour for a
  scalar default.
- `[sitemap.filters].drop` uses **extend** semantics: the global drop patterns are **prepended**
  to each site's own `[site.filters].drop` (global first, then site-specific). The result is the
  concatenation, not a replacement.

**Why extend, not replace, for filters (chosen deliberately):** the real sites share a common
base of junk patterns (`*~`, hidden dotfiles, `*.txt*`, `*.log*`, `*.py*`) and each adds only a
few site-specific drops (media: `*/zsvc/z_content/*`; www: `*SAMPLE*`, `*Template*`, ...). With
replace semantics every site would have to repeat the entire common base just to add one pattern,
which is exactly the duplication a shared-defaults section is meant to remove. Extend lets the
common patterns be written once in `[sitemap.filters]` and each site list only its extras.

Trade-off accepted: a site cannot remove an individual global pattern (the global drops always
apply). For shared junk filters that is desirable; if per-site opt-out is ever needed, switch the
filter merge in `site_loader._extend_filters` to replace semantics (scalars are unaffected).
Implemented in `adapters/config/site_loader.py`: `_with_scalar_defaults` (override) and
`_extend_filters` (extend).

## Layers

### domain/ (pure - no I/O, no lxml, no os.walk)

- `model.py` - frozen dataclasses:
  - `SitemapEntry(loc: str, lastmod: datetime | None, priority: float, changefreq: str | None)`
  - `SitemapDocument(entries: tuple[SitemapEntry, ...])` (one `<urlset>` worth)
  - `SitemapIndexEntry(loc, lastmod)` for index children
- `enums.py` - add `ChangeFreq` (always/hourly/daily/weekly/monthly/yearly/never). Keep existing
  `OutputFormat`, `DeployTarget` (used by retained config commands).
- `filters.py` - pure ordered filter engine. `compile_filters(patterns)` returns a list of
  matchers; `is_dropped(relpath, matchers)` returns bool. Supports wildcard (`fnmatch`) and
  `re:`-prefixed regexp, applied in order. Drop-by-default semantics per spec.
- `formatting.py` - pure helpers: `iso8601_z(mtime: float) -> str` (`...T..:..:..Z`),
  `format_priority(value: float) -> str` (4-decimal), `join_url(prefix, relpath) -> str`.
- `limits.py` - `MAX_URLS = 50_000`, `MAX_BYTES = 50 * 1024 * 1024`; `chunk_entries(entries)`
  returns a list of entry-tuples respecting the URL cap (byte cap guarded by writer).
- `errors.py` - keep `ConfigurationError`; add `SitemapValidationError`. Remove `DeliveryError`,
  `InvalidRecipientError` (email-only).

### application/

- `ports.py` - keep config/logging ports. Add:
  - `ContentSource` - `walk(directory: DirectorySpec, matchers) -> Iterable[SitemapEntry]`
  - `SitemapWriter` - `write(documents, output_path, *, gzip) -> list[Path]` (atomic + validate)
  - Remove email ports.
- `generate.py` - `GenerateSitemap` use case. Inputs: `SiteConfig`-derived request. Steps: compile
  filters, walk every configured directory via `ContentSource`, append explicit `[[url]]` entries,
  `chunk_entries`, build documents (single `<urlset>` or index + children), write via
  `SitemapWriter`. Returns `GenerateResult(url_count, paths_written, was_split)`. Pure
  orchestration over ports - no os/lxml imports.

### adapters/

- `config/site_loader.py` - `load_sites(config) -> list[SiteConfig]` reads and validates the
  `[[site]]` array from the merged `Config` (pydantic models: `SiteConfig` with `name`,
  `DirectorySpec(path, url)`, `ExplicitUrl(loc, changefreq, priority)`, `FilterConfig(drop)`).
  Clear errors on malformed/duplicate config (exit non-zero).
- `filesystem.py` - `ContentSource` impl. `os.walk` each directory; emit a directory entry (own
  mtime, trailing `/`) and a file entry per surviving file; apply `is_dropped`; relpath to URL via
  the per-directory prefix; mtime to ISO8601 Z.
- `sitemap_lxml.py` - `SitemapWriter` impl. Builds `<urlset>` (and `<sitemapindex>` when split)
  with lxml, sitemaps.org 0.9 namespace + `xsi:schemaLocation` matching the live header, optional
  gzip, atomic write (temp file, re-parse validation with lxml, `os.replace`).
- `memory/` - in-memory `ContentSource`/`SitemapWriter` fakes for tests. Remove email spy.
- Keep `config/loader.py`, `deploy.py`, `display.py`, `permissions.py`, `overrides.py`,
  `logging/setup.py`.

### composition/

- `AppServices` gains `load_site_config`, `content_source`, `sitemap_writer`, `generate_sitemap`;
  drops all email fields. `build_production` / `build_testing` updated.

### cli/

- New `commands/generate.py`: `hugesitemap generate [--site NAME[,NAME...]|all] [--dry-run]
  [--gzip]`. Reads sites from the layered config; default processes all. Real argv honored (fixes
  gen3's `args=[]` bug). `--dry-run` walks + validates but does not write; prints per-site URL
  count. Config errors give a non-zero exit with a clear message (`ExitCode.CONFIG_ERROR`).
- Remove `cli_hello`, `cli_send_email`, `cli_send_notification` from registration and
  `commands/__init__.py`. Keep `info`, `config*`, `logdemo`, `fail`.

## pyproject changes

- `dependencies`: add `lxml`, `rtoml`; remove `btx_lib_mail`. Keep `pydantic`, `rich-click`,
  `lib_*`, `orjson`. Update `description` + `keywords`.
- import-linter contracts unchanged (domain stays pure; new domain modules import only stdlib).

## Testing (TDD, per layer, >=80% gate)

- domain: filter ordering (wildcard + `re:`); `iso8601_z`; `format_priority`; `join_url` edge
  cases (hypothesis); `chunk_entries` boundary at 50k.
- adapters: `filesystem` against a temp fixture tree (dir + file entries, mtime, dropped paths);
  `sitemap_lxml` (well-formed re-parse, namespace/header, gzip, index split, atomic rename);
  `site_loader` (valid/invalid TOML).
- application: `GenerateSitemap` with in-memory fakes (split vs single, explicit URLs, dry-run).
- cli: `generate` happy path, `--dry-run`, bad config exit codes.
- Remove email/greeting tests.

## Out of scope

systemd unit/timer and `uv tool install` deployment on the internal host (covered separately).
