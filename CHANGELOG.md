# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format, and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
