"""Sphinx configuration for the OPUS documentation.

The build imports every OPUS module to generate the API reference, and the Django
application's modules cannot be imported until Django is configured. So this file sets
``OPUS_CONFIG`` to the checked-in dummy configuration if the environment does not
already name one, points Django at ``opus_app.settings``, and calls ``django.setup()``
before Sphinx reads anything.

Two local extensions in ``_ext/`` write generated pages into this directory before each
build: ``opus_field_tables`` writes the API guide's metadata-field table, and
``opus_api_reference`` writes the API reference's ``automodule`` pages.
"""

from __future__ import annotations

import os
import sys
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docutils.nodes import Element
    from sphinx.addnodes import pending_xref
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

_DOCS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _DOCS_DIR.parent

# The local extensions, and the source root, so that an editable install is not
# required for autodoc to find the packages.
sys.path.insert(0, str(_DOCS_DIR / '_ext'))
sys.path.insert(0, str(_REPO_ROOT / 'src'))

# OPUS has no default location for its configuration file. A build against a real
# installation can point OPUS_CONFIG at that installation's file; otherwise the
# checked-in dummy configuration the GitHub-hosted CI jobs use serves here too --
# nothing in this build connects to a database or reads PDS holdings.
#
# Sphinx evaluates this file with the working directory set to the directory holding
# it, so a relative OPUS_CONFIG -- which is what both scripts/run-all-checks.sh and
# the CI workflow set, relative to the repository root -- would be looked for under
# docs/ and not found. It is resolved against the repository root here, which is what
# it was relative to when it was set.
_opus_config = os.environ.get('OPUS_CONFIG')
if _opus_config:
    os.environ['OPUS_CONFIG'] = str(_REPO_ROOT / _opus_config)
else:
    os.environ['OPUS_CONFIG'] = str(_REPO_ROOT / 'tests' / 'fixtures' / 'opus_ci.toml')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opus_app.settings')

import django  # noqa: E402  (must follow the environment above)
from django.conf import settings as _django_settings  # noqa: E402

# django.setup() applies opus_app.settings.LOGGING through logging.config.dictConfig,
# and that configuration sets `disable_existing_loggers`. Sphinx creates its own
# loggers before it imports this file, so applying it here would disable them: the
# build would then report no warnings at all and `-W` could never fail, however broken
# the documentation was. Switching Django's logging configuration off for this process
# leaves Sphinx's loggers alone; nothing in a documentation build serves a request or
# has anywhere to log to.
_django_settings.LOGGING_CONFIG = None

django.setup()

# -- Project information ------------------------------------------------------

project = 'rms-opus'
project_copyright = '2026, SETI Institute'
author = 'Robert S. French'
release = distribution_version('rms-opus')
version = release

# -- General configuration ----------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'myst_parser',
    'sphinxcontrib.mermaid',
    'opus_field_tables',
    'opus_api_reference',
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store',
                    # Included into a page rather than being one.
                    'api_guide_fields_table.rst']

# Every cross-reference has to resolve; see nitpick_ignore below for the exceptions
# and why each one cannot be linked.
nitpicky = True

# The README and CONTRIBUTING are included from partway down, after the badge block,
# so the fragment MyST sees starts at the first section rather than at the title --
# which MyST reports as headings starting at H2. The title is there, in the file,
# above the point the include starts from; and the sections have to be H2 for the
# Markdown linter, which objects to a file with several H1s. This is the one warning
# class that is silenced, and this is the whole reason.
suppress_warnings = ['myst.header']

# `|br|` forces a line break inside a table cell, which the generated metadata-field
# table needs to put a field's units under its label.
rst_prolog = """
.. |br| raw:: html

   <br />
"""

# -- Autodoc ------------------------------------------------------------------

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
# Django models and forms carry class attributes whose repr is long and unstable;
# showing the annotation alone keeps the reference readable.
autodoc_typehints_description_target = 'documented_params'
autodoc_default_options = {
    'exclude-members': '__weakref__',
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
# Render an `Attributes:` section as a field list inside the class description rather
# than as separate attribute entries. Several classes describe their attributes that
# way and also have them picked up by `:undoc-members:`, which would otherwise
# describe each attribute twice under one identifier.
napoleon_use_ivar = True

# -- Intersphinx --------------------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'django': ('https://docs.djangoproject.com/en/stable/',
               'https://docs.djangoproject.com/en/stable/_objects/'),
}

# -- Cross-reference repair ---------------------------------------------------

# Names autodoc emits that no inventory carries under that spelling, mapped to the
# spelling that resolves. `_redirect_reference` rewrites each of these before Sphinx
# gives up on it, so they end up as links rather than as silenced warnings.
#
# Django and the standard library document a class under the path it is imported
# from, while autodoc names the module the class is defined in; and the type in a
# docstring's `Returns:` or `Raises:` section is written the way the source imports
# it, which is the bare name.
REFERENCE_ALIASES = {
    'HttpRequest': 'django.http.HttpRequest',
    'django.http.request.HttpRequest': 'django.http.HttpRequest',
    'HttpResponse': 'django.http.HttpResponse',
    'django.http.response.HttpResponse': 'django.http.HttpResponse',
    'Http404': 'django.http.Http404',
    'django.http.response.Http404': 'django.http.Http404',
    'django.db.models.base.Model': 'django.db.models.Model',
    'django.forms.forms.Form': 'django.forms.Form',
    'django.forms.fields.Field': 'django.forms.Field',
    'QuerySet': 'django.db.models.query.QuerySet',
    'Traversable': 'importlib.resources.abc.Traversable',
    'json.decoder.JSONDecodeError': 'json.JSONDecodeError',
}


def _redirect_reference(app: Sphinx, env: BuildEnvironment, node: pending_xref,
                        contnode: Element) -> None:
    """Rewrite a reference target that no inventory carries under that spelling.

    This runs on ``missing-reference`` ahead of intersphinx, rewrites the target in
    place and returns None, leaving the resolution itself to intersphinx and to the
    Python domain.

    Parameters:
        app: The Sphinx application, which this handler does not use.
        env: The build environment, which this handler does not use.
        node: The unresolved reference, whose target is rewritten in place.
        contnode: The node holding the reference's text, which this handler does not
            use.

    Returns:
        None always, so that the handlers after this one see the rewritten target.
    """
    del app, env, contnode
    replacement = REFERENCE_ALIASES.get(node['reftarget'])
    if replacement is not None:
        node['reftarget'] = replacement
    return None


def setup(app: Sphinx) -> None:
    """Register the cross-reference repair handler.

    Parameters:
        app: The Sphinx application being configured.
    """
    # Priority 400 puts this ahead of intersphinx's own missing-reference handler,
    # which runs at the default 500, so a rewritten target is what intersphinx looks
    # for.
    app.connect('missing-reference', _redirect_reference, priority=400)


# -- Nitpick exceptions -------------------------------------------------------

# Only symbols that genuinely have no resolvable target belong here, and each entry
# says why. Where a name has a target under a different spelling it goes in
# REFERENCE_ALIASES above instead, which links it rather than silencing it.
nitpick_ignore = [
    # rms-pdslogger and requests publish no Sphinx inventory, so there is nothing to
    # link either name to.
    ('py:class', 'pdslogger.PdsLogger'),
    ('py:exc', 'requests.RequestException'),
    # A type alias declared inside an `if TYPE_CHECKING:` block. The block does not
    # execute, so autodoc never sees the name and has nothing to describe; the
    # annotations that use it are still checked, which is the point of writing it
    # there.
    ('py:class', 'opus_app.apps.results.views.SearchResultsChunk'),
    ('py:class', 'SearchResultsChunk'),
    # A TypeVar. Sphinx describes the generic function it parameterizes but has no
    # object of its own to point the parameter at.
    ('py:class', 'opus_log_analyzer.opus.html_generator.T'),
]

nitpick_ignore_regex: list[tuple[str, str]] = []

# -- HTML output --------------------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_title = f'rms-opus {release}'
html_static_path: list[str] = []

# -- Mermaid ------------------------------------------------------------------

# Render diagrams in the browser rather than shelling out to a headless browser, so
# the build needs nothing installed beyond the Python dependencies.
mermaid_output_format = 'raw'

# -- MyST ---------------------------------------------------------------------

myst_heading_anchors = 3
