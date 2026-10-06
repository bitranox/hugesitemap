# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format, and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- **Requires lib_layered_config 7.0.1.** An unquoted `.env` value now converts like the
  environment layer, so `..._ENABLED=false` arrives as the boolean `false` rather than the text
  `"false"`. `config-deploy --force` replaces only a file whose content differs and keeps the old
  one as `<name>.bak`; a file that already holds the bundled content is left alone.
- **`click` is a declared dependency.** The package imports it directly (`adapters/cli/main.py`,
  `commands/config.py`) but only had it through rich-click. A new test fails when a runtime
  import is missing from `[project].dependencies`.

### Fixed
- **`[lib_layered_config.default_permissions]` now takes effect, and only the configuration
  files decide it.** The per-layer modes were read, but only `enabled` was ever used, so
  `--set lib_layered_config.default_permissions.user_directory='"0o750"'` still produced a `0o700`
  directory. `config-deploy` now hands its options and any `--set` of the section to
  lib_layered_config, which deploys each target with its configured directory and file mode
  (`--dir-mode`/`--file-mode` still win) and reads the section itself: from the bundled
  defaults, the configuration files the deploy does not overwrite and the environment, never
  from `.env` (nor `--env-file`). So a `.env` in the working directory can neither change a
  deployed mode nor block a deploy, and `config-deploy --force` replaces a deployed file that
  does not parse or holds a bad value without further options. A malformed or out-of-range
  mode, a bare integer (TOML `user_file = 400` is decimal 400, i.e. `0o620`), an unsafe mode, a
  non-boolean `enabled`, a section that is not a table or an unknown key stops the command with
  exit **78** before anything is written: one `Error:` line per problem naming the key and where
  it was set (`(source: override)` for a `--set`), then, for a configured value, a hint that
  both `--dir-mode` and `--file-mode` deploy anyway. `--no-permissions` together with
  `--dir-mode` or `--file-mode` is a usage error (exit **2**). "Deployed configuration" is logged
  after the deploy succeeded rather than announced before it.
- **A configuration that does not load no longer stops every command (exit codes changed).**
  The root group loaded the configuration before any subcommand ran and let a load error
  escape, so a malformed `config.toml`, a `.env` that is not UTF-8 or an unreadable file made
  every command exit 1, `info` and `config-deploy` (the command that replaces the broken file)
  included. The failure is now recorded: `config` and `generate` exit **78** with one `Error:`
  line naming the file (`--traceback` adds the loader's traceback), while `info`,
  `config-deploy`, `config-generate-examples` and `--help` run as usual. Any other exception
  from the loader is a bug and propagates as one.
- **Command-line mistakes are usage errors (exit 2) for every command, checked before
  loading.** An invalid root `--profile` name used to exit **22**, and an invalid
  `config-deploy --profile` name exited **1** as "Failed to deploy configuration"; both now exit
  **2**. Conflicting `--set` values (`--set a.b=1 --set a.b.c=2`) escaped as a TypeError (exit
  **22**), and the other order silently dropped the earlier value; both orders now exit **2**
  naming the two keys. The same key given twice still takes the last value.
- **`config --profile X` keeps the root's `--env-file`.** The reload used to fall back to the
  upward `.env` search.
- **`config-deploy --force` with nothing to write no longer tells you to use `--force`.** Under
  lib_layered_config 7 an empty result with `--force` means every target file is already
  current; the command now says so instead of repeating the hint the user just followed.
- **`build_testing()` can run a command.** The in-memory logging initializer was a no-op while every
  command binds job context onto the lib_log_rich runtime, so any command under the testing
  composition raised `RuntimeError('lib_log_rich.init() must be called before using the logging
  API')`. It now starts a quiet runtime (no journald, event log, Graylog or queue; console at ERROR;
  no `.env` loading). The conftest fixtures that build services use it too, so their stderr no
  longer carries queued INFO lines by timing.
- **Tests no longer pass or fail by order or by machine.** An autouse fixture shuts the lib_log_rich
  runtime down and restores the root logger's handlers, level and propagate flag after every test,
  and another pins rich-click's colour and width globals, so CI (GITHUB_ACTIONS set, 79-column
  Windows runners) renders the same plain output as a developer terminal.
- **No more `SystemExit: N` on stderr.** `generate` and the config commands raised a bare
  `SystemExit`, which `main()`'s catch-all branch printed as `SystemExit: 78` (or 1, 13, 22) after
  the real error message, text a user reads as a crash. They now exit through click's context
  (`ctx.exit`), and `main()` returns the exit code rich_click's `main()` hands back instead of
  discarding it. The exit codes themselves are unchanged. `config-deploy` re-raises a deliberate
  click `Exit` (a `RuntimeError` subclass) ahead of its catch-all, so it keeps its own code instead
  of becoming 1. `typed_click` gains a typed `get_current_context` wrapper.

### Security
- **`config-deploy` refuses unsafe and malformed modes itself, as a usage error (exit code
  changed).** `--dir-mode`/`--file-mode` went through an unbounded octal parser that took
  `-1`, `7777` or a 20-digit value and handed it to the deploy unchecked; the only check was
  whichever one the installed lib_layered_config made, which under 7.x refused it inside the
  deploy as "Failed to deploy configuration" (exit **1**). The
  options now accept only a plain octal literal in `0`..`0o7777`, and refuse the
  setuid/setgid/sticky bits, group and world write, an execute bit on a file, a directory
  without owner `rwx` and a file without owner `rw`, naming each offending bit (exit **2**,
  nothing written). The rule is lib_layered_config's `DeployMode`, the same one it applies to
  configured modes; a zero-padded mode such as `0000750` is accepted as `0o750`.

### Removed
- `adapters.config.permissions` as a whole: `parse_mode` (whose silent fall-back to the default
  was the bug), `get_permission_defaults` and the `PermissionDefaults` model.
  lib_layered_config reads and validates the section now; a caller that wants the settings uses
  its `deploy_permissions_from_config`. The deploy port (`DeployConfiguration`) takes
  `set_permissions: bool | None` (None, the default, follows the configured `enabled`) and
  `permission_overrides`.

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
