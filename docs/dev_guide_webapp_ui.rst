.. _dev_guide_webapp_ui:

The Interface: the ``ui``, ``help`` and ``paraminfo`` Apps
==========================================================

The apps and the front end that serve the page a user actually looks at:
:mod:`opus_app.apps.ui` renders the single page and the calls that keep it current;
:mod:`opus_app.apps.help` serves the help pages; :mod:`opus_app.apps.paraminfo` is the
description of every field, which the other two render from. The JavaScript and CSS that
run in the browser are at the end of this chapter.

.. _dev_guide_webapp_ui_app:

The ``ui`` app
--------------

OPUS is a single page. The browser loads it once and then asks for pieces of itself as
the user works, and every route below serves one of those pieces.

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Route
     - Serves
   * - ``/`` and ``/opus/``
     - :class:`~opus_app.apps.ui.views.MainSite` -- the page itself. Routed from
       :mod:`opus_app.urls` rather than from this app's own ``urls.py``.
   * - ``__notifications.json``
     - :func:`~opus_app.apps.ui.views.api_notifications` -- the notification banner and
       the blog-updated date.
   * - ``__menu.json``
     - :func:`~opus_app.apps.ui.views.api_get_menu` -- the Search tab's category menu.
   * - ``__metadata_selector.json``
     - :func:`~opus_app.apps.ui.views.api_get_metadata_selector` -- the Select Metadata
       modal.
   * - ``__widget/<slug>.html``
     - :func:`~opus_app.apps.ui.views.api_get_widget` -- one search widget.
   * - ``__initdetail/<opus_id>.html``
     - :func:`~opus_app.apps.ui.views.api_init_detail_page` -- the top of the Details
       tab.
   * - ``__normalizeurl.json``
     - :func:`~opus_app.apps.ui.views.api_normalize_url` -- bringing a bookmarked URL up
       to date.
   * - ``__dummy.json`` and two ``__fake/`` routes
     - :func:`~opus_app.apps.ui.views.api_dummy` -- does nothing, for timing.
   * - ``admin/``
     - Django's admin site. No app defines an admin module, so it is effectively inert.

Every ``__``-prefixed route is private; the page itself and the admin site are not.
Of the private ones, all but ``__menu.json`` carry ``@never_cache``.

MainSite
~~~~~~~~

:class:`opus_app.apps.ui.views.MainSite`

Renders ``ui/base.html`` and supplies the front end's start-up defaults: the default
columns, widgets, sort order and selection limit; the preview guides; the API guide's
URL; **the search menu already rendered into the page**, rather than fetched, so the
first paint needs no round trip; and a version suffix the templates append to every
static asset URL.

That suffix is what cache-busts the assets on a release. It comes from the
``OPUS_FILE_VERSION`` setting, which starts empty and is **filled in from the installed
distribution's version the first time this view runs** -- so it is computed once per
worker process and is stable thereafter.

api_notifications
~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.ui.views.api_notifications`

Two pieces of site content that are maintained outside the repository, each in a file the
configuration names: the date of the last blog update, and the HTML of any short-term
notification. **A file that is not there is not an error** -- its entry comes back as
null, which is how OPUS says there is nothing to show. The notification's modification
time is returned as well, so the front end can tell a new notification from one the user
has already dismissed.

api_get_menu and api_get_metadata_selector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.ui.views.api_get_menu`, :func:`opus_app.apps.ui.views.api_get_metadata_selector`

Both render a category-and-field tree, and both get it from the same private helper. They
differ in which fields they list -- the **searchable** ones for the Search tab, the
**displayable** ones for the Select Metadata modal -- and in what the modal adds: a
synthetic "Current Search Fields" category at the top, and a second template for the
add-a-field list.

The helper is where four decisions live:

* **Which categories appear** is the search's triggered tables, from
  :func:`~opus_app.apps.results.views.get_triggered_tables`, or the ``BASE_TABLES``
  setting when there is no search.
* **Which are expanded** comes from an ``expanded_cats`` parameter, defaulting to the
  general category on the Search tab and to the synthetic one in the modal.
* ``obs_surface_geometry_name``'s fields are **folded into**
  ``obs_surface_geometry``, and that category is not offered separately.
* On the Search tab a range field is listed once, under its unsuffixed slug; in the modal
  both ends are listed, because a user selects them as separate columns.

Each field is decorated with its display unit, its default unit and its available units
before the template sees it, which is why the templates need to know nothing about the
unit system.

api_get_widget
~~~~~~~~~~~~~~

:func:`opus_app.apps.ui.views.api_get_widget`

Builds one search widget, **with the current search already filled in**, and returns it
as HTML rather than JSON. A range field constrained more than once comes back with one
set of inputs per constraint, which is how the ORed clauses of
:ref:`dev_guide_webapp_search_url_to_params` are edited.

It uses :class:`~opus_app.apps.search.forms.SearchForm` for the inputs themselves, and
adds three things around them: the preset range dropdowns, rendered in **every** valid
unit so that switching units needs no round trip; per-value tooltips for a mult field,
looked up under a ``MULT_`` context; and the grouped rendering of a grouped mult field,
one group at a time.

It also undoes the OPUS ID substitution: the search parser rewrites
``obs_pds.opus_id`` to ``obs_general.opus_id`` for efficiency, and this rewrites it back,
so the widget appears where the user expects it.

api_init_detail_page
~~~~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.ui.views.api_init_detail_page`

The parts of the Details tab that are **fast** to compute: the instrument, the preview
images, whether the observation is in the cart, and the file listing grouped by version
and product type. The slow part -- the metadata table -- is fetched separately, by the
results app, which is the whole reason this handler exists.

Each product type carries the tooltip its data-dictionary term supplies, and an index
product gets a link into the Node's file browser.

api_normalize_url
~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.ui.views.api_normalize_url`

**The largest handler in OPUS**, and the one that makes an OPUS URL a durable bookmark.
Given a top-level URL it rewrites every part of it into the form the current OPUS uses,
and returns both the new URL and an HTML message explaining what had to change.

It normalizes, in order: every search slug, with its query type and its unit; the
metadata column list; the widget list; the sort order; the tab being viewed; the two
browse modes; the two paging positions; and the observation being detailed. For each it
resolves a renamed slug to its current name, drops a value that does not resolve,
and fills in the default for anything the URL leaves out.

Three of its rules are worth knowing:

* **A query type or a unit is always emitted** once the field is understood, even when
  the URL omitted it, so a normalized URL is fully explicit.
* **Clause numbers are renumbered** from one, so a URL that has had clauses removed comes
  back tidy.
* **The sort order is truncated after the OPUS ID**, since nothing after a unique key can
  affect the ordering, and the OPUS ID is appended if it is absent.

The message it returns is null when the URL needed no explaining -- including when it was
empty, which is what a caller with no bookmark at all sends.

api_dummy
~~~~~~~~~

:func:`opus_app.apps.ui.views.api_dummy`

Returns an empty object. Several routes reach it: one for network performance testing, and
the ``__fake/`` modal URLs so that the front end can record a user action in the web log
without doing any work. The results app routes another.

opus_app.apps.ui.templatetags.multilines_template_tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One line of code, and a page of explanation for it. Django's template lexer splits a
template with a regular expression whose wildcard cannot cross a newline, so a tag
written over two lines is emitted as literal text instead of being evaluated. This
module recompiles the same pattern with the dot-matches-newline flag and changes nothing
else.

**It is not a template-tag library and must not be loaded as one.** It defines no
registry, so Django never offers it; the patch is applied purely as an import side
effect, because setting up the template engine imports every module in every installed
app's ``templatetags`` package and keeps only those that define a registry.

It is a monkeypatch of a private module global, so it carries the Django version it was
last verified against and the three checks that verification consists of. **Re-verify all
three on the next Django upgrade.**

.. _dev_guide_webapp_help_app:

The ``help`` app
----------------

Six pages, each of which can be returned as HTML or as a PDF -- except the splash page,
whose route carries no format at all.

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Route
     - Handler
   * - ``__help/about.(html|pdf)``
     - :func:`~opus_app.apps.help.views.api_about`
   * - ``__help/bundles.(html|pdf)``
     - :func:`~opus_app.apps.help.views.api_bundles`
   * - ``__help/faq.(html|pdf)``
     - :func:`~opus_app.apps.help.views.api_faq`
   * - ``__help/gettingstarted.(html|pdf)``
     - :func:`~opus_app.apps.help.views.api_gettingstarted`
   * - ``__help/splash.html``
     - :func:`~opus_app.apps.help.views.api_splash`
   * - ``__help/citing.(html|pdf)``
     - :func:`~opus_app.apps.help.views.api_citing_opus`
   * - ``apiguide.pdf``
     - A redirect. See below.

Where each page's content comes from:

**About** -- the installed version, the database schema and host being served, and the
machine's name. **Bundles** -- a live query: every distinct bundle in ``obs_general``,
grouped under its instrument's display name, so the page is always current. **FAQ** --
``faq.yaml``, which ships inside the package; the HTML offers the answers collapsed and
the PDF does not. **Getting Started** -- the template alone, with no context at all.
**Splash** -- the template alone, and the one page that never becomes a PDF. **Citing** --
a QR code for the public OPUS URL, plus one for each URL the caller passes, generated as
a base64-encoded PNG and embedded in the page.

How the PDF is made
~~~~~~~~~~~~~~~~~~~

One private helper renders every page. For HTML it renders the template normally; for
PDF it renders the site header template as well, concatenates the two into a complete
document, and hands the result to ``pdfkit`` -- which shells out to ``wkhtmltopdf``. The
options set Letter paper, one-inch margins, a page-number footer, PDF bookmarks, and
print media queries.

**This is why PDF generation is unavailable on a platform without ``wkhtmltopdf``**, and
why :ref:`dev_guide_installation` lists it as optional: every other page works without
it.

The API guide redirect
~~~~~~~~~~~~~~~~~~~~~~

``apiguide.pdf`` answers a 302 to the ``API_GUIDE_URL`` setting rather than serving a
generated PDF, because the public API guide is published as documentation and is not
built here. It is the one place where the compatibility waiver in
:ref:`dev_guide_conventions` covers the URL but not the response: the entry point still
resolves, and a test pins the redirect, but what comes back is a redirect rather than a
document.

The route's pattern carries a capture group, and Django's redirect view interpolates
the captured group into the target -- so **the target URL must contain no percent sign at
all**, or requesting the route raises.

.. _dev_guide_webapp_paraminfo_app:

The ``paraminfo`` app
---------------------

One model and no routes. :class:`opus_app.apps.paraminfo.models.ParamInfo` is one row of
the ``param_info`` table -- one searchable or displayable field -- and its methods are
what the interface asks for a field's label, its tooltip and its units, so that a template
can render a field without knowing anything else about it.

The table is written by :mod:`opus_import.steps.do_param_info` and is unmanaged here.
:ref:`dev_guide_table_schemas` documents the ``pi_*`` keys each column comes from.

The methods fall into three groups.

**Identity.**
:attr:`~opus_app.apps.paraminfo.models.ParamInfo.param_qualified_name` is the
``<table>.<column>`` name that identifies the field across all the observation tables.

**Labels.** :meth:`~opus_app.apps.paraminfo.models.ParamInfo.body_qualified_label` and
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.body_qualified_label_results` are the
interesting pair. **Many fields share a label and differ only in the body, the mission or
the instrument they describe**, so the name of the field's category is appended in
brackets: "Ring Radius [Ring]". The category name is first stripped of its "Constraints"
and "Geometry" suffixes, and nothing is appended where the result would be the bare word
``Surface``, nor to a label that already carries the bracketed name. The results form
additionally leaves the general categories alone, because a results column is already in
context. :meth:`~opus_app.apps.paraminfo.models.ParamInfo.fully_qualified_label_results`
adds the unit on top.

**Tooltips.** :meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_tooltip` and
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_tooltip_results` look the field's
dictionary term up; the results form falls back to the search form's term.
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_link_tooltip` is the text shown for
a field that is a link to one defined in another category.

**Units and types.** :meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_default_unit`,
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_units` and
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.is_valid_unit` wrap
:mod:`opus_support`, and each returns the empty string for a field whose values carry no
unit or whose unit is never shown.
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.is_string` and
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.is_string_or_mult` are the two form-type
tests the templates make, and
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_ranges_info` returns the preset
ranges a search widget offers, parsed out of the JSON the import stored.

.. _dev_guide_webapp_templates:

Templates
---------

Every page template lives in an app. ``src/opus_app/templates/`` holds three files and
nothing else: overrides of Django's own form-widget templates, which is what lets the
search form's inputs carry OPUS's own markup.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - App
     - Templates
   * - ``ui``
     - ``base.html`` (the page), ``header.html`` and ``footer.html``, ``menu.html``,
       ``widget.html``, ``select_metadata.html`` and ``add_field.html``, ``detail.html``,
       ``confirm_modal.html``, ``customized_input.html``.
   * - ``results``
     - ``data.html``, ``list.html``, ``image_list.html``, and the four
       ``detail_metadata*.html`` variants -- a public and an internal form of both the
       category listing and the slug listing.
   * - ``metadata``
     - ``result_count.html``, ``mults.html``, ``endpoints.html``.
   * - ``cart``
     - ``cart.html``.
   * - ``help``
     - One per page: ``about``, ``bundles``, ``citing``, ``faq``, ``gettingstarted``,
       ``splash``, plus ``tutorial.html``, which no view renders.
   * - ``search``, ``paraminfo``, ``tools``
     - None.

Two error pages, ``400.html`` and ``404.html``, sit directly under ``src/opus_app/apps/``
and are found because the settings list that directory as a template root.

.. _dev_guide_webapp_frontend:

The front end
-------------

``src/opus_app/static/`` ships in the wheel and is served under ``/static_media/``.
**There is no build step and no bundler**: the files are loaded as plain scripts and
communicate through global namespace objects. Introducing a bundler is tracked
separately as issue
`#1436 <https://github.com/SETI/rms-opus/issues/1436>`__.

Thirteen JavaScript files under ``static/js/``, each owning one area of the interface:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - File
     - Owns
   * - ``opus.js``
     - The entry point. Every start-up hook, every genuinely global variable, and the
       main load loop that fetches whatever the current tab needs and updates it.
   * - ``hash.js``
     - Reading and writing the browser hash. Every change a user makes updates it, which
       is what makes any point in a session a shareable permanent link.
   * - ``search.js``
     - The Search tab itself, and the hinting data the widgets show -- the range
       endpoints and the mult counts.
   * - ``widgets.js``
     - Fetching, rendering, opening, closing and grouping the individual search widgets.
   * - ``menu.js``
     - The category and field list on the Search tab and in the Select Metadata modal.
   * - ``browse.js``
     - The largest file: the gallery and table views, thumbnail interaction, the metadata
       box, range selection, paging and infinite scroll.
   * - ``cart.js``
     - Adding to and editing the cart, the Selections tab, and the download links.
   * - ``detail.js``
     - Rendering the Details tab.
   * - ``selectMetadata.js``
     - The Select Metadata dialog.
   * - ``sortMetadata.js``
     - Editing the sort order, and the sort indicators in the table header.
   * - ``mutationObserver.js``
     - Watching for DOM changes so that the scrollbars can be resized when a panel opens,
       a tab switches or a group collapses.
   * - ``utils.js``
     - Shared helpers.
   * - ``stringUtils.js``
     - Title-casing, with a list of minor words to leave lowercase and a long list of PDS
       and instrument acronyms to leave uppercase.

Beside them, ``static/`` holds the CSS, the images, a feedback widget, and four vendored
asset trees -- the Django admin's own assets, CoreUI, a set of CDN fallbacks and a
scrollbar library. **The vendored trees ship in the wheel deliberately**: a
pip-deployed server has no checkout to collect static files from, so
``collectstatic`` has to find them inside the package.

One constraint runs through all of it: the ``/static_media/`` prefix cannot be changed
by changing the setting alone. See :ref:`dev_guide_webapp_static`.

:func:`~opus_import.import_util.slug_name_for_sfc_target` in the import pipeline
carries a matching warning: the surface geometry target slugs it builds are re-derived in
``utils.js``, so the two have to agree.

API reference
-------------

:doc:`api_opus_app.apps.ui`, :doc:`api_opus_app.apps.help`,
:doc:`api_opus_app.apps.paraminfo`
