"""Tests for the log analyzer's command-line surface.

The analyzer loads the OPUS-specific half of its behavior from a module named on the
command line, so the shipped default has to be a module that resolves from an installed
distribution.
"""

import importlib

from opus_log_analyzer.abstract_configuration import AbstractConfiguration
from opus_log_analyzer.log_analyzer import _create_argument_parser


def test_default_configuration_module_supplies_a_configuration_class() -> None:
    """The default `--configuration` names a module of this package that has `Configuration`.

    This is the whole contract `main()` relies on: it imports whatever module the option
    names and instantiates that module's `Configuration`. A bare top-level name would be
    resolved against whatever the working directory or the surrounding environment
    happens to offer, which is why the default is an absolute package path.
    """
    module_name = _create_argument_parser().get_default('configuration_file')
    assert module_name == 'opus_log_analyzer.opus.configuration'
    module = importlib.import_module(module_name)
    assert issubclass(module.Configuration, AbstractConfiguration)
