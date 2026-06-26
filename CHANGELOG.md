# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format, and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- `walk_directory` now skips building the igittigitt parser and the per-path
  `is_ignored` stat when a site configures no filters (`FilterSpec.is_empty`),
  removing parser construction and one `stat` per path for unfiltered sites.

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
