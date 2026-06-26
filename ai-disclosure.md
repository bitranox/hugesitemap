# AI disclosure

An honest account of the role AI played in this repository. For the general
position behind it, see [ai-stance.md](ai-stance.md).

## Summary

The maintainer ([bitranox](https://github.com/bitranox)) designed, directed, and
verified this project. An AI coding assistant (Anthropic's Claude, via the Claude
Code CLI) was a tool used to speed up the routine work, always under the
maintainer's direction and review. Every decision, and the final result, are the
maintainer's. The work was done in 2026 and the history is in this repository's
git log.

## What the maintainer drove

- **Set the goal and the approach.** Build a sitemap generator that turns a
  site's content directories into a valid `sitemap.xml` (sitemaps.org 0.9),
  reproducing the behaviour of an earlier directory-walking generator, and able to
  handle very large sites without running out of memory. Build it on the house
  CLI-application skeleton so it shares the project family's standard layout, exit
  handling, layered configuration, and logging, with the sitemap logic carried as
  its own domain and commands.
- **Made the design decisions.** A few calls shape the whole tool. First, stream
  end to end: entries are walked lazily and written one 50,000-URL chunk at a
  time, so peak memory stays flat (measured ~150 MB) whether a site has thousands
  or millions of URLs. Second, configure all sites in one layered config as a
  `[[site]]` array (no per-run config file, no profiles), with an optional global
  `[sitemap]` section whose scalars override per site and whose filter list
  extends each site's own. Third, reproduce the old live output exactly: directory
  and file URLs, real mtime `lastmod`, fixed-precision priority, path filters
  (git `.gitignore` semantics since 2.0.0), a sitemap index above 50,000 URLs, and validated,
  atomically-replaced output. Use libdeflate (via the `deflate` package) for gzip
  (best ratio for a write-once, serve-many file) and lxml with re-parse
  validation.
- **Decided what the tool should and shouldn't do.** Keep the domain pure (no
  I/O, enforced by import-linter), quarantine the untyped lxml and libdeflate
  surfaces behind small typed facades rather than disabling type checks, and keep
  the per-site config as an explicit, validated boundary. Strip the unrelated
  email/greeting scaffolding inherited from the skeleton.
- **Verified it against real runs.** What counts as "correct" here is that a real
  content tree produces a well-formed `sitemap.xml` (re-parsed with lxml) with the
  right URLs, `lastmod`, and priorities, and that memory stays flat as the site
  grows. That was checked by generating against real directory trees and by
  measuring peak RSS up to 5,000,000 URLs (~160 MB), not assumed from the code.
- **Reviewed every change**, and maintains and answers for the result.

## Where AI helped

Under that direction, the assistant did the legwork: drafting the domain (the
sitemap value objects, the gitignore-style path filter, the formatting
and limit helpers), the `GenerateSitemap` use case and its streaming chunker, the
filesystem walker, the lxml writer (tree build, re-parse validation, atomic write,
gzip, sitemap-index split), the typed facades over lxml and libdeflate, and the
`generate` command that plugs into the house CLI skeleton (clean architecture with
domain, application, adapters, and composition layers; rich-click;
`lib_cli_exit_tools` for exit handling; `lib_layered_config`; `lib_log_rich`). It
also wrote the unit tests, doctests, and docs, and carried out the
streaming-memory refactor. The maintainer checked and accepted all of it rather
than taking it on trust.

## What this means for you

Judge it the way you'd judge any other code. The behaviour is documented, the
logic is unit-tested (full suite with doctests and a coverage gate), the type
surface is checked under pyright strict, the layer boundaries are enforced by
import-linter, and the code is scanned by bandit. The memory behaviour is
reproducible: `make test` runs the full suite without touching a live site, and
the README documents the measured footprint. There is a maintainer behind it.
Issues and pull requests are welcome.
