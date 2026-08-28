# rms-opus

| Release | Test Status | Documentation | Coverage |
| ------- | ----------- | ------------- | -------- |
| [![Release](https://img.shields.io/github/v/release/SETI/rms-opus?logo=github)](https://github.com/SETI/rms-opus/releases) [![Release date](https://img.shields.io/github/release-date/SETI/rms-opus)](https://github.com/SETI/rms-opus/releases) | [![Tests](https://img.shields.io/github/actions/workflow/status/SETI/rms-opus/run-tests.yml?branch=main&label=tests)](https://github.com/SETI/rms-opus/actions/workflows/run-tests.yml) [![Integration](https://img.shields.io/github/actions/workflow/status/SETI/rms-opus/run-integration.yml?branch=main&label=integration)](https://github.com/SETI/rms-opus/actions/workflows/run-integration.yml) | [![Documentation](https://img.shields.io/readthedocs/rms-opus/latest?logo=readthedocs)](https://rms-opus.readthedocs.io/en/latest/) | [![Code coverage](https://img.shields.io/codecov/c/github/SETI/rms-opus/main?logo=codecov)](https://codecov.io/gh/SETI/rms-opus) |

| PyPI | Python | Downloads | License |
| ---- | ------ | --------- | ------- |
| [![PyPI version](https://img.shields.io/pypi/v/rms-opus?logo=pypi&logoColor=white)](https://pypi.org/project/rms-opus) | [![Python versions](https://img.shields.io/pypi/pyversions/rms-opus?logo=python&logoColor=white)](https://pypi.org/project/rms-opus) | [![Downloads](https://img.shields.io/pypi/dm/rms-opus)](https://pypi.org/project/rms-opus) | [![License](https://img.shields.io/github/license/SETI/rms-opus)](https://github.com/SETI/rms-opus/blob/main/LICENSE) |

| Issues | Pull requests | Activity |
| ------ | ------------- | -------- |
| [![Open issues](https://img.shields.io/github/issues/SETI/rms-opus)](https://github.com/SETI/rms-opus/issues) [![Closed issues](https://img.shields.io/github/issues-closed/SETI/rms-opus)](https://github.com/SETI/rms-opus/issues?q=is%3Aissue+is%3Aclosed) | [![Open pull requests](https://img.shields.io/github/issues-pr/SETI/rms-opus)](https://github.com/SETI/rms-opus/pulls) [![Closed pull requests](https://img.shields.io/github/issues-pr-closed/SETI/rms-opus)](https://github.com/SETI/rms-opus/pulls?q=is%3Apr+is%3Aclosed) | [![Commit activity](https://img.shields.io/github/commit-activity/m/SETI/rms-opus)](https://github.com/SETI/rms-opus/commits) [![Last commit](https://img.shields.io/github/last-commit/SETI/rms-opus)](https://github.com/SETI/rms-opus/commits) |

<!-- start-after-point -->

## Introduction

OPUS is the Outer Planets Unified Search tool of the Ring-Moon Systems Node of NASA's
Planetary Data System. It lets a researcher search the Node's archive by what an
observation *is* -- when it was taken, what instrument took it, what it was pointed at,
what ring or surface geometry it covers -- and then retrieve the matching data files.
A public instance runs at [opus.pds-rings.seti.org](https://opus.pds-rings.seti.org).

This distribution holds everything that instance is made of: the pipeline that reads
PDS3 volumes and PDS4 bundles and populates the search database, the Django application
that serves the web interface and the public API, and the log analyzer that reports on
how the site is used. It is published so that the Node can deploy it and so that the
software behind a public archive is inspectable, not because OPUS is a library to build
on: the packages carry no API stability guarantees.

## Features

- **Search by metadata, not by file name** -- observation time, target, instrument,
  wavelength, ring and surface geometry, and hundreds of other fields.
- **A public HTTP API** returning JSON, CSV or HTML, documented in the
  [API guide](https://rms-opus.readthedocs.io/en/latest/api_guide.html), with stable
  per-observation identifiers meant to stay valid indefinitely.
- **An import pipeline** that reads PDS3 and PDS4 archives, computes every metadata
  field, and writes the whole database in one piece: nothing a run produces becomes
  visible until the run succeeds.
- **A schema-driven database** -- every table, column, search widget and tooltip comes
  from checked-in JSON, so adding a metadata field is a schema change rather than a
  migration.
- **A cart and bulk download**, building ZIP or TAR archives of the products a search
  selected.
- **A log analyzer** that turns Apache access logs into per-session reports of what
  users actually did.

## Installation

`rms-opus` requires **Python 3.12 or later** and **MySQL 8.0.19 or later** — the
import pipeline writes its multi-row upserts with the row alias that release added.
It also needs the MySQL client development headers, because its MySQL driver has no
Linux wheel and is compiled during the install:

```bash
sudo apt-get install pkg-config default-libmysqlclient-dev build-essential
```

Then:

```bash
pip install rms-opus
```

OPUS reads one TOML configuration file and has **no default location for it**: the
`OPUS_CONFIG` environment variable must name the file in the environment of every OPUS
process. `opus.toml.template` documents every key. It lives in the repository rather
than in the installed package, so copy it out of a checkout, or fetch it -- with `-f`,
so that a failed download stops rather than leaving the error page in the file:

```bash
curl -fsSLO https://raw.githubusercontent.com/SETI/rms-opus/main/opus.toml.template
cp opus.toml.template opus.toml   # then fill in every <PLACEHOLDER>
export OPUS_CONFIG=$PWD/opus.toml
```

Running the import pipeline needs the PDS holdings mounted. `memcached` and its
`pymemcache` client are optional and are not installed by `pip install rms-opus` --
without them OPUS falls back to Django's per-process local-memory cache. The
[deployment guide](https://rms-opus.readthedocs.io/en/latest/dev_guide_deployment.html)
covers both.

## Quick Start

Import a volume into a fresh database:

```bash
export OPUS_CONFIG=/path/to/opus.toml
opus_import --do-it-all COISS_2002
```

Serve the site against it, from a checkout:

```bash
python manage.py migrate     # Django's own tables; OPUS's come from the import
python manage.py runserver   # then open http://127.0.0.1:8000/opus/
```

From a `pip install` there is no `manage.py`; `django-admin` does the same work:

```bash
export DJANGO_SETTINGS_MODULE=opus_app.settings
django-admin migrate
```

Ask the public API how many Cassini ISS observations of Pan there are:

```bash
curl 'https://opus.pds-rings.seti.org/opus/api/meta/result_count.json?target=Pan&instrument=Cassini+ISS'
```

Summarize a day of access logs:

```bash
opus_log_analyzer --batch /var/log/apache2/access_log-2026-08-01
```

Each command has a `--help` describing the rest of its surface.

## Documentation

The full documentation is at
[rms-opus.readthedocs.io](https://rms-opus.readthedocs.io/en/latest/): the
[public web API guide](https://rms-opus.readthedocs.io/en/latest/api_guide.html) for
people querying an OPUS server, and the
[developer guide](https://rms-opus.readthedocs.io/en/latest/dev_guide.html) for people
working on OPUS itself.

To build it locally, install the docs extra and run Sphinx:

```bash
pip install -e ".[docs]"
cd docs && make html
```

## Contributing

See [CONTRIBUTING.md](https://github.com/SETI/rms-opus/blob/main/CONTRIBUTING.md),
and the [code of conduct](https://github.com/SETI/rms-opus/blob/main/docs/code_of_conduct.md)
it points at.

## License

Apache License 2.0. See [LICENSE](https://github.com/SETI/rms-opus/blob/main/LICENSE).

## Supported by BrowserStack

Thanks to BrowserStack for their support of this open-source project.

<a href="https://www.browserstack.com">
  <img src="https://raw.githubusercontent.com/SETI/rms-opus/main/browserstack-logo-600x315.png" alt="BrowserStack" width="250">
</a>
