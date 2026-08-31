.. _dev_guide_webapp_results:

Reading a Search: the ``results``, ``metadata`` and ``cart`` Apps
=================================================================

Three apps read from a completed search. :mod:`opus_app.apps.results` returns what the
search *found*; :mod:`opus_app.apps.metadata` describes what is *searchable* and how many
observations match; :mod:`opus_app.apps.cart` holds what a session has *selected* and
builds the downloads.

All three depend on the cache table :ref:`dev_guide_webapp_search_flow` describes, and
all three go through one paging routine.

.. _dev_guide_webapp_results_app:

The ``results`` app
-------------------

Twelve routed handlers, all reading and none writing. Every one that pages through
observations goes through
:func:`~opus_app.apps.results.views.get_search_results_chunk`.

.. list-table::
   :header-rows: 1
   :widths: 46 12 42

   * - Route
     - API
     - Handler
   * - ``__api/dataimages.json``
     - private
     - :func:`~opus_app.apps.results.views.api_get_data_and_images`
   * - ``api/data.(json|html|csv)``, ``__api/data.csv``
     - public
     - :func:`~opus_app.apps.results.views.api_get_data`
   * - ``api/metadata/<opus_id>.(json|html|csv)``,
       ``api/metadata_v2/<opus_id>.(json|html|csv)``
     - public
     - :func:`~opus_app.apps.results.views.api_get_metadata`
   * - ``__api/metadata/<opus_id>.(json|html|csv)``
     - private
     - :func:`~opus_app.apps.results.views.api_get_metadata_internal`
   * - ``api/images/<size>.(json|html|csv)``
     - public
     - :func:`~opus_app.apps.results.views.api_get_images_by_size`
   * - ``api/images.(json|csv)``
     - public
     - :func:`~opus_app.apps.results.views.api_get_images`
   * - ``api/image/<size>/<opus_id>.(json|html|csv)``,
       ``__api/image/<size>/<opus_id>.json``
     - both
     - :func:`~opus_app.apps.results.views.api_get_image`
   * - ``api/files/<opus_id>.json``, ``api/files.json``
     - public
     - :func:`~opus_app.apps.results.views.api_get_files`
   * - ``api/categories/<opus_id>.json``, ``__api/categories/<opus_id>.json``
     - both
     - :func:`~opus_app.apps.results.views.api_get_categories_for_opus_id`
   * - ``api/categories.json``
     - public
     - :func:`~opus_app.apps.results.views.api_get_categories_for_search`
   * - ``api/product_types/<opus_id>.json``
     - public
     - :func:`~opus_app.apps.results.views.api_get_product_types_for_opus_id`
   * - ``api/product_types.json``
     - public
     - :func:`~opus_app.apps.results.views.api_get_product_types_for_search`

The app's ``urls.py`` also routes ``__fake/__api/dataimages.json`` to
:func:`opus_app.apps.ui.views.api_dummy` -- a handler that does nothing, so that a user
action can be recorded in the web log without the work being done.

The paging engine
~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.results.views.get_search_results_chunk` is the single routine
behind every listing in OPUS, including the cart's. Given a request and a column list it
returns the page number, the first observation number, the limit, the rows, the sort
order, an auxiliary dictionary and an error pair.

It has two modes:

**Reading a search.** It resolves the query string to a cache table, creates a
**temporary table** holding just that page's slice of it -- ``sort_order`` and ``id``,
with the limit and offset applied -- INNER JOINs the wide query to that, and drops the
temporary table before returning. Settling the ordering and the paging before the joins
run is the point.

**Reading the cart.** No temporary table: it joins the ``cart`` table directly and
applies the sort order and the paging to the main statement. The paging parameters are
named differently in this mode, so that a browse position and a cart position can both be
in one URL.

Around the query it does four things worth knowing. Every requested slug is resolved
through :func:`~opus_app.apps.search.views.get_param_info_by_slug`, so an unknown column
is a 400 rather than a SQL error. Two columns may be prepended and appended to the
caller's list and stripped off the right end afterwards, which is how a caller gets the
OPUS ID or the preview JSON without them appearing in the output. A SQL NULL becomes the
string ``'N/A'``. And every value is put through
:func:`opus_support.units.format_unit_value`, so a number arrives already formatted in
the unit the request asked for.

:func:`~opus_app.apps.results.views.get_search_results_chunk_error_handler` turns the
error pair it returns into the right response -- a 400 raise or a 500 return. The cart app
imports it too.

What each handler returns
~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.results.views.api_get_data_and_images`
    One page of the browse or cart grid: per observation an OPUS ID, the metadata column
    values, the four preview images with their dimensions, and whether the observation is
    in the cart, in the recycle bin, or neither. It is the busiest endpoint in OPUS.

:func:`~opus_app.apps.results.views.api_get_data`
    The public tabular page: the labels, the rows, and how many observations the search
    found. JSON, HTML or CSV.

:func:`~opus_app.apps.results.views.api_get_metadata` and :func:`~opus_app.apps.results.views.api_get_metadata_internal`
    One observation's metadata. Both delegate to
    :func:`~opus_app.apps.results.views.get_metadata`. Without a column list it walks the
    "Constraints" categories in display order and returns every displayable field of
    each; with ``cols`` it returns exactly those fields, through
    ``_get_metadata_by_slugs``. The private form differs
    in three ways: its HTML is the Details tab's flavor, with tooltips and search icons;
    its column slugs may carry a ``:unit`` suffix; and it accepts a list of columns to
    embed in the search links it renders.

:func:`~opus_app.apps.results.views.api_get_images_by_size`, :func:`~opus_app.apps.results.views.api_get_images` and :func:`~opus_app.apps.results.views.api_get_image`
    The preview images for a search at one size, for a search at every size, and for one
    observation. All three share
    ``_api_get_images``, which reads the preview JSON out
    of ``obs_general`` and hands it to
    :func:`~opus_app.apps.tools.file_utils.get_pds_preview_images`. The single-observation
    form works by injecting an OPUS ID constraint into a copy of the query string, so
    that one code path serves both.

:func:`~opus_app.apps.results.views.api_get_files`
    Every file of one observation, or of a whole search, optionally filtered by product
    type. The result separates the current version from all versions, because a caller
    usually wants the first and occasionally needs the second.

:func:`~opus_app.apps.results.views.api_get_categories_for_opus_id` and :func:`~opus_app.apps.results.views.api_get_categories_for_search`
    Which "Constraints" categories an observation appears in, and which a search
    triggers. The first probes each table for a row; the second uses
    :func:`~opus_app.apps.results.views.get_triggered_tables`. Both skip
    ``obs_surface_geometry_name``, which is not a data table.

:func:`~opus_app.apps.results.views.api_get_product_types_for_opus_id` and :func:`~opus_app.apps.results.views.api_get_product_types_for_search`
    The product types available for one observation, or across a whole search. The
    search form caches its built response in the Django cache under the cache table's
    name.

:func:`~opus_app.apps.results.views.get_triggered_tables`
    Which tables a search makes relevant. With no selections it is the ``BASE_TABLES``
    setting; otherwise it walks every ``partables`` row and fires a trigger when the
    search's observations all carry the triggering value. A surface geometry trigger is
    the exception, compared as text rather than through a query --
    :ref:`dev_guide_import_steps_do_partables` explains why. The result is ordered by the
    ``table_names`` display order and cached.

:func:`~opus_app.apps.results.views.labels_for_slugs`
    A slug list to its display labels, with the unit appended. The cart app imports it
    too.

Two private helpers build the SQL the app's own queries need:
``_results_column_select`` turns a resolved column list into the SELECT terms, in the
caller's order -- which is what the result rows are then unpacked positionally against --
and leaves every join to its callers; ``_product_types_select`` builds the query behind
both product-type endpoints.

:mod:`opus_app.apps.results.templatetags.encode_value` supplies one template filter,
:func:`~opus_app.apps.results.templatetags.encode_value.encode_value`, which turns a
metadata value into the query-string form of an OPUS search URL, so that a link built
around a value searches for that exact value.

.. _dev_guide_webapp_metadata_app:

The ``metadata`` app
--------------------

What is *searchable*, rather than what was found. Eight routes served by seven
handlers, three of which are private wrappers that add a ``reqno`` echo. **The private
ones are not themselves decorated**:
each simply calls its public twin, which is where the
:func:`~opus_app.apps.tools.app_utils.api_view` wrapping happens.

.. list-table::
   :header-rows: 1
   :widths: 50 12 38

   * - Route
     - API
     - Handler
   * - ``api/meta/result_count.(json|html|csv)``
     - public
     - :func:`~opus_app.apps.metadata.views.api_get_result_count`
   * - ``__api/meta/result_count.json``
     - private
     - :func:`~opus_app.apps.metadata.views.api_get_result_count_internal`
   * - ``api/meta/mults/<slug>.(json|html|csv)``
     - public
     - :func:`~opus_app.apps.metadata.views.api_get_mult_counts`
   * - ``__api/meta/mults/<slug>.json``
     - private
     - :func:`~opus_app.apps.metadata.views.api_get_mult_counts_internal`
   * - ``api/meta/range/endpoints/<slug>.(json|html|csv)``
     - public
     - :func:`~opus_app.apps.metadata.views.api_get_range_endpoints`
   * - ``__api/meta/range/endpoints/<slug>.json``
     - private
     - :func:`~opus_app.apps.metadata.views.api_get_range_endpoints_internal`
   * - ``api/fields/<slug>.(json|csv)``, ``api/fields.(json|csv)``
     - public
     - :func:`~opus_app.apps.metadata.views.api_get_fields`

**The result count** is a row count over the cache table, cached in the Django cache
under that table's name. :func:`~opus_app.apps.metadata.views.get_result_count_helper` is
the routine, and it returns the count, the table name and an error response, so that a
caller that also needs the table does not resolve the search twice. The results and cart
apps both use it.

**The mult counts** are what the interface's green numbers beside each checkbox are: for
each value of a mult field, how many of the search's observations have it. **The field's
own constraint is removed from the search first**, so that ticking one box does not make
the other boxes read zero. A ``MULTIGROUP`` field holds a JSON list, so its counts come
from a :class:`~opus_app.apps.tools.sql_builder.JSONTable` that explodes the list into
rows. The values come back in the mult table's display order.

**The range endpoints** are the smallest and largest value a numeric field takes over the
search, plus how many observations have neither. The field's own constraints are removed
for the same reason as above. With no search at all it uses the ORM's aggregates over the
whole table; with one it issues raw ``MIN`` and ``MAX`` joined to the cache table. The
answer is cached per field, per unit and per search.

**The field descriptions** are the public field dictionary:
:func:`~opus_app.apps.metadata.views.get_fields_info` builds one entry per field, or one
for the named field, carrying its id, its category, its type, its four labels, its default
and available units, and its previous slug. It follows a ``referred_slug`` to the field it
names, and skips the internal slugs that begin ``**``. Its ``collapse`` option folds the
per-target surface geometry fields onto one representative with ``<TARGET>`` standing in
for the body, which is what makes the field list a readable size.

:func:`~opus_app.apps.metadata.views.get_cart_count` is here rather than in the cart app,
returning a session's cart and recycle-bin counts; the results and cart apps both call
it.

.. _dev_guide_webapp_cart_app:

The ``cart`` app
----------------

The one app that writes rows a user can see. (The search app writes too --
``user_searches`` and the ``cache_NNN`` tables -- but nothing a user selected.) A cart is
the set of ``cart`` rows carrying one session id;
a row whose ``recycled`` column is set is in the recycle bin -- still in the table,
counted separately, and left out of the download totals and the archives themselves.

Every route is private except ``api/download/<opus_id>.(zip|tar|tgz)``, which is
public and is documented in :ref:`api_guide`.

.. list-table::
   :header-rows: 1
   :widths: 52 48

   * - Route
     - Handler
   * - ``__cart/view.json``
     - :func:`~opus_app.apps.cart.views.api_view_cart`
   * - ``__cart/status.json``
     - :func:`~opus_app.apps.cart.views.api_cart_status`
   * - ``__cart/data.csv``
     - :func:`~opus_app.apps.cart.views.api_get_cart_csv`
   * - ``__cart/(add|remove|addrange|removerange|addall).json``
     - :func:`~opus_app.apps.cart.views.api_edit_cart`
   * - ``__cart/reset.json``
     - :func:`~opus_app.apps.cart.views.api_reset_session`
   * - ``__cart/download.json``, ``api/download/<opus_id>.(zip|tar|tgz)``,
       ``__api/download/<opus_id>.(zip|tar|tgz)``
     - :func:`~opus_app.apps.cart.views.api_create_download`

The session and the recycle bin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every handler begins with
:func:`~opus_app.apps.tools.app_utils.get_session_id`, and every read and write carries
that session id. The ``cart`` table's unique key over the session and the observation is
what makes the writes idempotent, and is why they are ``REPLACE INTO`` rather than a
delete followed by an insert: a second concurrent write becomes a replacement rather than
a duplicate.

:func:`~opus_app.apps.cart.views.api_edit_cart`'s own docstring carries the authoritative
state-transition table for the five actions crossed with the recycle-bin flag; it is the
thing to read before changing any of them. The shape of it is:

* **Adding** anything moves it into the cart, whether it was absent or in the recycle
  bin. A bad OPUS ID is an error.
* **Removing** with the recycle-bin flag set moves it into the bin; without the flag it
  deletes the row outright. A bad OPUS ID is silently ignored in the first case and an
  error in the second.
* ``addall`` **with** ``view=cart`` **and the recycle-bin flag** is the documented way to
  move everything out of the bin and back into the cart.

Underneath the five actions sit four helpers: ``_add_to_cart_table`` and
``_remove_from_cart_table`` are the single-observation writes, ``_edit_cart_addall``
implements ``addall`` by reading the whole current view and adding every observation in
it, and ``_edit_cart_range`` is below.

:func:`~opus_app.apps.cart.views.api_reset_session` empties the cart -- or, with the
recycle-bin flag, only the bin. Despite the name it deletes cart rows and does not touch
the Django session.

Adding a range
~~~~~~~~~~~~~~

``_edit_cart_range`` adds or removes an inclusive range of
observations, given the two ends' OPUS IDs, **in the current sort order**. Reading the
browse list it uses the search's cache table; reading the cart it has to build a
**temporary table** of the session's cart in sort order first, because the cart has no
cache table of its own. The delete form explicitly carries the session id in its WHERE
clause, so it cannot reach another user's cart.

Reading the cart
~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.cart.views.api_view_cart`
    The OPUS-specific left side of the Selections page, rendered as HTML by
    ``cart/cart.html``: the cart and recycle-bin counts, and the product-type table
    ``_get_download_info`` builds, with each type's file count and total size. Two
    arguments shape it, and they do different things: ``types`` limits which product types
    the two grand totals at the top of the panel count, defaulting to ``all`` -- which
    counts every type ``obs_files`` marks ``default_checked``, and no others. The per-type
    file counts and sizes are computed for every type regardless. ``unselected_types``
    names the types the template renders **unchecked**, as is any type ``obs_files`` does
    not mark ``default_checked``. It does not page through observations -- that is
    :func:`~opus_app.apps.results.views.api_get_data_and_images` with ``view=cart``.

:func:`~opus_app.apps.cart.views.api_cart_status`
    The numbers the Selections panel shows: how many observations are in the cart and how
    many in the recycle bin, and, when asked, the download summary from
    ``_get_download_info`` -- the product types the cart offers and the file counts and
    total sizes each would contribute. It is the endpoint the interface calls after every
    cart edit, which is why the expensive half is optional.

Downloads
~~~~~~~~~

:func:`~opus_app.apps.cart.views.api_create_download` builds the archive. In order:

1. Resolve the product types and the observations -- one from the path, or the
   session's non-recycled cart. ``types`` defaults to ``all``, which applies no version
   filter at all, so the archive holds **every** version. Passing ``types`` **empty** is
   what restricts it to the current version, which is the opposite of what the code
   comment beside it says.
2. Check the selection count against ``MAX_SELECTIONS_FOR_DATA_DOWNLOAD``, or
   ``MAX_SELECTIONS_FOR_URL_DOWNLOAD`` for a URL-only download.
3. Resolve the files with
   :func:`~opus_app.apps.tools.file_utils.get_pds_products`, asking for raw entries so
   that on-disk paths, checksums and sizes all come back at once.
4. Choose the format from ``DOWNLOAD_FORMATS``: ZIP, TAR or gzipped TAR. An unknown one
   is a 400.
5. Write the metadata CSV.
6. Check the size: a single download against ``MAX_DOWNLOAD_SIZE``, and the running
   total for the session against ``MAX_CUM_DOWNLOAD_SIZE``. The running total is kept in
   the Django session, so it survives across downloads and resets when the session does.
   Both checks are skipped for a URL-only download, which transfers no data.
7. Add each file. Names are flattened to their basenames unless the caller asked for a
   hierarchy **or two files in the archive would collide**, in which case the logical
   path is used. A per-file failure is collected rather than raised, and the collected
   errors are appended to the manifest.
8. Add the manifest, the metadata CSV and the URL list to the archive, close it, and
   remove the two temporary text files.

A single-observation download is streamed back directly; a cart download is written under
the configured directory and its URL returned, because it can be very large.

``_get_download_info`` is what the Selections page's numbers
come from: the product types the whole cart offers -- **the whole cart, recycle bin
included, so the panel need not be redrawn on every edit** -- and, separately, the file
counts and total sizes over the **non-recycled** cart only. Sizes are totaled over
*distinct* logical paths, because one file can serve several observations.

:func:`~opus_app.apps.cart.views.api_get_cart_csv` streams the cart as CSV, through
``_csv_helper``, which is a thin wrapper over the same
paging engine with the recycle bin included and no limit. ``_create_csv_file`` is the
other half: it writes the metadata CSV that goes inside a download archive.

The model
~~~~~~~~~

:class:`opus_app.apps.cart.models.Cart` is a hand-written unmanaged model: the session
id, a foreign key to ``obs_general``, the OPUS ID, the recycled flag and a timestamp. The
generated models file carries a ``ZZ``-prefixed duplicate of the same table, which
nothing uses.

API reference
-------------

:doc:`api_opus_app.apps.results`, :doc:`api_opus_app.apps.metadata`,
:doc:`api_opus_app.apps.cart`
