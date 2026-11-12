"""A body the database has never held surface geometry for, served with no code changed.

Every body's surface geometry is a row of one table, and its category -- the
``table_names``, ``param_info`` and ``partables`` rows the web application serves it
through -- is written by finalization from the bodies that table holds. So a body new to
the database is served by a web application started after an import and its finalization
have run.

The run renames one body of one observation's surface geometry summary to a body the
fixture has no geometry for (`import_tests.tools.negative_cases.NEW_TARGET_CASE`), then
imports and finalizes that bundle alone. The web application is driven in a subprocess,
``opus_manage shell``, under the run's own configuration: pytest-django configures
Django once per session from the session's configuration, so a client in this process
cannot point at the run's schema.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import TYPE_CHECKING, Any

from import_tests.tools import build_run, fixture_layout, golden_io, negative_cases

if TYPE_CHECKING:
    from import_tests.tools.build_run import ImportRun
    from import_tests.tools.golden_io import DatabaseCredentials

#: The observation whose summary rows the recipe renames, and the body's category.
_OPUS_ID = 'vg-iss-1-s-c3450302'
_CATEGORY = 'obs_surface_geometry__ymir'

#: The requests the subprocess makes: the observation's categories, a search on the new
#: body's field the guide names, and a search on a field the renamed rows hold a value in.
_REQUESTS = {
    'categories': f'/api/categories/{_OPUS_ID}.json',
    'latitude': (
        '/api/data.json?surfacegeometrytargetname=Ymir'
        '&SURFACEGEOymir_planetographiclatitude1=-90&SURFACEGEOymir_planetographiclatitude2=90'
        '&cols=opusid,SURFACEGEOymir_planetographiclatitude1'
    ),
    'sub_solar': (
        '/api/data.json?SURFACEGEOymir_subsolarplanetographiclatitude1=0'
        '&SURFACEGEOymir_subsolarplanetographiclatitude2=20&cols=opusid'
    ),
}

#: What ``opus_manage shell -c`` runs: each request through Django's test client, with the
#: host the test-client rule names, printing each status and body as one JSON object.
_SHELL_PROGRAM = """
import json
from django.conf import settings
from django.test import Client
host = next((name for name in settings.ALLOWED_HOSTS if name != '*'), 'localhost')
client = Client(HTTP_HOST=host)
answers = {}
for key, url in json.loads(REQUESTS).items():
    response = client.get(url)
    answers[key] = [response.status_code, response.content.decode()]
print(json.dumps(answers))
"""


def _serve(run: ImportRun) -> dict[str, Any]:
    """Make `_REQUESTS` of the web application serving the run's schema.

    Parameters:
        run: The finished run, whose configuration names its schema.

    Returns:
        Each request's status and decoded JSON body, keyed as `_REQUESTS` keys it.
    """
    opus_manage = shutil.which('opus_manage', path=str(build_run.THIS_PYTHON.parent))
    assert opus_manage is not None
    program = f'REQUESTS = {json.dumps(json.dumps(_REQUESTS))}\n{_SHELL_PROGRAM}'
    finished = subprocess.run(
        [opus_manage, 'shell', '-c', program],
        cwd=fixture_layout.REPO_ROOT,
        env=build_run.run_environment(run.paths.config_file),
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    answers = json.loads(finished.stdout.strip().splitlines()[-1])
    return {key: (status, json.loads(body)) for key, (status, body) in answers.items()}


def test_the_new_body_has_its_category_rows(
    new_target_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Finalization wrote the body's category, its trigger the body's mult id."""
    rows = golden_io.query(
        db_credentials,
        new_target_run.schema,
        'SELECT `physical_table`, `label` FROM `table_names` WHERE `table_name` = %s',
        [_CATEGORY],
    )
    assert rows == [('obs_surface_geometry_target', 'Ymir Surface Geometry Constraints')]
    body_ids = golden_io.query(
        db_credentials,
        new_target_run.schema,
        'SELECT `m`.`id` FROM `mult` `m` JOIN `mult_field` `f` ON `f`.`field_id` = `m`.`field_id`'
        ' WHERE `f`.`qualified_name` = %s AND `m`.`value` = %s',
        ['obs_surface_geometry_name.target_name', 'YMIR'],
    )
    assert len(body_ids) == 1
    partables = golden_io.query(
        db_credentials,
        new_target_run.schema,
        'SELECT `trigger_val` FROM `partables` WHERE `partable` = %s',
        [_CATEGORY],
    )
    assert partables == [(str(body_ids[0][0]),)]


def test_the_web_application_serves_the_new_body(new_target_run: ImportRun) -> None:
    """The observation lists the body's category, and the body's fields search."""
    recipe = negative_cases.load_recipe(negative_cases.NEW_TARGET_CASE)
    assert recipe.value == 'YMIR'
    answers = _serve(new_target_run)

    status, categories = answers['categories']
    assert status == 200
    assert {'table_name': _CATEGORY, 'label': 'Ymir Surface Geometry Constraints'} in categories

    status, latitude = answers['latitude']
    assert status == 200
    assert 'Ymir' in latitude['columns'][1]

    status, sub_solar = answers['sub_solar']
    assert status == 200
    assert [row[0] for row in sub_solar['page']] == [_OPUS_ID]
