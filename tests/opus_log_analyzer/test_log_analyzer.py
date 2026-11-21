"""Tests for the log analyzer's command-line surface and its field reader.

The analyzer loads the OPUS-specific half of its behavior from a module named on the
command line, so the shipped default has to be a module that resolves from an installed
distribution.
"""

import importlib
import json
from pathlib import Path

import pytest

from opus_log_analyzer.abstract_configuration import AbstractConfiguration
from opus_log_analyzer.log_analyzer import _create_argument_parser
from opus_log_analyzer.opus.slug import ToInfoMap


def test_default_configuration_module_supplies_a_configuration_class() -> None:
    """The default `--configuration` names a packaged module supplying `Configuration`.

    This is the whole contract `main()` relies on: it imports whatever module the option
    names and instantiates that module's `Configuration`. A bare top-level name would be
    resolved against whatever the working directory or the surrounding environment
    happens to offer, which is why the default is an absolute package path.
    """
    module_name = _create_argument_parser().get_default('configuration_file')
    assert module_name == 'opus_log_analyzer.opus.configuration'
    module = importlib.import_module(module_name)
    assert issubclass(module.Configuration, AbstractConfiguration)


@pytest.mark.parametrize('lists_ringobsid', [False, True])
def test_the_field_reader_records_ringobsid_as_opusids_old_slug(
    tmp_path: Path, lists_ringobsid: bool
) -> None:
    """The logs may name ``ringobsid``, so it is read as ``opusid`` whichever the server.

    A server whose definitions still list ``ringobsid`` as a field of its own has that
    entry dropped, so the slug is never taken for a field.
    """
    general = {'opusid': {'label': 'OPUS ID'}, 'planet': {'label': 'Planet'}}
    if lists_ringobsid:
        general['ringobsid'] = {'label': 'RING OBS ID'}
    fields = tmp_path / 'opus' / 'api' / 'fields.json'
    fields.parent.mkdir(parents=True)
    fields.write_text(json.dumps({'data': {'General Constraints': general}}))
    read_json = ToInfoMap._ToInfoMap__read_json  # type: ignore[attr-defined]
    data = read_json(f'file://{tmp_path}/')['data']
    assert set(data) == {'opusid', 'planet'}
    assert data['opusid']['old_slug'] == 'ringobsid'
