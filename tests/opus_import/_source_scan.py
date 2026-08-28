"""The one source traversal the tests that read `src/` as text are allowed to use.

Several tests in this package check the code by parsing it rather than by running it,
which is the only way to reach the definitions no fixture can instantiate. That makes
the traversal itself load-bearing: a scan that sees part of the tree still reports a
clean result, so an incomplete traversal does not fail, it silently under-checks.

Two ways to write one are wrong, neither announces itself, and both read naturally:

- ``glob('*.py')`` skips a subpackage's modules. `obs/` is flat today, so this is
  latent rather than live -- but it is one `mkdir` from being real, and the scan would
  go on passing over the smaller tree.
- ``cls.body`` skips a method defined inside an ``if``. `ObsBase` subclasses do define
  methods conditionally, so this one is a live hazard rather than a latent one.

Both were written here, and both were fixed in one file; the second was then
reintroduced a few hundred lines below the first, in the same file, by a scan
written later. Hence this module: import the traversal instead of writing it, so
the correct one is the only one reachable.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path


def module_files(root: Path) -> list[Path]:
    """Every Python module at or under `root`.

    Args:
        root: Directory to search.

    Returns:
        Paths, sorted, a subpackage's modules included.
    """
    return sorted(root.rglob('*.py'))


def parsed_modules(root: Path) -> Iterator[tuple[Path, ast.Module]]:
    """Parse every module under `root`.

    Args:
        root: Directory to search.

    Yields:
        One ``(path, tree)`` per module, in path order.
    """
    for path in module_files(root):
        yield path, ast.parse(path.read_text(encoding='utf-8'), str(path))


def functions_in(node: ast.AST) -> Iterator[ast.FunctionDef]:
    """Every function defined anywhere inside `node`.

    Args:
        node: Any AST node.

    Yields:
        Each `ast.FunctionDef`, including one nested in a conditional, in a `try`, or
        inside another function. There are no `async def`s in the scanned trees, so
        `ast.AsyncFunctionDef` is deliberately not yielded; add it here, once, if that
        ever stops being true.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.FunctionDef):
            yield child


def classes(tree: ast.Module) -> Iterator[ast.ClassDef]:
    """Every class defined anywhere in a parsed module.

    Args:
        tree: A parsed module.

    Yields:
        Each `ast.ClassDef`, including one defined conditionally.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield node


def _owned_functions(cls: ast.ClassDef) -> Iterator[ast.FunctionDef]:
    """Every function `cls` itself defines, at any depth within its own body."""
    def descend(node: ast.AST) -> Iterator[ast.FunctionDef]:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                # A nested class's methods belong to it, and it gets its own turn from
                # `classes()`. Skipping here is what keeps them from being counted
                # twice and attributed to the wrong class.
                continue
            if isinstance(child, ast.FunctionDef):
                yield child
            yield from descend(child)
    yield from descend(cls)


def class_functions(root: Path) -> Iterator[tuple[Path, ast.ClassDef, ast.FunctionDef]]:
    """Every function defined inside a class, anywhere under `root`.

    Args:
        root: Directory to search.

    Yields:
        One ``(path, cls, fn)`` per definition. Conditionally-defined methods and
        subpackage modules are included; a nested class's methods are attributed to
        that class rather than to its enclosing one.
    """
    for path, tree in parsed_modules(root):
        for cls in classes(tree):
            for fn in _owned_functions(cls):
                yield path, cls, fn
