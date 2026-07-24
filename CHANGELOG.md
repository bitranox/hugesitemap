# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format, and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.3.1] 2026-07-24 13:49:42

### Fixed
- CI: resolve latest-ruff violations (PLR0917, PLC0415, RUF002) that turned red on the
  scheduled floating-`ruff` job. `cli_config_deploy` and `_execute_deploy` now take their
  options keyword-only instead of tripping the too-many-positional-arguments check.

### Changed
- Removed the blanket `[tool.ruff.lint].ignore` list (RUF002, RUF022, PLC0415, TC001-3,
  TC006) in favor of fixing each rule at the root: ASCII hyphens instead of en-dashes in
  docstrings, sorted `__all__`, top-level imports where nothing needed deferring (with a
  `# noqa: PLC0415` plus a reason kept only for the two genuine cases - breaking the
  `root`/`commands` circular import, and keeping the in-memory test doubles out of the
  production import path), and the autofixed `TYPE_CHECKING`-only imports for stdlib/
  third-party types and `cast()` expressions.
- Added `[tool.ruff.lint.flake8-type-checking] runtime-evaluated-base-classes =
  ["pydantic.BaseModel"]` so Pydantic model fields stay resolvable at runtime.
- Added `PLC0415` to the `tests/*.py` per-file-ignore list; deferred imports inside a test
  body are a deliberate idiom there and are left untouched.

## [2.3.0] - 2026-06-27

### Added
- `directory_urls` is now overridable **per `[[site.directory]]`**, not just per site.
  A directory's own value wins, else the site value, else the global `[sitemap]`
  value, else the default (`true`). This lets one site keep directory listing URLs
  for a meaningful tree while dropping them for a noisy one (e.g. files-only numeric
  buckets plus a full category tree), without enumerating directory URLs by hand.
  Surfaced as an optional `DirectoryRequest.directory_urls` / `DirectorySpec`
  field (`None` inherits).

## [2.2.0] - 2026-06-27

### Added
- `directory_urls` (per-site, and global `[sitemap].directory_urls`; default `true`):
  set `false` for a **files-only** sitemap. The tree is still walked and filtered the
  same way, but directory listing URLs are not emitted - useful when the directory
  pages are low-value autoindex listings. Explicit `[[site.url]]` entries are
  unaffected. Threaded as `GenerateRequest.directory_urls` and a `directory_urls`
  argument on the `ContentSource` port / `walk_directory`.

### Documentation
- Add `docs/filtering-examples.md`: one tree run through every filter option
  (inline `keep`/`ignore`, `.sitemapignore`, `.sitemapinclude`, the combined
  include+ignore case, and the `directory_urls = false` files-only output) with the
  exact sitemap each config produces. Linked from README and CONFIG.

## [2.1.0] - 2026-06-27

### Added
- Allowlist (include) filtering, symmetric to the ignore side. Each
  `[site.filters]` (and the global `[sitemap.filters]`) now has an include side -
  `keep` (inline), `keep_file`, and `nested_keep_filename` (per-directory files,
  e.g. `.sitemapinclude`) - mirroring `ignore` / `ignore_file` /
  `nested_ignore_filename`. When any include source is set, only paths it keeps are
  indexed and the ignore side then subtracts. Backed by `igittigitt.IncludeParser`,
  so it is directory-aware (keeps the parent directories of a deep match) - the
  recommended way to "index only X", safer than the `!`-inversion for large or
  fast-changing trees. Surfaced on the domain `FilterSpec` as `keep_patterns` /
  `keep_file` / `nested_keep_filename`.

  Precedence: a path is indexed iff the include side keeps it AND the ignore side
  does not drop it (ignore wins across the two); within each side the sources apply
  inline -> file -> nested with later winning, and a deeper nested file beats a
  shallower one. The include side extends globally like the ignore side; a global
  `keep` switches every site into allowlist mode.

  The domain field `nested_filename` was renamed to `nested_ignore_filename` for
  symmetry with the new `nested_keep_filename` (internal API; the TOML config key
  was already `nested_ignore_filename`).

### Changed
- `walk_directory` now skips building the igittigitt parser and the per-path
  `is_ignored` stat when a site configures no filters (`FilterSpec.is_empty`),
  removing parser construction and one `stat` per path for unfiltered sites.

### Documentation
- `examples/sites.toml` now shows `ignore_file` and `nested_ignore_filename` on a
  real site, so all three filter sources have a copyable example (previously only
  inline `ignore` was demonstrated).

## [2.0.1] - 2026-06-27

### Documentation
- Update the remaining living docs that still described the old filter engine to
  the gitignore mechanism (the `ai-disclosure.md` architecture summary and the
  `load_sites` docstring). The dated `docs/plans/` design record and the historical
  1.0.0 changelog entry are left as point-in-time records.

## [2.0.0] - 2026-06-27

Filters now use git `.gitignore` semantics (via `igittigitt`).

### Changed (BREAKING)
- The filter configuration moved from custom drop patterns to `.gitignore`
  syntax. `[sitemap.filters].drop` / `[site.filters].drop` are replaced by
  `[sitemap.filters].ignore` / `[site.filters].ignore`, and the `re:`-prefixed
  regexp form is removed. Convert patterns to gitignore syntax: an anchored
  hidden-dotfile regexp `re:/\.[^/]*` becomes `.*`, a content wildcard
  `*/zsvc/z_content/*` becomes a directory pattern such as `zsvc/z_content/`.
  Global `ignore` patterns are still prepended (extend) to each site's own.
- `GenerateRequest.drop_patterns` (tuple of strings) is replaced by
  `GenerateRequest.filter_spec` (a `FilterSpec`); the `ContentSource` port takes
  `filter_spec` instead of `matchers`. The domain `Matcher`, `compile_filters`,
  and `is_dropped` are removed in favour of the `FilterSpec` value object.

### Added
- `[site.filters].ignore_file`: point a site at a `.gitignore`-format rule file.
- `[site.filters].nested_ignore_filename`: discover per-directory ignore files
  (e.g. `.sitemapignore`) throughout each scanned tree, git-style - scales to
  very large, heterogeneous trees.
- Allowlist filtering via `!` negation (e.g. `["*", "!*/", "!*.html"]` indexes
  only `.html`), and directory-subtree pruning via trailing-slash patterns.

## [1.0.0] - 2026-06-25

Initial public release.

### Added
- `generate` command that scans a site's content directories and writes a valid
  `sitemap.xml` (sitemaps.org 0.9): both directory URLs (trailing slash, the
  directory's own mtime) and file URLs, with real mtime `lastmod`, 4-decimal
  priority, ordered wildcard/regexp drop filters, and a `<sitemapindex>` split
  above 50,000 URLs.
- Streaming generation: entries are walked lazily and written one 50,000-URL
  chunk at a time, so peak memory stays flat (~150 MB) whether a site has
  thousands or millions of URLs.
- Multi-site configuration as a layered `[[site]]` array with an optional global
  `[sitemap]` section (scalars override per site, filter lists extend); `--site`
  selects which sites to generate, all by default.
- Optional gzip output via libdeflate at maximum ratio; lxml-built XML validated
  by re-parsing and written with an atomic rename so the live file is only ever
  replaced by well-formed XML.
- Clean architecture (pure domain, application ports, adapters, composition)
  enforced by import-linter; layered configuration via `lib_layered_config`,
  structured logging via `lib_log_rich`, and a rich-click CLI with POSIX exit
  codes.
- `info`, `config`, `config-deploy`, `config-generate-examples`, and `logdemo`
  helper commands inherited from the CLI skeleton.
