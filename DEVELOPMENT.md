# Development

This handbook covers local development of `hugesitemap`: a Python CLI that
scans a site's content directories and writes a valid `sitemap.xml`
(sitemaps.org 0.9 protocol). The main command is `generate`. For installation
options see [INSTALL.md](INSTALL.md); for the configuration format see
[README.md](README.md) and [CONFIG.md](CONFIG.md).

## Local Setup

The project targets Python 3.10 and newer. [uv](https://docs.astral.sh/uv/) is
the recommended package manager.

```bash
# Create a virtual environment and install the package editable with dev extras
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
uv pip install -e .[dev]
```

Alternatively, with plain pip:

```bash
pip install -e .[dev]
```

The editable install registers the `hugesitemap` console script on your PATH.

## Running the CLI in Development

```bash
# Run via the installed console script
hugesitemap --help
hugesitemap generate --dry-run

# Run the module directly (no install of the console script required, src on path)
python -m hugesitemap generate --dry-run

# Run through make
make run generate --dry-run
```

The `generate` command is the heart of the tool:

```bash
hugesitemap generate                    # all configured sites (default)
hugesitemap generate --site media,www   # only the named sites
hugesitemap generate --site all         # explicit "all"
hugesitemap generate --dry-run          # walk + validate, write nothing
hugesitemap generate --site media --gzip
```

Sites are defined in the layered configuration as an array of tables (one
`[[site]]` per site) with an optional global `[sitemap]` section for shared
defaults. They are discovered through `lib_layered_config`; there is no separate
config file to pass on the command line. See the README for the full
configuration format and a worked example.

Use `--dry-run` freely during development: it performs the full directory walk
and lxml validation but writes nothing to disk.

## Make Targets

All build and automation targets delegate to `uvx bmk@latest`. Trailing
arguments are forwarded automatically (e.g. `make run generate --dry-run`).

| Target                     | Aliases           | Description                                          |
|----------------------------|-------------------|------------------------------------------------------|
| `test`                     | `t`               | Lint, format, type-check, run tests with coverage    |
| `testintegration`          | `testi`, `ti`     | Run integration tests only (external resources)      |
| `codecov`                  | `coverage`, `cov` | Upload coverage report to Codecov                    |
| `build`                    | `bld`             | Build wheel/sdist artifacts                          |
| `clean`                    | `cln`, `cl`       | Remove caches, coverage, and build artifacts         |
| `run`                      |                   | Run the project CLI via uvx (forwards trailing args) |
| `bump-major`               |                   | Increment major version ((X+1).0.0)                  |
| `bump-minor`               |                   | Increment minor version (X.Y.Z -> X.(Y+1).0)         |
| `bump-patch`               |                   | Increment patch version (X.Y.Z -> X.Y.(Z+1))         |
| `bump`                     |                   | Bump patch version (default)                         |
| `commit`                   | `c`               | Create a git commit with a timestamped message       |
| `push`                     | `psh`, `p`        | Run tests, commit, and push to remote                |
| `release`                  | `rel`, `r`        | Tag vX.Y.Z, push, create GitHub release              |
| `dependencies`             | `deps`, `d`       | Check and list project dependencies                  |
| `dependencies-update`      |                   | Update dependencies to latest versions               |
| `config`                   |                   | Show current merged configuration                    |
| `config-deploy`            |                   | Deploy configuration to system/user directories      |
| `config-generate-examples` |                   | Generate example configuration files                 |
| `info`                     |                   | Print resolved package metadata                      |
| `logdemo`                  |                   | Run the logging demonstration                        |
| `version-current`          |                   | Print the current version                            |
| `dev`                      |                   | Editable install (`uv pip install -e .`)             |
| `install`                  |                   | Editable install (no dev extras)                     |
| `help`                     |                   | Show make targets                                    |

## Testing and Linting

`make test` is the single entry point for local CI. It runs the full quality
gate:

- `ruff` lint
- `ruff format` check
- `pyright` (strict mode)
- `bandit` security scan
- `import-linter` (`lint-imports`) architecture contracts
- `pytest` with coverage (including doctests)

```bash
make test          # full quality gate, excludes local_only tests
pytest tests/      # run ALL tests directly (no marker filter)
```

Run `lint-imports` on its own to verify the Clean Architecture layer boundaries
defined in `pyproject.toml` (domain stays pure; dependencies point inward only).

## Integration Tests

Tests that require external resources are marked with
`@pytest.mark.local_only` and excluded from the default `make test` run.

| Command                | What it runs                                   |
|------------------------|------------------------------------------------|
| `make test`            | All tests EXCEPT `local_only` (default for CI) |
| `make testintegration` | ONLY `local_only` integration tests            |
| `pytest tests/`        | ALL tests (no marker filter)                   |

Mark new tests that touch external resources so CI skips them:

```python
@pytest.mark.local_only
@pytest.mark.os_agnostic
def test_real_external_service(...):
    """Integration test requiring an external resource."""
    ...
```

## Project Layout

The package follows Clean Architecture with explicit layer directories under
`src/hugesitemap/`:

```
src/hugesitemap/
├── __init__.py          # Public API
├── __main__.py          # python -m entry point
├── entry.py             # Console script entry point (production wiring)
│
├── domain/              # DOMAIN - pure business logic, no I/O or frameworks
│   ├── model.py         # SitemapEntry and related value objects
│   ├── enums.py         # Type-safe enums
│   ├── errors.py        # Domain exception types
│   ├── filters.py       # FilterSpec value object (gitignore exclusion rules)
│   ├── formatting.py    # lastmod / priority formatting helpers
│   └── limits.py        # 50,000-URL split limits
│
├── application/         # APPLICATION - ports and use cases
│   ├── ports.py         # Callable Protocol definitions
│   └── generate.py      # generate_sitemap use case and request models
│
├── adapters/            # ADAPTERS - infrastructure implementations
│   ├── config/
│   │   └── site_loader.py   # Loads [[site]] / [sitemap] config into models
│   ├── filesystem.py    # Recursive directory walk (content source)
│   ├── sitemap_lxml.py  # Sitemap XML writer with atomic write + re-parse
│   ├── typed_lxml.py    # Typed facade over lxml
│   ├── typed_deflate.py # Typed facade over libdeflate gzip output
│   ├── logging/         # lib_log_rich initialization
│   ├── memory/          # In-memory adapters for testing
│   └── cli/             # CLI adapter (rich-click)
│
└── composition/         # COMPOSITION - dependency wiring
```

Dependencies point inward only: the domain layer never imports from adapters or
composition. The `composition` layer wires adapters to the application ports for
use by the entry points.

## Versioning and Metadata

- The single source of truth for the package version is `pyproject.toml`
  (`[project].version`).
- Runtime metadata is served from static constants in
  `src/hugesitemap/__init__conf__.py`, kept in sync with `pyproject.toml`.
- Do not duplicate the version elsewhere in code. Bump `pyproject.toml`,
  `__init__conf__.py`, and `CHANGELOG.md` (the `make bump` targets automate the
  changelog).
- The console script name defaults to `hugesitemap`.

## Commit and Push Workflow

- Commit after each completed sub-task to avoid losing work across sessions.
- Always run `make test` before pushing so lint, type-check, and tests pass.
- `make push` runs the full test suite, commits, and pushes to the remote.
- Do NOT add Claude as a co-author in commits.

## CI and Publishing

GitHub Actions workflows (under `.github/`, template-managed and off-limits)
handle CI and release:

- The CI workflow runs lint, type-check, tests, and builds wheel/sdist across
  the supported CPython versions and runner images.
- The release workflow publishes to PyPI on `v*.*.*` tags. It uses the
  `PYPI_API_TOKEN` secret when set, otherwise an OIDC Trusted Publisher.

To cut a release:

1. Bump the version (`make bump-patch` / `bump-minor` / `bump-major`) and update
   `CHANGELOG.md`.
2. Tag the commit (`git tag vX.Y.Z && git push --tags`), or use `make release`.
3. The release workflow builds and uploads the wheel/sdist to PyPI.
