# Configuration System

This project uses [`lib_layered_config`](https://github.com/bitranox/lib_layered_config) to manage configuration through a layered merging system. Configuration values are loaded from multiple sources and merged in a defined order, allowing flexible overrides from system-wide defaults down to individual command-line arguments.

There are two distinct configuration concerns, both served by the same layered files:

1. **Application configuration** - logging (`lib_log_rich`) and general behaviour. These are flat sections merged across all layers.
2. **Per-site sitemap configuration** - the sites that `generate` processes. These are declared inside the layered config as an array of tables (`[[site]]`) and validated by pydantic. See [Sitemap Site Configuration](#sitemap-site-configuration) below.

## Key Concepts

- **Layered merging**: Configuration is assembled from multiple files and sources, with later layers overriding earlier ones
- **Cross-platform paths**: Follows XDG conventions on Linux, standard locations on macOS and Windows
- **Profile support**: Named profiles allow environment-specific configurations (e.g., `production`, `staging`, `test`)
- **TOML format**: All configuration files use TOML syntax
- **Runtime overrides**: Values can be overridden via environment variables or CLI flags without modifying files

---

## Configuration Layers

Configuration is loaded and merged in the following order (lowest to highest precedence):

| Priority | Layer        | Description                                     |
|:--------:|--------------|-------------------------------------------------|
| 1        | **defaults** | Bundled with the package (`defaultconfig.toml`) |
| 2        | **app**      | System-wide settings for all machines           |
| 3        | **host**     | Machine-specific overrides                      |
| 4        | **user**     | User's personal settings                        |
| 5        | **.env**     | Project directory dotenv file                   |
| 6        | **env vars** | Environment variables                           |
| 7        | **CLI**      | Command-line `--set` flags (highest priority)   |

**Merge behavior**: Each layer only needs to specify values it wants to override. Unspecified values inherit from lower layers.

**Important - nested tables merge, lists replace.** `lib_layered_config` deep-merges nested tables across layers but replaces lists wholesale (last writer wins). Because the sites are an array of tables (`[[site]]`, a list), a higher layer that defines `site` replaces the whole array from lower layers rather than appending. Keep the entire `[[site]]` array in a single layer. See [Sitemap Site Configuration](#sitemap-site-configuration).

---

## File Locations

### Platform-Specific Paths

| Layer    | Linux                                   | macOS                                                               | Windows                                               |
|----------|-----------------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| defaults | (bundled with package)                  | (bundled with package)                                              | (bundled with package)                                |
| app      | `/etc/xdg/{slug}/config.toml`           | `/Library/Application Support/{vendor}/{app}/config.toml`           | `C:\ProgramData\{vendor}\{app}\config.toml`           |
| host     | `/etc/xdg/{slug}/hosts/{hostname}.toml` | `/Library/Application Support/{vendor}/{app}/hosts/{hostname}.toml` | `C:\ProgramData\{vendor}\{app}\hosts\{hostname}.toml` |
| user     | `~/.config/{slug}/config.toml`          | `~/Library/Application Support/{vendor}/{app}/config.toml`          | `%APPDATA%\{vendor}\{app}\config.toml`                |

### Path Placeholders

| Placeholder  | Linux           | macOS / Windows     |
|--------------|-----------------|---------------------|
| `{slug}`     | `hugesitemap`   | (not used)          |
| `{vendor}`   | (not used)      | `bitranox`          |
| `{app}`      | (not used)      | `Sitemap Generator` |
| `{hostname}` | System hostname | System hostname     |

### Concrete Examples

**Linux:**
- User config: `~/.config/hugesitemap/config.toml`
- App config: `/etc/xdg/hugesitemap/config.toml`
- Host config: `/etc/xdg/hugesitemap/hosts/myserver.toml`

**macOS:**
- User config: `~/Library/Application Support/bitranox/Sitemap Generator/config.toml`

**Windows:**
- User config: `%APPDATA%\bitranox\Sitemap Generator\config.toml`

---

## CLI Commands

### Global Options

These options apply to all commands and must be specified **before** the command name:

| Option                    | Description                                                               |
|---------------------------|---------------------------------------------------------------------------|
| `--version`               | Show version and exit.                                                    |
| `--profile NAME`          | Load configuration from a named profile (e.g., `production`, `test`).     |
| `--set SECTION.KEY=VALUE` | Override a configuration setting. Can be repeated for multiple overrides. |
| `--env-file PATH`         | Explicit `.env` file path. Skips the default upward directory search.     |
| `--traceback`             | Show full Python traceback on errors (useful for debugging).              |
| `--no-traceback`          | Hide traceback, show only error message (default).                        |

**Example usage:**

```bash
# Use a specific profile
hugesitemap --profile production config

# Override settings at runtime (repeatable)
hugesitemap --set lib_log_rich.console_level=DEBUG config
hugesitemap --set sitemap.default_priority=0.7 generate --dry-run

# Load configuration from an explicit .env file
hugesitemap --env-file /etc/myapp/.env config

# Show full traceback for debugging
hugesitemap --traceback config-deploy --target user
```

---

### View Configuration

Display the merged configuration from all sources (defaults -> app -> host -> user -> .env -> env vars).

#### Options Reference

| Option           | Required | Description                                                     |
|------------------|:--------:|-----------------------------------------------------------------|
| `--format`       | No       | Output format: `human` (default) or `json`.                     |
| `--section NAME` | No       | Show only a specific section (e.g., `lib_log_rich`, `sitemap`). |
| `--profile NAME` | No       | Load configuration for a specific profile.                      |

#### Examples

```bash
# Show merged configuration from all sources
hugesitemap config

# Output as JSON (useful for scripting)
hugesitemap config --format json

# Show specific section only
hugesitemap config --section lib_log_rich

# Load configuration for a specific profile
hugesitemap config --profile production

# Combine options
hugesitemap config --profile staging --format json --section sitemap
```

### Deploy Configuration Files

Deploy bundled default configuration to platform-specific directories.

#### Options Reference

| Option             | Required | Description                                                                       |
|--------------------|:--------:|-----------------------------------------------------------------------------------|
| `--target`         | Yes      | Target layer: `app`, `host`, or `user`. Can be specified multiple times.          |
| `--force`          | No       | Overwrite existing configuration files. Without this, existing files are skipped. |
| `--profile NAME`   | No       | Deploy to a profile-specific subdirectory (e.g., `profile/production/`).          |
| `--permissions`    | No       | Enable Unix permission setting (default).                                         |
| `--no-permissions` | No       | Disable permission setting; use system umask instead.                             |
| `--dir-mode MODE`  | No       | Override directory permissions (octal: `750` or `0o750`).                         |
| `--file-mode MODE` | No       | Override file permissions (octal: `640` or `0o640`).                              |

#### Basic Examples

```bash
# Create user configuration file
hugesitemap config-deploy --target user

# Deploy to system-wide location (requires privileges)
sudo hugesitemap config-deploy --target app

# Deploy host-specific configuration
sudo hugesitemap config-deploy --target host

# Deploy to multiple locations at once
hugesitemap config-deploy --target user --target host

# Overwrite existing configuration
hugesitemap config-deploy --target user --force

# Deploy to a specific profile directory
hugesitemap config-deploy --target user --profile production

# Deploy production profile and overwrite if exists
hugesitemap config-deploy --target user --profile production --force
```

The deployed defaults ship with **no sites configured**. After deploying, edit
the target `config.toml` (or add a `config.d` drop-in) to declare your
`[[site]]` entries. Because `app` is usually where shared site definitions live,
deploying to `app` and editing that file is the common workflow.

#### Deploying for Other Users

To deploy user-level configuration for a different user account, use `sudo -u`:

```bash
# Deploy user config for 'serviceaccount' user
sudo -u serviceaccount hugesitemap config-deploy --target user

# Deploy with a specific profile
sudo -u serviceaccount hugesitemap config-deploy --target user --profile production

# The config will be created at that user's home directory:
# /home/serviceaccount/.config/hugesitemap/config.toml
```

**Important notes:**

- Using `sudo` alone (without `-u`) deploys to root's home directory, not the target user's
- Always use `sudo -u <username>` when deploying for service accounts or other users
- Files are created with ownership of the target user (correct behavior)
- File permissions are set according to the `user` layer defaults (`0o700`/`0o600` = private)

**Common deployment scenarios:**

```bash
# System admin deploying app-wide config (all users)
sudo hugesitemap config-deploy --target app

# System admin deploying for a service account
sudo -u myservice hugesitemap config-deploy --target user

# System admin deploying host-specific config
sudo hugesitemap config-deploy --target host

# Regular user deploying their own config (no sudo needed)
hugesitemap config-deploy --target user
```

#### File Permissions (POSIX Only)

On Linux and macOS, `config-deploy` sets Unix file permissions based on the target layer. Windows uses ACLs and ignores these settings.

| Target | Directory Mode      | File Mode           | Description                             |
|--------|:-------------------:|:-------------------:|-----------------------------------------|
| `app`  | `0o755` (rwxr-xr-x) | `0o644` (rw-r--r--) | World-readable for system-wide config   |
| `host` | `0o755` (rwxr-xr-x) | `0o644` (rw-r--r--) | World-readable for host-specific config |
| `user` | `0o700` (rwx------) | `0o600` (rw-------) | Private to user only                    |

**Permission options:**

```bash
# Skip permission setting entirely (use system umask)
hugesitemap config-deploy --target user --no-permissions

# Override directory mode (octal)
hugesitemap config-deploy --target user --dir-mode 750

# Override file mode (octal)
hugesitemap config-deploy --target user --file-mode 640

# Both overrides together
hugesitemap config-deploy --target user --dir-mode 750 --file-mode 640

# Octal formats: both "750" and "0o750" are accepted
hugesitemap config-deploy --target user --dir-mode 0o750
```

**Configurable defaults:**

Permission defaults can be customized in `[lib_layered_config.default_permissions]`:

```toml
[lib_layered_config.default_permissions]
# Values: octal strings ("0o755", "755") or decimal integers (493)
app_directory = "0o755"
app_file = "0o644"
host_directory = "0o755"
host_file = "0o644"
user_directory = "0o700"
user_file = "0o600"

# Set to false to disable permission setting by default
enabled = true
```

### Generate Example Configuration Files

Create example TOML files showing all available options with default values and documentation comments. Useful for learning the configuration structure or creating initial configuration files.

#### Options Reference

| Option              | Required | Description                                                         |
|---------------------|:--------:|---------------------------------------------------------------------|
| `--destination DIR` | Yes      | Directory to write example files.                                   |
| `--force`           | No       | Overwrite existing files. Without this, existing files are skipped. |

#### Examples

```bash
# Generate examples in a specific directory
hugesitemap config-generate-examples --destination ./examples

# Overwrite existing example files
hugesitemap config-generate-examples --destination ./examples --force

# Generate examples in current directory
hugesitemap config-generate-examples --destination .
```

#### Generated Files

| File              | Description                                                  |
|-------------------|--------------------------------------------------------------|
| `config.toml`     | Main configuration file with all sections                    |
| `config.d/*.toml` | Modular configuration files (sites, layered-config, logging) |

Each file contains commented documentation explaining available options and their default values.

### Runtime Overrides

Use `--set` to override configuration values without modifying files. This option:
- Has the **highest precedence** (overrides all other sources including environment variables)
- Can be **repeated** to set multiple values
- Must appear **before** the command name

#### Syntax

```
--set SECTION.KEY=VALUE
--set SECTION.SUBSECTION.KEY=VALUE
```

#### Examples

```bash
# Override a single value
hugesitemap --set lib_log_rich.console_level=DEBUG config

# Override multiple values
hugesitemap --set lib_log_rich.console_level=DEBUG --set lib_log_rich.console_format_preset=short config

# Override a global sitemap default
hugesitemap --set sitemap.default_priority=0.7 generate --dry-run

# Override with JSON arrays/objects (use single quotes around the value)
hugesitemap --set 'sitemap.filters.ignore=["*~", "*.log"]' config

# Combine with profile
hugesitemap --profile production --set lib_log_rich.console_level=DEBUG config
```

Note: `--set` targets scalar keys and nested tables well. The `[[site]]` array is
an array of tables and is best edited in a config file rather than constructed
through `--set`.

#### Supported Value Types

| Type        | Example                                                       |
|-------------|---------------------------------------------------------------|
| String      | `--set section.key=value`                                     |
| Integer     | `--set section.timeout=30`                                    |
| Float       | `--set section.ratio=0.5`                                     |
| Boolean     | `--set section.enabled=true` or `--set section.enabled=false` |
| JSON Array  | `--set section.items='["a", "b"]'`                            |
| JSON Object | `--set section.metadata='{"key": "value"}'`                   |

---

## Sitemap Site Configuration

The sites that `generate` processes are declared in the layered configuration as
an **array of tables** (`[[site]]`), so every site is described in one place and
discovered through `lib_layered_config` (there is no separate `--config` file).
The entries are read and validated with pydantic by `load_sites` in
`adapters/config/site_loader.py`; any problem raises a configuration error with a
message suitable for direct display at the CLI.

The bundled defaults (`defaultconfig.d/30-sites.toml`) ship with **no sites**.
Declare your own by deploying to the application layer (for example
`/etc/xdg/hugesitemap/config.toml`) or a `config.d` drop-in. A ready-to-edit
example lives in `examples/sites.toml`.

### Keep the whole site array in one layer

`lib_layered_config` deep-merges nested tables but replaces lists wholesale (last
writer wins). Because `[[site]]` is a list, a higher layer that defines `site`
**replaces** the array from lower layers rather than appending. Put the entire
`[[site]]` array in a single layer (typically `app`), or higher layers will
silently drop the lower layers' sites.

### Configuration Format

```toml
# Optional global defaults shared by every site.
[sitemap]
gzip             = false
default_priority = 0.5

  [sitemap.filters]
  ignore = ["*~", ".*", "*.txt", "*.log"]   # .gitignore patterns, prepended to each site's filters

[[site]]
name        = "media"                     # unique; used by --site
base_url    = "https://media.example.com/"
output_path = "/srv/www/media/sitemap.xml"
gzip        = false                       # optional; inherits [sitemap].gzip
default_priority = 0.5                     # optional; inherits [sitemap].default_priority

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

### Settings Reference

| Key                                     | Type        | Default  | Description                                                                             |
|-----------------------------------------|-------------|----------|-----------------------------------------------------------------------------------------|
| `[sitemap]`                             | table       | absent   | Global defaults shared by all sites (optional).                                         |
| `[sitemap].gzip`                        | bool        | `false`  | Default `gzip`; a site's own value overrides it.                                        |
| `[sitemap].default_priority`            | float       | `0.5`    | Default priority; a site's own value overrides it.                                      |
| `[sitemap].directory_urls`              | bool        | `true`   | Default for `directory_urls`; a site's own value overrides it.                          |
| `[sitemap.filters].ignore`              | array       | `[]`     | `.gitignore` patterns prepended to every site's own.                                    |
| `[[site]]`                              | table array | `[]`     | One entry per site; `generate` processes all by default.                                |
| `name`                                  | string      | required | Unique site identifier used by `--site`.                                                |
| `base_url`                              | string      | required | Site base URL (trailing slash recommended); used to build child sitemap URLs on split.  |
| `output_path`                           | string      | required | Destination path for the generated `sitemap.xml`.                                       |
| `gzip`                                  | bool        | inherits | Write gzip-compressed output (`sitemap.xml.gz`).                                        |
| `default_priority`                      | float       | inherits | Priority assigned to every walked entry.                                                |
| `directory_urls`                        | bool        | `true`   | Emit directory listing URLs; set `false` for a files-only sitemap.                      |
| `[[site.directory]]`                    | table array | `[]`     | Repeatable: on-disk `path` mapped to `url` (prefix).                                    |
| `[[site.directory]].directory_urls`     | bool        | inherits | Per-directory override of `directory_urls` (else the site / global value).              |
| `[[site.url]]`                          | table array | `[]`     | Repeatable: explicit `loc` with optional `changefreq` and `priority` (default `0.5`).   |
| `[site.filters].keep`                   | array       | `[]`     | Allowlist patterns: index **only** matching files (the `ignore` side then subtracts).   |
| `[site.filters].ignore`                 | array       | `[]`     | Ignore patterns; appended after the global ones.                                        |
| `[site.filters].keep_file`              | string      | absent   | Path to an allowlist rule file (the include-side `ignore_file`).                        |
| `[site.filters].ignore_file`            | string      | absent   | Path to a `.gitignore`-format ignore rule file for this site.                           |
| `[site.filters].nested_keep_filename`   | string      | absent   | Per-directory allowlist filename to discover within each tree (e.g. `.sitemapinclude`). |
| `[site.filters].nested_ignore_filename` | string      | absent   | Per-directory ignore filename to discover within each tree (e.g. `.sitemapignore`).     |

Unknown keys are rejected: each table is validated with `extra="forbid"`, so a
typo in a key name raises a configuration error rather than being ignored.

### Resolution Semantics

The `[sitemap]` section provides global defaults applied to each site, with two
different merge rules:

- **Scalars override.** `gzip` and `default_priority` resolve as: the site's own
  value wins; otherwise the global `[sitemap]` value; otherwise the built-in
  default (`gzip=false`, `default_priority=0.5`).
- **Filters extend (not replace).** The global `[sitemap.filters].ignore`
  patterns are **prepended** to each site's own `[site.filters].ignore` (global
  patterns first, then the site's own). `ignore_file` and
  `nested_ignore_filename` use the site's value, falling back to the global.
  Common junk patterns are written once globally; each site lists only its extras.
  Because matching is last-match-wins, a site can re-include a globally ignored
  path with a `!` negation. The global `keep` allowlist extends the same way -
  but note a global `keep` switches **every** site into allowlist mode, so use it
  only as a deliberate site-wide policy.

### Filters (gitignore semantics)

Filtering uses git `.gitignore` matching via
[`igittigitt`](https://github.com/bitranox/igittigitt). A single tree run through
every option below, with the exact sitemap each config produces, is in
[docs/filtering-examples.md](docs/filtering-examples.md). A filter has two symmetric
sides, each with the same three sources:

| Source              | Include / allowlist side | Ignore / deny side       |
|---------------------|--------------------------|--------------------------|
| inline patterns     | `keep`                   | `ignore`                 |
| rule file           | `keep_file`              | `ignore_file`            |
| per-directory files | `nested_keep_filename`   | `nested_ignore_filename` |

- Patterns are anchored at each `[[site.directory]]` root (a leading `/` anchors,
  no slash matches at any depth, `**` spans directories). A trailing-slash pattern
  (`zsvc/`) matches a directory and prunes its **whole subtree**.
- The include side is **directory-aware**: it keeps the parent directories of a
  match so the walk reaches deep files. `keep = ["*.html"]` indexes only HTML;
  `keep = ["a000/**"]` only that subtree. This is the safe way to "index only X"
  on large or fast-changing trees - a new directory is excluded by default rather
  than silently appearing. (The `!`-inversion `ignore = ["*", "!*/", "!*.html"]`
  still works but is clunkier and can't re-include under an ignored directory.)
- A rule file (`keep_file` / `ignore_file`) is a `.gitignore`-format file (absolute
  path recommended); a missing file raises a configuration error.

#### Precedence - which rule wins

This is **not** one combined "last match wins" list. It is two phases:

1. **Include phase.** If the include side has any source, a path must be kept by it
   to survive; otherwise everything survives this phase.
2. **Ignore phase.** Among survivors, the ignore side drops matches.

A path is indexed **iff the include side keeps it AND the ignore side does not drop
it**, so **the ignore side always wins across the two** (you allowlist broadly, then
carve out exceptions). *Within* each side the three sources are applied
inline -> file -> nested and **later wins** (git's last-matching-rule rule), and a
**deeper** nested file beats a shallower one. So if both a `.sitemapinclude` and a
`.sitemapignore` touch the same path, the path is kept by the include file and then
dropped by the ignore file - **ignore wins**.

#### Per-directory files (`nested_*_filename`)

Setting `nested_ignore_filename = ".sitemapignore"` (and/or
`nested_keep_filename = ".sitemapinclude"`) lets each subdirectory carry its own
rules, exactly like git reads a `.gitignore` in every directory. At startup the
whole tree is scanned once for files of that name; each file's patterns are anchored
at the directory that contains it. This keeps rules next to the content they govern
instead of one giant central list - the reason it scales to large, heterogeneous
trees. The filename is your choice (the `.sitemap*` names are only a convention).

Worked example, with `nested_ignore_filename = ".sitemapignore"`:

```
/srv/www/media/
  a000/
    .sitemapignore     # contains:  *.tmp
    report.pdf         # indexed
    report.tmp         # dropped by a000/.sitemapignore
    old/
      .sitemapignore   # contains:  !report.tmp   (deeper file wins)
      report.tmp       # indexed again here, because the deeper rule re-includes it
  aalg/
    keep.pdf           # indexed (no local rules apply)
```

### Directory URLs (`directory_urls`)

By default the sitemap lists a **directory URL** (trailing `/`) for every directory
the walk visits, plus a **file URL** per surviving file. Set `directory_urls = false`
(per site, globally under `[sitemap]`, or **per `[[site.directory]]`**) to emit **only
file URLs**. The tree is still walked and filtered exactly the same way - only the
directory listing URLs are left out.

Use it when the directory listings are low-value autoindex pages you do not want a
search engine to crawl or index, so the sitemap carries just the real content (e.g.
the files, or with `keep` the files of one type). Explicit `[[site.url]]` entries are
never affected.

It resolves per directory: a `[[site.directory]]` with its own `directory_urls` wins;
otherwise the site value applies; otherwise the global `[sitemap]` value; otherwise
the built-in default (`true`). So one site can keep directory pages for a meaningful
tree and drop them for a noisy one:

```toml
[[site]]
# ...
directory_urls = false        # site default: files-only

  [[site.directory]]          # numeric buckets -> files only (inherits false)
  path = "/srv/www/a000"
  url  = "https://example.com/a000/"

  [[site.directory]]          # real category tree -> keep its listing pages
  path = "/srv/www/catalog"
  url  = "https://example.com/catalog/"
  directory_urls = true
```

### Selecting Sites

`generate` processes every configured site by default. Use `--site` to restrict:

```bash
hugesitemap generate                    # all configured sites (default)
hugesitemap generate --site media,www   # only the named sites (matched by `name`)
hugesitemap generate --site all         # explicit "all"
hugesitemap generate --dry-run          # walk + validate, write nothing
hugesitemap generate --site media --gzip
```

---

## Profiles

Profiles provide isolated configuration namespaces for different environments (e.g., `production`, `staging`, `test`).

### Profile Name Requirements

Profile names are validated for security and cross-platform compatibility (via `lib_layered_config.validate_profile_name`):

| Rule                   | Description                                                                               |
|------------------------|-------------------------------------------------------------------------------------------|
| **Maximum length**     | 64 characters                                                                             |
| **Allowed characters** | ASCII letters (`a-z`, `A-Z`), digits (`0-9`), hyphens (`-`), underscores (`_`)            |
| **Start character**    | Must start with a letter or digit (not `-` or `_`)                                        |
| **Reserved names**     | Windows reserved names rejected: `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9` |
| **Path safety**        | No path separators (`/`, `\`) or traversal sequences (`..`)                               |

**Valid examples:** `production`, `staging-v2`, `test_env`, `dev01`

**Invalid examples:** `../etc` (path traversal), `-invalid` (starts with hyphen), `CON` (Windows reserved)

### Which Layers Are Affected?

| Layer    | Affected by Profile? | Notes                               |
|----------|:--------------------:|-------------------------------------|
| defaults | No                   | Always loaded from package          |
| app      | Yes                  | Uses `profile/<name>/` subdirectory |
| host     | Yes                  | Uses `profile/<name>/` subdirectory |
| user     | Yes                  | Uses `profile/<name>/` subdirectory |
| .env     | No                   | Project directory                   |
| env vars | No                   | Environment                         |
| CLI      | No                   | Command line                        |

### Profile Path Examples

**Without profile:**
- `~/.config/hugesitemap/config.toml`

**With profile `production`:**
- `~/.config/hugesitemap/profile/production/config.toml`

### Reading Behavior

Profile directories are **separate namespaces**. Configuration deployed with a profile is only visible when reading with that same profile.

| Command                       | Sees `app` layer?                  | Sees `user` layer?                 |
|-------------------------------|------------------------------------|------------------------------------|
| `config` (no profile)         | Only if deployed without profile   | Only if deployed without profile   |
| `config --profile production` | Only if deployed with `production` | Only if deployed with `production` |

**Example**: If you deploy `app` with `--profile production` but `user` without a profile:

| Command                       | app layer | user layer |
|-------------------------------|:---------:|:----------:|
| `config`                      | No        | Yes        |
| `config --profile production` | Yes       | No         |

---

## Environment Variables

Configuration can be overridden via environment variables using two methods:

### Method 1: Native lib_log_rich Variables

For logging configuration, use the native `LOG_*` variables (highest precedence):

```bash
LOG_CONSOLE_LEVEL=DEBUG hugesitemap info
LOG_ENABLE_GRAYLOG=true LOG_GRAYLOG_ENDPOINT="logs.example.com:12201" hugesitemap info
```

### Method 2: Application-Prefixed Variables

For any configuration section, use the format: `<PREFIX>___<SECTION>__<KEY>=value`

```bash
HUGESITEMAP___LIB_LOG_RICH__CONSOLE_LEVEL=DEBUG hugesitemap info
HUGESITEMAP___SITEMAP__DEFAULT_PRIORITY=0.7 hugesitemap generate --dry-run
```

**Separator reference:**
- `___` (triple underscore) - separates the application prefix from the section
- `__` (double underscore) - separates the section from the key

---

## .env File Support

Create a `.env` file in your project directory for local development overrides.
In a `.env` file the application prefix is implicit, so use the `SECTION__KEY`
form (double underscore between section and key):

```bash
# .env
LOG_CONSOLE_LEVEL=DEBUG
LOG_CONSOLE_FORMAT_PRESET=short
LOG_ENABLE_GRAYLOG=false
SITEMAP__DEFAULT_PRIORITY=0.7
```

By default, the application searches upward from the current directory to discover `.env` files.

To load a specific `.env` file instead, use `--env-file`:

```bash
# Load from an explicit path (skips upward directory search)
hugesitemap --env-file /opt/myapp/config/.env config
hugesitemap --env-file ./environments/staging.env generate --dry-run
```

The file must exist and be readable; Click validates this before the command runs.

---

## Default Configuration

The `defaultconfig.toml` and the files in `defaultconfig.d/` (bundled with the package) provide baseline values. These serve as the fallback when no external configuration files are deployed.

| File                     | Purpose                                                                  |
|--------------------------|--------------------------------------------------------------------------|
| `30-sites.toml`          | Sitemap site definitions (`[sitemap]` + `[[site]]`); ships with no sites |
| `40-layered-config.toml` | `lib_layered_config` integration and deploy-permission defaults          |
| `90-logging.toml`        | `lib_log_rich` logging defaults                                          |

Because the files in `defaultconfig.d/` are siblings of `defaultconfig.toml`,
`lib_layered_config` discovers and merges them automatically.

---

## Customization Best Practices

**Do NOT modify deployed configuration files directly.** These files may be overwritten during package updates.

Instead, create your own override files in the appropriate layer directory using a high-numbered prefix:

```bash
# User-level customization (Linux)
~/.config/hugesitemap/999-myconfig.toml

# User-level customization (macOS)
~/Library/Application Support/bitranox/Sitemap Generator/999-myconfig.toml

# User-level customization (Windows)
%APPDATA%\bitranox\Sitemap Generator\999-myconfig.toml

# System-wide customization (Linux)
/etc/xdg/hugesitemap/999-myconfig.toml
```

**Why this works:**
- Files in each layer directory are loaded in alphabetical order
- Higher-numbered files (e.g., `999-`) load last and override earlier values
- Your custom file won't be touched by updates that regenerate `config.toml`

**Caveat for site definitions:** the per-layer alphabetical merge applies to
tables, but the `[[site]]` array is a list and is replaced wholesale by the last
writer. Within one layer, only the highest-numbered file that defines `site`
takes effect; it does not concatenate across drop-in files. Keep all `[[site]]`
entries in a single file in a single layer.

**Example `999-myconfig.toml`:**

```toml
# My custom overrides - survives package updates

[lib_log_rich]
console_level = "DEBUG"

[sitemap]
default_priority = 0.7
```

This approach keeps your customizations separate and safe from updates while still benefiting from new default values added in future versions.

---

## Library Use

You can import the configuration system directly in Python:

```python
from hugesitemap.adapters.config.loader import get_config
from hugesitemap.adapters.config.site_loader import load_sites

# Get the merged configuration object
config = get_config()
print(config.as_dict())

# Access specific sections
log_config = config.get("lib_log_rich", default={})

# Read and validate the configured sites
for site in load_sites(config):
    print(site.name, site.base_url, site.output_path)
```
