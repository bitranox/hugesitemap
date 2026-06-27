# hugesitemap

<!-- Badges -->
[![CI](https://github.com/bitranox/hugesitemap/actions/workflows/default_cicd_public.yml/badge.svg)](https://github.com/bitranox/hugesitemap/actions/workflows/default_cicd_public.yml)
[![CodeQL](https://github.com/bitranox/hugesitemap/actions/workflows/codeql.yml/badge.svg)](https://github.com/bitranox/hugesitemap/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open in Codespaces](https://img.shields.io/badge/Codespaces-Open-blue?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/bitranox/hugesitemap?quickstart=1)
[![PyPI](https://img.shields.io/pypi/v/hugesitemap.svg)](https://pypi.org/project/hugesitemap/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/hugesitemap.svg)](https://pypi.org/project/hugesitemap/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-46A3FF?logo=ruff&labelColor=000)](https://docs.astral.sh/ruff/)
[![codecov](https://codecov.io/gh/bitranox/hugesitemap/graph/badge.svg?token=EbL5IdJD9o)](https://codecov.io/gh/bitranox/hugesitemap)
[![Maintainability](https://qlty.sh/badges/041ba2c1-37d6-40bb-85a0-ec5a8a0aca0c/maintainability.svg)](https://qlty.sh/gh/bitranox/projects/hugesitemap)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)


`hugesitemap` scans a site's content directories and writes a valid
`sitemap.xml` (sitemaps.org 0.9 protocol), reproducing the behaviour of an
earlier directory-walking sitemap generator but built to modern clean-architecture standards.

**Built for huge sites.** That is the whole point of the name: entries are
streamed and written one 50,000-URL chunk at a time, so peak memory stays flat
(measured ~150 MB) whether a site has 5,000 or 5,000,000 URLs - the full sitemap
is never held in memory. A nightly run over a multi-million-URL site stays in
the low hundreds of MB on any server; only the output file on disk grows. See
[Memory footprint](#memory-footprint) for the measured numbers.

- Recursive directory walk per configured `[[directory]]`, emitting both
  directory URLs (trailing slash, the directory's own mtime) and file URLs.
- `<lastmod>` from each entry's real mtime in ISO8601 UTC (`...Z`), 4-decimal
  `<priority>`, and explicit `[[url]]` entries with their own changefreq/priority.
- Git `.gitignore`-style filters (via `igittigitt`): anchored patterns, subtree
  pruning, a `keep` allowlist (index only X), rule files, and optional
  per-directory `.sitemapignore` / `.sitemapinclude` files.
- 50,000-URL split into a sitemap index plus numbered child sitemaps.
- Optional gzip output (libdeflate at maximum ratio - smallest standard-gzip
  `.gz` for a write-once, serve-many file); atomic write with lxml re-parse
  validation before the live file is replaced.
- Constant, small memory footprint: entries are streamed and written one
  50,000-URL chunk at a time, so peak RAM stays flat (~150 MB) whether a site
  has 5,000 or 5,000,000 URLs - it never loads the whole sitemap into memory.
- CLI entry point styled with rich-click; layered configuration with
  lib_layered_config; structured logging with lib_log_rich.


### Python 3.10+ Baseline

- The project targets **Python 3.10 and newer**.
- Runtime dependencies require current stable releases (`rich-click>=1.9.6`
  and `lib_cli_exit_tools>=2.2.4`). Dev dependencies (pytest, ruff, pyright,
  bandit, etc.) specify minimum version constraints to ensure compatibility.
- CI workflows exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.10 through 3.14
  alongside the latest available 3.x release provided by Actions.

---

## Install - recommended via uv

[uv](https://docs.astral.sh/uv/) is an ultrafast Python package manager written in Rust (10-20x faster than pip/poetry).

### Install uv (if not already installed) 
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy the actual binaries
cp /root/.local/bin/uv /usr/local/bin/uv
cp /root/.local/bin/uvx /usr/local/bin/uvx

# Ensure world-executable
chmod 755 /usr/local/bin/uv /usr/local/bin/uvx

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### One-shot run (no install needed)

```bash
uvx hugesitemap@latest --help
```

### Persistent install as CLI tool

```bash
# Install latest python
install_latest_python_gcc.sh
# pin uv to the latest python
uv python pin /opt/python-latest/bin/python3
# One-time install, persists from the git repo
uv tool install --python /opt/python-latest/bin/python3 --from "git+https://github.com/bitranox/hugesitemap.git" hugesitemap
# or One-time install, persists from PyPi
uv tool install --python /opt/python-latest/bin/python3 hugesitemap
# Update (requires network)
uv tool upgrade hugesitemap
# Run
hugesitemap --help
```

### Persistent install as CLI tool
```bash
# install the CLI tool (isolated environment, added to PATH)
uv tool install hugesitemap

# upgrade to latest
uv tool upgrade hugesitemap
```

### Install as project dependency

```bash
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
uv pip install hugesitemap
```

For alternative install paths (pip, pipx, source builds, etc.), see
[INSTALL.md](INSTALL.md). All supported methods register the `hugesitemap`
command on your PATH.

---

## Configuration

See [CONFIG.md](CONFIG.md) for detailed documentation on the layered configuration system, including precedence rules, profile support, and customization best practices.

---

## Quick Start

```bash
# Install
uv tool install hugesitemap

# Verify
hugesitemap --version

# deploy config files
hugesitemap deploy-config --target app

# Try it out
hugesitemap generate --dry-run
hugesitemap info
hugesitemap config
```

---

## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.

### Available Commands

```bash
# Display package information
hugesitemap info

# Generate sitemaps for the configured sites
hugesitemap generate                       # all configured sites (default)
hugesitemap generate --site media,www      # only the named sites
hugesitemap generate --dry-run             # walk + validate, write nothing
hugesitemap generate --site media --gzip   # write sitemap.xml.gz

# Error-handling demo
hugesitemap fail
hugesitemap --traceback fail

# Configuration management
hugesitemap config                         # Show current configuration
hugesitemap config --format json           # Show as JSON
hugesitemap config --section lib_log_rich  # Show specific section
hugesitemap config --profile production    # Use a named profile

# Deploy configuration templates to target directories
# Without profile:
hugesitemap config-deploy --target app    # → /etc/xdg/{slug}/config.toml
hugesitemap config-deploy --target host   # → /etc/xdg/{slug}/hosts/{hostname}.toml
hugesitemap config-deploy --target user   # → ~/.config/{slug}/config.toml

# With profile:
hugesitemap config-deploy --target app --profile production   # → /etc/xdg/{slug}/profile/production/config.toml
hugesitemap config-deploy --target host --profile production  # → /etc/xdg/{slug}/profile/production/hosts/{hostname}.toml
hugesitemap config-deploy --target user --profile production  # → ~/.config/{slug}/profile/production/config.toml

# With custom permissions (POSIX only):
hugesitemap config-deploy --target user --file-mode 640       # Files with rw-r----- (640)
hugesitemap config-deploy --target user --dir-mode 750        # Directories with rwxr-x--- (750)
hugesitemap config-deploy --target app --no-permissions       # Skip permission setting (use umask)

# Profile names: alphanumeric, hyphens, underscores; max 64 chars; must start with letter/digit
# See CONFIG.md for full validation rules

# Deploy configuration examples
hugesitemap config-generate-examples --destination ./examples

# Load configuration from an explicit .env file (skips upward directory search)
hugesitemap --env-file /path/to/.env config
hugesitemap --env-file ./environments/production.env generate --dry-run

# Override configuration at runtime (repeatable --set)
hugesitemap --set lib_log_rich.console_level=DEBUG config

# Logging demo
hugesitemap logdemo
hugesitemap --set lib_log_rich.console_level=DEBUG logdemo

# All commands work with any entry point
python -m hugesitemap info
uvx hugesitemap info
```

---

### Generating a Sitemap

Sites are defined in the layered configuration as an array of tables (one
`[[site]]` per site), so all sites live in one place and are discovered through
`lib_layered_config` (no separate config file to pass, no profiles). The
`generate` command processes every configured site by default; `--site` selects
specific ones. A ready-to-edit example lives in [`examples/sites.toml`](examples/sites.toml).

```bash
hugesitemap generate                    # all configured sites (default)
hugesitemap generate --site media,www   # only the named sites
hugesitemap generate --site all         # explicit "all"
hugesitemap generate --dry-run          # walk + validate, write nothing
hugesitemap generate --site media --gzip
```

For each selected site, the walk emits a directory URL (trailing slash, the
directory's own mtime) for every surviving directory and a file URL for every
surviving file. `<lastmod>` is each entry's real mtime in ISO8601 UTC (`...Z`);
`<priority>` is the 4-decimal `default_priority`. When a site exceeds 50,000
URLs the output is split into numbered child sitemaps plus a `<sitemapindex>` at
`output_path`. Each file is validated by re-parsing it with lxml and written via
an atomic rename, so the live file is only ever replaced by well-formed XML.

#### Memory footprint

The generator streams end to end: the directory walk yields entries one at a
time, and they are written one 50,000-URL chunk at a time, so the whole sitemap
is never held in memory. Peak RAM is therefore roughly constant regardless of
how large the site is - dominated by a single chunk, not the total URL count.

Measured peak RSS on a typical machine (realistic ~50-character URLs):

| URLs      | Peak RSS | Output on disk |
|-----------|----------|----------------|
| 50,000    | ~135 MB  | 8 MB           |
| 1,000,000 | ~160 MB  | 154 MB         |
| 5,000,000 | ~160 MB  | 770 MB         |

So even on a big server generating millions of URLs, the process stays in the
low hundreds of MB; only the output file grows. (Naively buffering every entry
would instead cost on the order of 1 GB+ at 5,000,000 URLs.)

#### Configuration Format

Deploy this to the application layer (for example
`/etc/xdg/hugesitemap/config.toml`) or a `config.d` drop-in:

```toml
# Optional global defaults shared by every site.
[sitemap]
gzip             = false
default_priority = 0.5

  [sitemap.filters]
  ignore = ["*~", ".*", "*.txt", "*.log", "*.py"]   # .gitignore patterns, prepended to each site's filters

[[site]]
name        = "media"                     # unique; used by --site
base_url    = "https://media.example.com/"
output_path = "/srv/www/media/sitemap.xml"

  [[site.directory]]                      # repeatable: one on-disk path -> URL prefix
  path = "/srv/www/media/a000"
  url  = "https://media.example.com/a000/"

  [[site.url]]                            # repeatable: explicit extra URLs
  loc        = "https://media.example.com/index.html"
  changefreq = "yearly"
  priority   = 0.1

  [site.filters]                          # appended after the global patterns
  ignore = ["zsvc/"]                      # trailing slash prunes the whole subtree

[[site]]
name        = "www"
base_url    = "https://www.example.com/"
output_path = "/srv/www/www/sitemap.xml"
# ... directories / urls / filters ...
```

The optional `[sitemap]` section holds global defaults. Scalars (`gzip`,
`default_priority`) are inherited unless a site overrides them. Filters
**extend rather than replace**: the global `ignore` patterns are prepended to
each site's own, so common patterns are written once and each site lists only its
extras. Because matching is last-match-wins, a site can re-include a globally
ignored path with a `!` negation.

| Key                                     | Type        | Default  | Description                                                                  |
|-----------------------------------------|-------------|----------|------------------------------------------------------------------------------|
| `[sitemap]`                             | table       | absent   | Global defaults shared by all sites (optional).                              |
| `[sitemap].gzip`                        | bool        | `false`  | Default `gzip`; a site's own value overrides it.                             |
| `[sitemap].default_priority`            | float       | `0.5`    | Default priority; a site's own value overrides it.                           |
| `[sitemap.filters].ignore`              | array       | `[]`     | `.gitignore` patterns prepended to every site's own.                         |
| `[[site]]`                              | table array | `[]`     | One entry per site; `generate` processes all by default.                     |
| `name`                                  | string      | required | Unique site identifier used by `--site`.                                     |
| `base_url`                              | string      | required | Site base URL; used to build child sitemap URLs on split.                    |
| `output_path`                           | string      | required | Destination path for `sitemap.xml`.                                          |
| `gzip`                                  | bool        | inherits | Write gzip-compressed output (`sitemap.xml.gz`).                             |
| `default_priority`                      | float       | inherits | Priority assigned to every walked entry.                                     |
| `[[site.directory]]`                    | table array | `[]`     | `path` (on disk) mapped to `url` (prefix).                                   |
| `[[site.url]]`                          | table array | `[]`     | Explicit `loc` with optional `changefreq`/`priority`.                        |
| `[site.filters].keep`                   | array       | `[]`     | Allowlist patterns: index **only** matching files (`ignore` then subtracts). |
| `[site.filters].ignore`                 | array       | `[]`     | Ignore patterns; appended after the global ones.                             |
| `[site.filters].keep_file`              | string      | absent   | Path to an allowlist rule file (the include-side `ignore_file`).             |
| `[site.filters].ignore_file`            | string      | absent   | Path to a `.gitignore`-format ignore rule file for this site.                |
| `[site.filters].nested_keep_filename`   | string      | absent   | Per-directory allowlist filename to discover (e.g. `.sitemapinclude`).       |
| `[site.filters].nested_ignore_filename` | string      | absent   | Per-directory ignore filename to discover (e.g. `.sitemapignore`).           |

Filtering uses git `.gitignore` semantics (via
[`igittigitt`](https://github.com/bitranox/igittigitt)): patterns are anchored at
each directory root and a trailing-slash pattern (`zsvc/`) prunes a whole subtree.
A filter has two **symmetric sides**, each with inline patterns, a rule file, and
a per-directory nested filename: an **include** side (`keep` / `keep_file` /
`nested_keep_filename`) and an **ignore** side (`ignore` / `ignore_file` /
`nested_ignore_filename`).

**Allowlist (`keep`).** To index **only** certain files, set `keep`: `keep =
["*.html"]` indexes only HTML, `keep = ["a000/**"]` only that subtree. It is
directory-aware (keeps the parent dirs of a match so the walk reaches deep files)
and the safe choice for large or fast-changing trees - a new directory is excluded
by default instead of silently appearing.

**Precedence.** A path is indexed iff the include side keeps it **and** the ignore
side does not drop it - so **ignore wins** across the two. Within each side the
sources apply inline -> file -> nested with **later winning** (git last-match-wins;
a deeper nested file beats a shallower one). Full details and a worked nested-file
example are in [CONFIG.md](CONFIG.md#filters-gitignore-semantics).

> **Keep all sites in one layer.** `lib_layered_config` deep-merges nested
> tables but replaces lists wholesale (last writer wins), so a higher layer
> carrying a `site` array replaces a lower one rather than appending to it.

#### Programmatic Usage

```python
from hugesitemap.adapters.config.loader import get_config
from hugesitemap.adapters.config.site_loader import load_sites
from hugesitemap.adapters.filesystem import walk_directory
from hugesitemap.adapters.sitemap_lxml import write_sitemap
from hugesitemap.application.generate import (
    DirectoryRequest,
    GenerateRequest,
    generate_sitemap,
)
from hugesitemap.domain.filters import FilterSpec
from hugesitemap.domain.model import SitemapEntry

for site in load_sites(get_config()):
    request = GenerateRequest(
        base_url=site.base_url,
        output_path=site.output_path,
        gzip=site.gzip,
        default_priority=site.default_priority,
        directories=tuple(DirectoryRequest(root=d.path, url_prefix=d.url) for d in site.directories),
        explicit_entries=tuple(
            SitemapEntry(loc=u.loc, lastmod=None, priority=u.priority, changefreq=u.changefreq)
            for u in site.explicit_urls
        ),
        filter_spec=FilterSpec(
            patterns=tuple(site.filters.ignore),
            ignore_file=site.filters.ignore_file,
            nested_filename=site.filters.nested_ignore_filename,
        ),
    )
    result = generate_sitemap(request, content_source=walk_directory, write_sitemap=write_sitemap)
    print(site.name, result.url_count, result.paths_written)
```

## Further Documentation

- [Install Guide](INSTALL.md)
- [Development Handbook](DEVELOPMENT.md)
- [Contributor Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Module Reference](docs/systemdesign/module_reference.md)
- [License](LICENSE)

## AI transparency

This project is built with AI-assisted tooling under the maintainer's direction
and review. For the general position, see [ai-stance.md](ai-stance.md); for an
honest account of how AI was used in this specific repository, see
[ai-disclosure.md](ai-disclosure.md).
