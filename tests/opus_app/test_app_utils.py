"""Tests for the OPUS request helpers that need no database.

`opus_app.apps.tools.app_utils` is where every OPUS API handler goes for the small
decisions that are the same everywhere: what a query parameter means, what a slug's
trailing digit means, what a download is called, and what an error page says. None of
that reads the database, so it belongs in the holdings-free suite the GitHub-hosted CI
runs. The golden-response suite reaches all of it as well, but only as a side effect of
driving whole endpoints, and only on the self-hosted runner with a full import behind
it -- so a regression surfaces there as a wrong response body two layers from its cause.
These tests name the function instead, and run wherever `pytest` does.

What is worth pinning, and why:

* **Reading a query parameter is a rejection, not a conversion.** `get_reqno` answers
  None for everything that is not a non-negative integer, and every handler turns that
  None into a 400. Letting a negative number, a float or a huge value through would
  reach the handlers looking like a real request number.
* **The `__sessionid` override.** It is how a test drives two carts in one process
  (PR-12a's cross-session regression tests depend on it), and it is read ahead of
  Django's own session, so a change of precedence would silently put those tests back
  on one session.
* **The slug-suffix pair.** `strip_numeric_suffix` and `get_numeric_suffix` decide
  which half of a range widget a slug names; they must agree about what a suffix is.
* **What an error message says when there is no request.** The 500 path can be reached
  with no request at all, and the builders have to produce a message rather than raise
  while producing one.
* **The distribution name.** `get_git_version` reads the version of `rms-opus` out of
  the installed metadata; a wrong name there raises on the About page and in every
  cache-busting asset URL.
"""

import csv
import importlib.metadata
import io
import json
import re

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from opus_app.apps.tools.app_utils import (
    cols_to_slug_list,
    csv_response,
    download_filename,
    get_git_version,
    get_mult_name,
    get_numeric_suffix,
    get_reqno,
    get_session_id,
    http404_no_request,
    http404_unknown_opus_id,
    is_old_format_ring_obs_id,
    json_response,
    sort_dictionary,
    strip_numeric_suffix,
    wrap_http500_string,
)


@pytest.fixture
def factory() -> RequestFactory:
    """Return a request factory, which needs no database and no middleware."""
    return RequestFactory()


def _request(factory: RequestFactory, query: str) -> HttpRequest:
    """Build a GET request for a path carrying the given query string.

    Parameters:
        factory: The request factory.
        query: The query string, without its leading question mark.

    Returns:
        The request.
    """
    return factory.get('/api/data.json' + ('?' + query if query else ''))


@pytest.mark.parametrize(('query', 'expected'), [
    ('reqno=0', 0),
    ('reqno=123', 123),
    ('reqno=+7', 7),
    ('reqno=%20456%20', 456),          # int() accepts surrounding whitespace
    # No upper bound, deliberately recorded rather than endorsed: the value is only
    # echoed back in the response, so nothing downstream cares how large it is.
    ('reqno=' + '1' * 400, int('1' * 400)),
])
def test_get_reqno_accepts_a_non_negative_integer(factory: RequestFactory, query: str,
                                                  expected: int) -> None:
    """A request number is any non-negative integer, however it is spelled."""
    assert get_reqno(_request(factory, query)) == expected


@pytest.mark.parametrize('query', [
    '',                       # absent altogether
    'reqno=',                 # present and empty
    'reqno=-1',               # negative
    'reqno=1.5',              # not an integer
    'reqno=1e3',              # not an integer, even though float() would take it
    'reqno=abc',
    'reqno=0x10',
    'reqno=NaN',
])
def test_get_reqno_rejects_everything_else(factory: RequestFactory, query: str) -> None:
    """Anything that is not a non-negative integer is None, which handlers answer 400."""
    assert get_reqno(_request(factory, query)) is None


def test_get_reqno_takes_the_last_of_a_repeated_parameter(
        factory: RequestFactory) -> None:
    """A repeated parameter is Django's last-wins, not a list reaching int()."""
    assert get_reqno(_request(factory, 'reqno=1&reqno=2')) == 2


def test_get_session_id_prefers_the_override(factory: RequestFactory) -> None:
    """`__sessionid` is read ahead of Django's session, which is what tests drive."""
    request = _request(factory, '__sessionid=cross_session_a')
    assert get_session_id(request) == 'cross_session_a'


@pytest.mark.parametrize(('name', 'stripped', 'suffix'), [
    ('J2000_longitude1', 'J2000_longitude', '1'),
    ('J2000_longitude2', 'J2000_longitude', '2'),
    ('J2000_longitude', 'J2000_longitude', None),
    ('time3', 'time3', None),        # only 1 and 2 are range halves
    ('time0', 'time0', None),
    ('', '', None),
])
def test_the_slug_suffix_pair_agree(name: str, stripped: str,
                                    suffix: str | None) -> None:
    """Whatever one of the two calls a suffix, the other must remove exactly that."""
    assert strip_numeric_suffix(name) == stripped
    assert get_numeric_suffix(name) == suffix
    assert stripped + (suffix or '') == name


@pytest.mark.parametrize(('slugs', 'expected'), [
    (None, []),
    ('', []),
    ('opusid', ['opusid']),
    ('opusid,target', ['opusid', 'target']),
    ('opusid,,target', ['opusid', '', 'target']),   # an empty slug is kept, and
                                                    # rejected later by name
    ('opusid,', ['opusid', '']),
])
def test_cols_to_slug_list(slugs: str | None, expected: list[str]) -> None:
    """A `?cols=` value is split on commas, and an absent one is no columns at all."""
    assert cols_to_slug_list(slugs) == expected


def test_get_mult_name() -> None:
    """A field's mult table is its qualified name with the dot turned into `mult_`."""
    assert get_mult_name('obs_general.planet_id') == 'mult_obs_general_planet_id'


@pytest.mark.parametrize(('identifier', 'is_old'), [
    ('S_IMG_CO_ISS_1866145657_N', True),     # underscore in position 1
    ('_IMG_CO_ISS_1866145657_N', True),      # underscore in position 0
    ('co-iss-n1866145657', False),           # a modern opus id
    ('vg-iss-2-s-c4360845', False),
    ('S_', False),                           # too short to be either
    ('', False),
])
def test_is_old_format_ring_obs_id(identifier: str, is_old: bool) -> None:
    """A ringobsid is told from an opusid by an underscore in its first two places."""
    assert is_old_format_ring_obs_id(identifier) is is_old


def test_download_filename_is_safe_for_a_filesystem_and_a_suffix() -> None:
    """The name carries a timestamp but no character that a path or a suffix minds."""
    name = download_filename('co-iss-n1866145657', None)
    assert name.startswith('pdsrms-')
    assert name.endswith('_co-iss-n1866145657')
    assert ':' not in name       # Windows rejects it in a file name
    assert '.' not in name       # would be read as the start of the suffix
    assert '/' not in name


def test_download_filename_without_an_opus_id_names_no_observation() -> None:
    """A whole-cart download is for no single observation, so nothing is appended."""
    assert re.fullmatch(r'pdsrms-[\dT_-]+[a-z]', download_filename(None, None))


def test_download_filename_ends_with_a_varying_letter() -> None:
    """The salt that keeps two downloads in the same second apart really varies.

    Asserting that 200 names are distinct would pass without it, because the
    timestamp carries microseconds; what pins the salt is that the final character
    is not always the same one. With 26 letters and 200 draws, a false failure has
    probability 26**-199.
    """
    finals = {download_filename(None, None)[-1] for _ in range(200)}
    assert len(finals) > 1
    assert finals <= set('abcdefghijklmnopqrstuvwxyz')


def test_sort_dictionary_orders_by_key() -> None:
    """The result is ordered by key, which is what a recorded response compares to."""
    assert list(sort_dictionary({'b': 1, 'a': 2, 'C': 3})) == ['C', 'a', 'b']


def test_sort_dictionary_keeps_every_item() -> None:
    """Reordering must not disturb what each key maps to, or lose one."""
    original = {'b': 1, 'a': 2, 'C': 3}
    assert sort_dictionary(original) == original


def test_json_response_declares_its_type() -> None:
    """A JSON response has to say so, or a browser renders it as text."""
    response = json_response({'reqno': 42, 'data': [1, 2]})
    assert isinstance(response, HttpResponse)
    assert response['Content-Type'] == 'application/json'
    assert json.loads(response.content) == {'reqno': 42, 'data': [1, 2]}


def test_csv_response_is_a_named_attachment() -> None:
    """A CSV download is an attachment whose name the caller chose, plus `.csv`."""
    response = csv_response('pdsrms-data', [[1, 'a'], [2, 'b']],
                            column_names=['n', 'letter'])
    assert response['Content-Type'] == 'text/csv'
    assert response['Content-Disposition'] == 'attachment; filename=pdsrms-data.csv'
    rows = list(csv.reader(io.StringIO(response.content.decode())))
    assert rows == [['n', 'letter'], ['1', 'a'], ['2', 'b']]


@pytest.mark.parametrize('column_names', [None, []])
def test_csv_response_without_column_names_writes_no_header(
        column_names: list[str] | None) -> None:
    """The header row is optional, and no columns is the same as none given.

    A caller that computed an empty column list must not get a blank first line,
    which is why the test is on the value's truth rather than on it being None.
    """
    response = csv_response('pdsrms-data', [[1, 'a']], column_names=column_names)
    rows = list(csv.reader(io.StringIO(response.content.decode())))
    assert rows == [['1', 'a']]


def test_an_error_message_names_the_path_it_was_given(
        factory: RequestFactory) -> None:
    """The builders take a request or a bare path, and say the same thing either way."""
    request = _request(factory, 'opusid=nosuch')
    assert (http404_unknown_opus_id('nosuch', request)
            == http404_unknown_opus_id('nosuch', '/api/data.json'))


def test_an_error_message_names_the_value_that_was_rejected(
        factory: RequestFactory) -> None:
    """A page that says only "not found" leaves the user nothing to correct."""
    message = http404_unknown_opus_id('nosuch', _request(factory, 'opusid=nosuch'))
    assert 'nosuch' in message
    assert '/api/data.json' in message


def test_an_error_message_survives_having_no_request_at_all() -> None:
    """`api_view` reports a request-less call, so the builders may not raise on None."""
    message = http404_no_request(None)
    assert '(no request)' in message


def test_wrap_http500_string_escapes() -> None:
    """The 500 body is raw HTML with no template between it and the browser."""
    wrapped = wrap_http500_string('<script>alert(1)</script>')
    assert '<script>' not in wrapped
    assert '&lt;script&gt;' in wrapped
    assert wrapped.startswith('<div id="info">')


def test_get_git_version_reads_the_installed_distribution() -> None:
    """It reports the version of `rms-opus` itself.

    The distribution name is the part that can go wrong: a typo raises
    `PackageNotFoundError` on the About page and in every cache-busting asset URL.
    """
    assert get_git_version() == importlib.metadata.version('rms-opus')


def test_get_git_version_reports_something_shaped_like_a_version() -> None:
    """The templates append it to a URL, so it has to be a version and not a marker."""
    assert re.match(r'\d+\.\d+', get_git_version()), get_git_version()
