"""Tests for the log analyzer's command-line surface.

The analyzer loads the OPUS-specific half of its behavior from a module named on the
command line, so the shipped default has to be a module that actually resolves from an
installed distribution.
"""

import importlib

from opus_log_analyzer.abstract_configuration import AbstractConfiguration
from opus_log_analyzer.log_analyzer import _create_argument_parser


def test_default_configuration_module_exposes_a_configuration_class() -> None:
    """The default `--configuration` module imports and supplies a `Configuration`.

    This is the whole contract `main()` relies on: it imports whatever module the option
    names and instantiates that module's `Configuration`. The default used to be the bare
    name `opus.configuration`, which resolved only while the analyzer ran from its own
    source directory; nothing would import it from an installed distribution.
    """
    module_name = _create_argument_parser().get_default('configuration_file')
    module = importlib.import_module(module_name)
    assert issubclass(module.Configuration, AbstractConfiguration)


def test_default_configuration_module_is_inside_this_package() -> None:
    """The default names a module of this package, not a bare top-level name.

    A top-level name would be resolved against whatever the working directory or the
    surrounding environment happens to offer, which is the failure this default is
    written to avoid.
    """
    module_name = _create_argument_parser().get_default('configuration_file')
    assert module_name.startswith('opus_log_analyzer.')
