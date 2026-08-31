.. _dev_guide_dictionary:

The Data Dictionary
===================

Every tooltip the OPUS interface shows comes out of two database tables, ``contexts``
and ``definitions``. :ref:`dev_guide_database` describes their columns; this chapter
describes **where their contents come from** and how to add a term.

Both are built by :mod:`opus_import.steps.do_dictionary`, under
``--import-dictionary``, and by nothing else. The web application only reads them, which
is why :class:`~opus_app.apps.tools.dictionary.Contexts` and
:class:`~opus_app.apps.tools.dictionary.Definitions` are declared unmanaged.

Where a context comes from
--------------------------

``src/opus_import/dictionary_data/contexts.csv`` -- one line per context, three fields:
the internal name, the description, and the parent's internal name (or the literal
``NULL`` for the root). It is packaged with :mod:`opus_import` and read through
:mod:`importlib.resources`, so an installed OPUS finds it without a checkout.

A line with any other number of fields **stops the read**, so nothing is written and the
whole build fails. That is deliberate: a context tree assembled from a partly-read file
would give a term the wrong parent rather than no parent.

:func:`~opus_import.steps.do_dictionary.create_import_contexts_table` reads it, and it
runs before the definitions builder because ``definitions`` carries a foreign key onto
``contexts``.

Where a definition comes from
-----------------------------

The **table schemas**, which is where OPUS's own parameters are described.
:func:`~opus_import.steps.do_dictionary.create_import_definitions_table` reads every
packaged schema file matching three globs -- ``obs*.json``, ``internal_def*.json`` and
``mult_tooltips*.json`` -- and, for every column that carries one, turns a
``definition`` key into a row.

Each definition is filed under the context named beside it. A column contributes up to
two rows, because a field can be described differently on the Search tab and beside a
result:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Schema keys
     - Row
   * - ``definition``, ``pi_dict_name``, ``pi_dict_context``
     - The term shown as the field's tooltip on the Search tab.
   * - ``definition_results``, ``pi_dict_name_results``, ``pi_dict_context_results``
     - The term shown beside a result.

A ``definition`` with no term name or no context is an error, and the builder collects
**every** such fault before writing anything, so one run reports all of them and a
broken schema leaves the previous run's tables untouched.

Two of the three globs are worth a word:

``internal_def_product_types.json``
    A dictionary source rather than a table. Its entries carry only ``definition``,
    ``pi_dict_name`` and ``pi_dict_context`` -- no ``field_name``, no ``field_type`` --
    and they are what gives each PDS product type its description in the cart and on the
    Details tab.

``mult_tooltips*.json``
    A shape the builder supports and **no file uses**. Such a file would also
    contribute a ``contexts`` row of its own, named ``MULT_<slug>`` from the file's own
    name, which is the naming
    :func:`~opus_app.apps.tools.dictionary.get_def_for_tooltip` recognizes as a mult
    tooltip.

How a tooltip is looked up
--------------------------

:func:`opus_app.apps.tools.dictionary.get_def_for_tooltip` takes a term and a context and
returns the definition, or None when there is none.
:meth:`opus_app.apps.paraminfo.models.ParamInfo.get_tooltip` and
:meth:`~opus_app.apps.paraminfo.models.ParamInfo.get_tooltip_results` are what the
templates call; the results form falls back to the search form's term when the results
one is not set.

A missing definition is logged as an error **except** for a context beginning ``MULT_``,
because a mult value legitimately has no tooltip.

The build and the copy
----------------------

:func:`~opus_import.steps.do_dictionary.do_dictionary` drops both import tables, builds
contexts and then definitions, and copies both over the permanent tables **only if both
builds succeeded**. It drops the import tables again afterwards, so a failed build
leaves nothing behind.

The copy order is the reverse of the drop order, for the foreign key: ``definitions`` is
dropped first and created last.

**A failed dictionary import does not change the run's exit status.** It reports through
the log, like :mod:`~opus_import.steps.do_validate`; see
:ref:`dev_guide_import_verifying`.

Adding a term
-------------

1. **Choose or add the context.** If the term belongs under a context
   ``contexts.csv`` already names, use it. Otherwise add a line to that file, naming a
   parent that already exists.
2. **Add the text to the schema.** Put ``definition`` on the column, together with
   ``pi_dict_name`` and ``pi_dict_context``. Add the ``_results`` trio as well if the
   field should read differently beside a result.
3. **Rebuild.** ``opus_import --import-dictionary`` rewrites both tables from scratch;
   nothing incremental is possible, and nothing else needs re-running.
4. **Restart the web application.** The definition lookup is a database query rather than
   a process-local cache, so this is only needed if you also changed ``param_info``.

:mod:`opus_import.util.dump_pds_definitions` prints a PDS index label's own field
descriptions in exactly the form a ``definition`` key wants, which is the quickest way to
write the text for a new instrument's columns. See :ref:`dev_guide_import_running`.

API reference
-------------

:doc:`api_opus_import`, :doc:`api_opus_app.apps.tools`
