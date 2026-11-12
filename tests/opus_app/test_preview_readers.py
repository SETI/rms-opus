"""The page readers' preview images for an observation whose ``obs_preview`` row is missing.

A page LEFT JOINs ``obs_preview``, so such an observation reads NULL, which
`get_search_results_chunk` delivers as its ``NULL_RESULT``; the readers give it the
not-found placeholder, as the Detail page does, rather than failing the page. The search,
the labels and the counts are stood in for, so no database is read; that the real chunk
delivers ``NULL_RESULT`` for a NULL join is pinned against the integration database.
"""

from __future__ import annotations

import inspect
import json
from typing import Any

import pytest
from django.conf import settings
from django.test import RequestFactory

from opus_app.apps.results import views as results_views

#: One page of two observations, the second without an ``obs_preview`` row.
_OPUS_IDS = ['co-iss-n1', 'co-iss-n2']
_VIEWSET = json.dumps(
    {
        'viewables': [
            {
                'url': f'previews/COISS_2xxx/x_{size}.jpg',
                'bytes': 10,
                'width': 1,
                'height': 1,
                'name': size,
            }
            for size in ('thumb', 'small', 'med', 'full')
        ]
    }
)


def _stand_in_search(monkeypatch: pytest.MonkeyPatch, rows: list[tuple[Any, ...]]) -> None:
    """Make the page read return `rows`, with nothing else touching a database."""

    def chunk(*_args: Any, **_kwargs: Any) -> tuple[Any, ...]:
        aux = {'opus_ids': _OPUS_IDS, 'cart_states': ['', '']}
        return (1, None, 100, rows, 'time1,opusid', aux, None)

    monkeypatch.setattr(results_views, 'get_search_results_chunk', chunk)
    monkeypatch.setattr(results_views, 'get_session_id', lambda _request: 'session')
    monkeypatch.setattr(results_views, 'labels_for_slugs', lambda slugs, units=True: slugs)
    monkeypatch.setattr(
        results_views, 'get_result_count_helper', lambda _request, _code: (2, None, None)
    )


def _request(path: str) -> Any:
    """Return a GET request for `path` from the allowed host."""
    host = next((name for name in settings.ALLOWED_HOSTS if name != '*'), 'localhost')
    return RequestFactory().get(path, HTTP_HOST=host)


#: The page's row for the observation without an ``obs_preview`` row, as the chunk gives it.
_MISSING = (_OPUS_IDS[1], results_views.NULL_RESULT)


def test_the_gallery_shows_the_placeholder_for_a_missing_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gallery's page answers, with the placeholder for the observation."""
    _stand_in_search(monkeypatch, [(_OPUS_IDS[0], _VIEWSET), _MISSING])
    handler = inspect.unwrap(results_views.api_get_data_and_images)

    response = handler(_request('/__api/dataimages.json?reqno=1'), api_code=1)

    page = json.loads(response.content)['page']
    assert page[0]['images']['med']['url'].endswith('x_med.jpg')
    assert page[1]['images']['med']['url'] == settings.THUMBNAIL_NOT_FOUND


def test_an_image_call_shows_the_placeholder_for_a_missing_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An image call answers, with the placeholder for the observation."""
    _stand_in_search(monkeypatch, [(_OPUS_IDS[0], _VIEWSET), _MISSING])

    response = results_views._api_get_images(
        _request('/api/images/med.json'), 'json', 1, 'med', False, None
    )

    images = json.loads(response.content)['data']
    assert images[0]['url'].endswith('x_med.jpg')
    assert images[1]['url'] == settings.THUMBNAIL_NOT_FOUND


def test_a_page_reads_the_chunks_null_as_no_preview() -> None:
    """The chunk's stand-in for NULL is no view set."""
    assert results_views.page_preview_json(results_views.NULL_RESULT) is None


def test_a_page_reads_a_view_set_as_its_decoded_json() -> None:
    """A view set's JSON text is decoded."""
    assert results_views.page_preview_json(_VIEWSET) == json.loads(_VIEWSET)
