"""Entry point for ``python -m opus_import``."""

from opus_import.cli import main

# Re-exported so that `python -m opus_import` and a caller naming
# `opus_import.__main__.main` reach the same function. `no_implicit_reexport`
# makes an import alone private to this module.
__all__ = ['main']

# Re-exported so that `python -m opus_import` and a caller naming
# `opus_import.__main__.main` reach the same function. `no_implicit_reexport`
# makes an import alone private to this module.
__all__ = ['main']

if __name__ == '__main__':
    main()
