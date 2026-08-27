"""Tests for the API-reference page generator.

The generator decides what the published API reference contains, and it decides it by
importing things. Two properties matter and neither is visible in the rendered output:
that a package which stops importing stops the build instead of vanishing, and that
every module the walk finds is written onto a page. A reference that silently omits a
subtree looks exactly like one that is complete.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

import opus_api_reference
import pytest

BROKEN = "raise ImportError('deliberately broken')\n"


@pytest.fixture
def package_with_broken_subpackage(tmp_path: Path) -> Iterator[str]:
    """Create an importable package holding a subpackage that raises on import.

    The subpackage is the case that matters: `pkgutil.walk_packages` imports a package
    to recurse into it, and that import is the one it would otherwise swallow.

    Parameters:
        tmp_path: The directory to build the package in.

    Yields:
        The outer package's import name.
    """
    name = 'opus_docs_broken_pkg'
    package = tmp_path / name
    (package / 'broken_sub').mkdir(parents=True)
    (package / '__init__.py').write_text('"""A package for the walk to fail on."""\n')
    (package / 'fine.py').write_text('"""A module that imports."""\n')
    (package / 'broken_sub' / '__init__.py').write_text(
        '"""A subpackage that does not import."""\n' + BROKEN)
    sys.path.insert(0, str(tmp_path))
    try:
        yield name
    finally:
        sys.path.remove(str(tmp_path))
        for module in [key for key in sys.modules if key.startswith(name)]:
            del sys.modules[module]


@pytest.fixture
def package_with_broken_module(tmp_path: Path) -> Iterator[str]:
    """Create an importable package holding a plain module that raises on import.

    Parameters:
        tmp_path: The directory to build the package in.

    Yields:
        The package's import name.
    """
    name = 'opus_docs_broken_mod_pkg'
    package = tmp_path / name
    package.mkdir()
    (package / '__init__.py').write_text('"""A package with one bad module."""\n')
    (package / 'broken.py').write_text('"""A module that does not import."""\n' + BROKEN)
    sys.path.insert(0, str(tmp_path))
    try:
        yield name
    finally:
        sys.path.remove(str(tmp_path))
        for module in [key for key in sys.modules if key.startswith(name)]:
            del sys.modules[module]


def test_a_subpackage_that_cannot_be_imported_stops_the_build(
        package_with_broken_subpackage: str) -> None:
    """The walk raises rather than dropping the subtree it could not import.

    Given no ``onerror``, `pkgutil.walk_packages` catches and ignores the ImportError
    it gets from importing a package, which would leave the reference quietly short of
    a whole subtree while the build still succeeded under ``-W``.
    """
    with pytest.raises(ImportError, match='deliberately broken'):
        opus_api_reference.walk_package(package_with_broken_subpackage)


def test_a_broken_plain_module_is_still_listed(
        package_with_broken_module: str) -> None:
    """A module the walk cannot import is still written onto a page.

    The walk never imports a plain module, so it cannot fail here -- and it must not
    drop one either, because listing it is what gives autodoc the chance to import it
    and fail, which is what ``-W`` turns into a build error.
    """
    grouped = opus_api_reference.walk_package(package_with_broken_module)
    assert f'{package_with_broken_module}.broken' in grouped[package_with_broken_module]


def test_every_walked_module_reaches_a_page() -> None:
    """Nothing the walk finds is dropped between the walk and the rendered pages.

    The grouping and the page rendering are separate steps, and a module that reached
    the first but not the second would be missing from the reference with nothing to
    show for it.
    """
    written = '\n'.join(opus_api_reference.build_pages().values())
    for entry in opus_api_reference.PACKAGES:
        for package_name, modules in opus_api_reference.walk_package(entry.name).items():
            assert f'.. automodule:: {package_name}\n' in written
            for module in modules:
                assert f'.. automodule:: {module}\n' in written


def test_excluded_modules_are_named_on_the_landing_page() -> None:
    """A reader is told what was left out, rather than left to notice the absence.

    Both the count and the names come from `EXCLUDED_MODULES`, so neither can drift
    from what the generator actually excludes. The count is compared against the
    generator's own phrasing rather than a copy of it, so this holds for one excluded
    module as well as for several.
    """
    index = opus_api_reference.render_index_page()
    excluded = opus_api_reference.EXCLUDED_MODULES
    for name, reason in excluded.items():
        assert name in index
        # The reason is rendered wrapped, so compare on its first few words rather
        # than on the whole sentence.
        assert ' '.join(reason.split()[:4]) in ' '.join(index.split())

    # Read the count back out of the rendered page and compare it with the data,
    # rather than with the function that phrased it -- comparing the page against
    # `absent_phrase()` would agree with any wording, including a hardcoded one.
    stated = re.search(r'(\S+) modules? (?:is|are) deliberately absent',
                       ' '.join(index.split()))
    assert stated is not None, 'the page states no count'
    spelled = {'One': 1}.get(stated.group(1))
    assert (spelled or int(stated.group(1))) == len(excluded)


def test_excluded_modules_reach_no_automodule_directive() -> None:
    """An excluded module is named as excluded, never documented."""
    written = '\n'.join(opus_api_reference.build_pages().values())
    for name in opus_api_reference.EXCLUDED_MODULES:
        assert f'.. automodule:: {name}\n' not in written
