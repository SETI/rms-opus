# OPUS Modernization — Executive Overview

## Purpose

- **Bring OPUS up to the RMS Node's engineering standards.** OPUS is the Node's flagship
  search tool, but its codebase predates the conventions every other RMS repository now
  follows. This project rebuilds the repository's foundations — packaging, testing,
  documentation, code quality — without changing what users see.
- **Eliminate accumulated risk.** The web framework it runs on has reached end-of-life
  (no more security patches), the data import pipeline — the half of the system that
  builds the OPUS database from the PDS archive — has no automated tests whatsoever,
  what testing does exist depends on a single in-house machine with access to the full
  data archive, and critical institutional knowledge exists only in the code itself.
  Each of these is addressed directly.
- **Make the system installable and operable like a normal software product.** Today,
  deploying OPUS means checking out source code into specific directory locations with
  hand-edited configuration files. Afterward, it installs with one standard command and
  is configured with one settings file.

## Why it's useful

- **Security and longevity**: current, supported versions of Python and Django, with
  known-vulnerable dependencies retired and automatic dependency auditing in place.
- **A test suite for the import pipeline, built from nothing**: the pipeline that reads
  the PDS archive and populates the OPUS database — roughly half the system, and the part
  where a silent error corrupts the data users search — currently has zero automated
  tests. This project builds one, including a miniature stand-in for the archive so the
  full import can be exercised on any machine in minutes.
- **Confidence to change things**: that suite, together with tests for the web
  application, runs on GitHub's own servers with no access to the PDS archive required —
  so every future change is verified before it lands, by anyone, from anywhere. The
  existing full-scale end-to-end test (real archive data through to live API responses)
  is retained as the final safety net.
- **Lower bus factor**: complete developer documentation — architecture, setup,
  deployment, and step-by-step recipes for common tasks like adding a new instrument —
  published on ReadTheDocs, including the public API guide.
- **Faster, safer onboarding of future work**: consistent code style enforced
  automatically, type checking that catches whole classes of bugs before runtime, and a
  codebase where every function is documented.
- **No disruption**: the public API and user experience are preserved. The only
  externally visible changes are two deliberate improvements — the API returns more
  accurate error codes for bad requests, and the API guide moves to a professionally
  rendered documentation site.

## What's going to happen

- All work happens on a **separate long-lived branch**; the production system and `main`
  remain stable and deployable throughout. Nothing goes live until the entire effort is
  complete, tested end-to-end, and rehearsed as a real deployment.
- The work is divided into **24 reviewable pull requests across six phases**, executed
  sequentially by an AI developer working from a fixed, twice-audited specification, with
  a human reviewing and approving every step:
  1. **Foundations** — modern tooling and quality gates are installed; dead code and
     known bugs are removed.
  2. **Restructuring** — the code is reorganized into a standard installable package,
     ending years of fragile path-and-configuration workarounds; configuration
     consolidates into a single settings file.
  3. **Modernization** — the web framework is upgraded to the current long-term-support
     release; inconsistent internal patterns (database access, error handling, logging)
     are unified.
  4. **Type safety and documentation** — the entire codebase gains type annotations and
     documentation, verified mechanically so they can't drift out of date.
  5. **Testing** — the import pipeline's first-ever test suite is written and comes
     online in cloud CI, along with the miniature archive stand-in that makes it possible;
     the existing archive-based integration testing is preserved and folded in.
  6. **Publication** — developer documentation goes live, the package is published, and
     deployment procedures are updated to the new one-command install.
- Every step must pass **both** test systems — the new cloud suite and the existing
  full-scale integration suite — before it can be merged, so correct behavior is
  continuously proven rather than assumed.
- At the end, a **full acceptance test on a clean machine** (install → import data →
  serve the site → verify the API) gates the final merge and first release.
