"""Write the API reference's ``automodule`` pages by walking the OPUS packages.

The API reference covers every module of every OPUS package, so listing the modules by
hand would mean a list that goes stale the moment a module is added or renamed. This
module walks the packages instead and writes one page per package and subpackage,
holding an ``automodule`` block for the package itself and for each module directly
inside it, before each build. What it walks and what it leaves out are stated in
`PACKAGES` and `EXCLUDED_MODULES`.

`setup` registers this module as a Sphinx extension.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.application import Sphinx


class PackageEntry(NamedTuple):
    """One top-level package in the API reference.

    Attributes:
        name: The package's import name.
        summary: A sentence describing what the package is for, shown on the
            reference's landing page and at the top of the package's own page.
    """

    name: str
    summary: str


#: The packages the API reference covers, in the order its landing page lists them.
PACKAGES = (
    PackageEntry('opus_config',
                 'Loads the TOML configuration file named by ``OPUS_CONFIG`` and hands '
                 'it to the rest of OPUS as frozen dataclasses.'),
    PackageEntry('opus_support',
                 'The unit, time, spacecraft-clock, angle and orbit conversions that '
                 'the import pipeline and the web application both need. It is '
                 'internal to OPUS and carries no API guarantees for anything outside '
                 'this distribution.'),
    PackageEntry('opus_import',
                 'The import pipeline: reads PDS holdings and writes the OPUS '
                 'database.'),
    PackageEntry('opus_app',
                 'The Django project serving the OPUS user interface and the public '
                 'web API.'),
    PackageEntry('opus_log_analyzer',
                 'Turns Apache access logs into reports on how OPUS is being used.'),
)

#: Modules kept out of the reference, each for a reason autodoc cannot work around.
#:
#: autodoc documents a module by importing it, so a module that does work when it is
#: imported does that work during the documentation build.
EXCLUDED_MODULES = frozenset({
    # Calls settings.configure() in its module body, which would configure Django a
    # second time and from a different source than conf.py's django.setup().
    'opus_app.clear_django_cache',
    # Machine-written by scripts/models/create_opus_models.sh: one class per database
    # table plus a nested Meta class each, none of them docstringed and none of them
    # surviving the next regeneration. The tables themselves are described in
    # :doc:`dev_guide_database`, which is where a reader should look.
    'opus_app.apps.search.models',
})

#: The name of the page listing the packages.
INDEX_PAGE = 'api_reference'


def walk_package(package_name: str) -> dict[str, list[str]]:
    """Group one top-level package's modules by the package that holds them.

    Parameters:
        package_name: The package to walk.

    Returns:
        Each package and subpackage name mapped to the modules directly inside it,
        sorted by name, with the members of `EXCLUDED_MODULES` left out. A package
        with no modules of its own still appears, with an empty list.

    Raises:
        ModuleNotFoundError: If the package is not importable, which means the
            documentation is being built without OPUS installed.
    """
    package = importlib.import_module(package_name)
    grouped: dict[str, list[str]] = {package_name: []}
    for info in sorted(pkgutil.walk_packages(package.__path__, f'{package_name}.'),
                       key=lambda info: info.name):
        if info.name in EXCLUDED_MODULES:
            continue
        if info.ispkg:
            grouped.setdefault(info.name, [])
        else:
            grouped.setdefault(info.name.rpartition('.')[0], []).append(info.name)
    return grouped


def _automodule(name: str, is_package: bool = False) -> list[str]:
    """Return the ``automodule`` block for one module.

    A package's ``__init__`` gets ``:ignore-module-all:`` as well. Several of them
    re-export names from the modules underneath, and autodoc documents a name listed
    in ``__all__`` even when it was only imported -- which would describe those names
    twice, once on the package's page and once on the module's, under the same
    identifiers. Ignoring ``__all__`` leaves each name described where it is defined.

    Parameters:
        name: The module's import name.
        is_package: True for a package's ``__init__``.

    Returns:
        The directive and its options, as lines.
    """
    lines = [f'.. automodule:: {name}',
             '   :members:',
             '   :undoc-members:',
             '   :show-inheritance:']
    if is_package:
        lines.append('   :ignore-module-all:')
    lines.append('')
    return lines


def render_package_page(name: str, modules: list[str], subpackages: list[str],
                        summary: str | None = None) -> str:
    """Render the API-reference page for one package.

    Parameters:
        name: The package's import name, which is also the page's title.
        modules: The modules directly inside the package.
        subpackages: The package's immediate subpackages, each of which has a page of
            its own.
        summary: A sentence about the package, for a top-level package.

    Returns:
        The page as reStructuredText.
    """
    lines = ['.. Written by docs/_ext/opus_api_reference.py at build time. Change the',
             '   generator rather than this file.',
             '',
             f'.. _api_{name}:',
             '',
             name,
             '=' * len(name),
             '']
    if summary is not None:
        lines += [summary, '']
    if subpackages:
        lines += ['.. toctree::',
                  '   :maxdepth: 1',
                  '']
        lines += [f'   api_{subpackage}' for subpackage in subpackages]
        lines += ['']
    lines += _automodule(name, is_package=True)
    for module in modules:
        lines += _automodule(module)
    return '\n'.join(lines)


def render_index_page() -> str:
    """Render the API reference's landing page.

    Returns:
        The page as reStructuredText.
    """
    title = 'API Reference'
    lines = ['.. Written by docs/_ext/opus_api_reference.py at build time. Change the',
             '   generator rather than this file.',
             '',
             '.. _api_reference:',
             '',
             title,
             '=' * len(title),
             '',
             'Every module of every OPUS package, generated from the docstrings in',
             'the source. These pages are written before each build by walking the',
             'packages, so a module added to one of them appears here without',
             'anything having to be listed by hand.',
             '']
    for entry in PACKAGES:
        lines += [f':doc:`api_{entry.name}`', f'    {entry.summary}', '']
    lines += ['.. toctree::',
              '   :hidden:',
              '   :maxdepth: 2',
              '']
    lines += [f'   api_{entry.name}' for entry in PACKAGES]
    lines += ['']
    return '\n'.join(lines)


def build_pages() -> dict[str, str]:
    """Render every API-reference page.

    Returns:
        Each page's file stem mapped to its reStructuredText.
    """
    pages = {INDEX_PAGE: render_index_page()}
    for entry in PACKAGES:
        grouped = walk_package(entry.name)
        for package_name, modules in grouped.items():
            subpackages = [candidate for candidate in grouped
                           if candidate.rpartition('.')[0] == package_name]
            pages[f'api_{package_name}'] = render_package_page(
                package_name, modules, sorted(subpackages),
                entry.summary if package_name == entry.name else None)
    return pages


def write_api_reference(source_dir: Path) -> int:
    """Write the API-reference pages into the documentation source tree.

    A page is rewritten only when its content changes, so an unchanged reference does
    not make Sphinx re-read it.

    Parameters:
        source_dir: The documentation source directory to write the pages into.

    Returns:
        The number of pages written, including the landing page.
    """
    pages = build_pages()
    for name, text in pages.items():
        path = source_dir / f'{name}.rst'
        if not path.is_file() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8')
    return len(pages)


def setup(app: Sphinx) -> dict[str, Any]:
    """Register this module as a Sphinx extension.

    Parameters:
        app: The Sphinx application being configured.

    Returns:
        The extension metadata Sphinx expects, declaring the extension safe for both
        the parallel read and the parallel write phase.
    """
    write_api_reference(app.srcdir)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
