.. _dev_guide_webapp_extending:

Extending the Web Application
=============================

Five things get added to the web application: an endpoint, a searchable field, a return
format, an app, and a front-end area. The import pipeline's extension points are in
:ref:`dev_guide_import_extending`.

**Two rules apply to all of them.** A public URL that worked before has to keep working
(:ref:`dev_guide_conventions`), and the golden-response suite in
``integration_tests/test_api/`` is what proves a change did not alter what OPUS answers.

.. _dev_guide_webapp_extending_endpoint:

Adding an API endpoint
----------------------

1. **Write the handler** in the app that owns the data, and decorate it with
   :func:`~opus_app.apps.tools.app_utils.api_view` -- and with ``@never_cache`` unless
   the answer is genuinely stable for a URL. The decorator is what makes an exception
   into a status code; a handler outside it returns Django's default 500 page and
   records nothing.
2. **Declare an ``api_code`` parameter** only if the handler passes it on to the search
   helpers. The wrapper inspects the signature once, at decoration time, and supplies one
   only when it is declared.
3. **Route it** in the app's own ``urls.py``. Nothing else needs editing:
   :mod:`opus_app.urls` includes every app's routes and mounts the whole set at both
   prefixes.
4. **Decide which API it is.** A name beginning ``__`` is private, carries no
   compatibility promise, and by convention requires and echoes a ``reqno``. Anything
   else is public and is documented in :ref:`api_guide`.
5. **Raise, do not return, an error.** Use
   :exc:`~opus_app.apps.tools.app_utils.Http400Error` for a malformed request and
   :exc:`django.http.Http404` for something that does not exist, and **take the message
   from** :mod:`opus_app.apps.tools.app_utils` rather than writing one at the raise site.
   Add a new message function there if none fits.
6. **Add a golden-response test.**

.. code-block:: python

    from django.http import HttpRequest, HttpResponse
    from django.views.decorators.cache import never_cache

    from opus_app.apps.results.views import get_search_results_chunk
    from opus_app.apps.tools.app_utils import (
        Http400Error,
        api_view,
        get_reqno,
        http400_bad_or_missing_reqno,
        json_response,
    )


    @never_cache
    @api_view
    def api_my_endpoint(request: HttpRequest) -> HttpResponse:
        """One line saying what this returns.

        This is a PRIVATE API.

        ::

            Format: __api/myendpoint.json
            Arguments: reqno=<N>

        Parameters:
            request: The HTTP request, whose query string carries ``reqno``.

        Returns:
            The answer as JSON, with ``reqno`` echoed back.

        Raises:
            Http400Error: If ``reqno`` is missing or malformed.
        """
        reqno = get_reqno(request)
        if reqno is None:
            raise Http400Error(http400_bad_or_missing_reqno(request))
        return json_response({'answer': ..., 'reqno': reqno})

Declare ``api_code`` only where the handler passes it on -- as
:func:`~opus_app.apps.results.views.api_get_data` does, to
:func:`~opus_app.apps.results.views.get_search_results_chunk`. The skeleton above does
not, so it does not declare one:

.. code-block:: python

    @never_cache
    @api_view
    def api_my_searching_endpoint(request: HttpRequest, *, api_code: int) -> HttpResponse:
        """One line saying what this returns.

        Parameters:
            request: The HTTP request, whose query string carries the search.
            api_code: The API call number, supplied by the decorator and passed on so
                that the search helpers log against it.

        Returns:
            The answer as JSON.
        """
        chunk = get_search_results_chunk(request, cols='opusid', api_code=api_code)
        ...

.. code-block:: python

    # In the app's urls.py
    urlpatterns = [
        re_path(r'^__api/myendpoint.json$', api_my_endpoint),
    ]

Querying from an endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~

If the endpoint reads a search, do **not** parse the query string yourself. Call
:func:`~opus_app.apps.search.views.url_to_search_params` and then either
:func:`~opus_app.apps.search.views.get_user_query_table`, for a cache table to join
against, or :func:`~opus_app.apps.results.views.get_search_results_chunk`, for a page of
rows already formatted. Both handle the paging, the units, the null rendering and the
cache-table race that a hand-written query would have to repeat.

If the endpoint needs SQL of its own, build it with
:mod:`opus_app.apps.tools.sql_builder` and never by concatenation.
:ref:`dev_guide_webapp_tools_sql_builder` says what that module guarantees and why; the
short version is that identifiers are validated before they are quoted, and every value
is a bound parameter.

.. _dev_guide_webapp_extending_field:

Adding a searchable or displayable field
----------------------------------------

**There is nothing to do in the web application.** A field exists because the import
pipeline wrote a ``param_info`` row for it, and everything downstream -- the menu, the
widget, the metadata selector, the results columns, the field dictionary -- is generated
from that row.

The recipe is :ref:`dev_guide_extending_column`. Three things have to happen on the web
side afterwards, and all three are operational rather than code:

1. **Regenerate the models** if the column is in a new table:
   ``scripts/models/create_opus_models.sh``.
2. **Restart the workers and clear the shared cache**, for the reasons
   :ref:`dev_guide_deployment_after_import` gives.

.. _dev_guide_webapp_extending_format:

Adding a return format
----------------------

A handler's formats are the alternatives in its route's regular expression, and the
branch at the bottom of the handler that renders each. To add one:

1. Add it to the route's pattern.
2. Add the branch, using :func:`~opus_app.apps.tools.app_utils.json_response`,
   :func:`~opus_app.apps.tools.app_utils.csv_response` or a template.
3. Leave the final ``else`` raising
   :func:`~opus_app.apps.tools.app_utils.http404_unknown_format`, so that a format the
   route somehow admits and the handler does not produce is a 404 rather than a crash.

An **archive** format is different: those come from the ``DOWNLOAD_FORMATS`` setting,
which maps a format name to its MIME type and the two modes the archive library is opened
in. Adding one is an entry there plus the corresponding library call in
:func:`~opus_app.apps.cart.views.api_create_download`.

.. _dev_guide_webapp_extending_app:

Adding an app
-------------

Rarely the right answer -- most new work belongs in one of the eight apps that exist --
but the steps are:

1. Create ``src/opus_app/apps/<name>/`` with an ``__init__.py`` carrying a one-line
   docstring, a ``views.py`` and a ``urls.py``. **No** ``apps.py`` **and no**
   :class:`~django.apps.AppConfig` subclass: none of the OPUS apps defines one, and
   Django's default is what they all use.
2. Add the dotted path to ``INSTALLED_APPS`` in :mod:`opus_app.settings`. Django derives
   the app label from the path's last component, so an app under ``apps/foo/`` has the
   label ``foo``.
3. Add an ``include`` of its ``urls`` to the list in :mod:`opus_app.urls`, so that its
   routes are mounted at both prefixes.
4. **Add a logger entry** to the ``LOGGING`` settings. The key must be a prefix of the
   modules' real names -- they call ``logging.getLogger(__name__)`` -- and a key that
   prefixes no real logger silently stops that app's records reaching the log file.
5. If it has templates, put them in ``<name>/templates/<name>/``. The app-directories
   loader finds them; the explicit list in the ``TEMPLATES`` setting is a second route to
   the same directories and does not have to be extended.
6. If it declares a model, make it ``managed = False``: the import pipeline creates
   every OPUS table, so a managed model would invite a migration that must not exist.
   See :ref:`dev_guide_webapp_models`.

.. _dev_guide_webapp_extending_frontend:

Adding to the front end
-----------------------

The front end is plain JavaScript with no build step. A new area of the interface is a
new file under ``src/opus_app/static/js/`` defining one global namespace object, loaded
from the page template, and wired into the start-up sequence in ``opus.js``.

Three conventions to follow, because everything else already does:

* **One namespace object per file**, declared inside the linter pragma the other files
  use, and named in the ``globals`` comment of every file that calls into it.
* **Reflect state into the hash.** Anything a user changes that should survive a
  bookmark goes through ``hash.js``; that is what makes an OPUS URL a permanent link, and
  what :func:`~opus_app.apps.ui.views.api_normalize_url` then has to be taught about.
* **Reference assets under** ``/static_media/``, which is fixed for the reasons
  :ref:`dev_guide_webapp_static` gives.

Adding a **search widget type** is more than a front-end change: the widget's HTML comes
from :func:`~opus_app.apps.ui.views.api_get_widget` and
:class:`~opus_app.apps.search.forms.SearchForm`, the values are parsed by
:func:`~opus_app.apps.search.views.url_to_search_params`, and the SQL comes from one of
the four query builders. A genuinely new *kind* of field therefore touches all four,
plus the ``field_type`` and ``pi_form_type`` vocabularies in
:ref:`dev_guide_table_schemas`.

Where to go next
----------------

:ref:`dev_guide_webapp_tools`
    The shared machinery a new endpoint should be built out of.

:ref:`dev_guide_testing`
    The suites, and which one covers what you changed.

:ref:`dev_guide_conventions`
    The style and quality rules, and the one waiver that applies here.

API reference
-------------

:doc:`api_opus_app`
