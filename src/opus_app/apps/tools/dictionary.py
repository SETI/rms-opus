# tools/dictionary.py
"""The PDS data dictionary tables and the tooltip lookup made against them.

`definitions` and `contexts` are written only by the import pipeline's
`--import-dictionary` step, never by the web application, which is why both models
are `managed = False`: Django is told the tables exist but must not create, alter or
drop them.

These two models and `get_def_for_tooltip` used to be a Django app of their own. The
browsable dictionary site that app once served was removed long before this file
existed, leaving an app whose entire content was the code below, so the app was
deleted and its remains moved here. `tools` is where they belong: it is the app the
other OPUS apps already reach into for shared helpers, and `paraminfo`, `ui` and
`cart` are exactly the three that use them.

Both classes were produced by `inspectdb` and their field definitions are reproduced
verbatim, because the columns they name are created by the import pipeline rather
than by a migration: a field changed here would silently stop matching the table.
"""

import logging

from django.db import models

log = logging.getLogger(__name__)


class Contexts(models.Model):
    """One namespace of dictionary terms, e.g. a PDS mission or instrument."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=25)
    description = models.CharField(max_length=100)
    parent = models.CharField(max_length=25)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contexts'


class Definitions(models.Model):
    """The definition of one term within one context."""

    id = models.IntegerField(primary_key=True)
    term = models.CharField(max_length=255)
    context = models.ForeignKey(Contexts, models.DO_NOTHING,
                                related_name='%(class)s_name',
                                db_column='context', to_field='name')
    definition = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'definitions'
        unique_together = (('term', 'context'),)


def get_def_for_tooltip(term, context):
    """Get a dictionary definition for (i) tooltips in the OPUS UI.

    Parameters:
        term: The dictionary term to look up.
        context: The name of the context the term is defined in.

    Returns:
        The definition text, or None when the term is not defined in that context.
        A missing definition is logged as an error except for the MULT_ contexts,
        where a mult value is allowed to carry no tooltip.
    """
    try:
        entry = Definitions.objects.get(context__name=context, term=term)
    except Definitions.DoesNotExist:
        # We allow mult tooltips to be None
        if not context.startswith('MULT_'): # pragma: no cover - import error
            log.error('No tooltip definition for context "%s" term "%s"',
                      context, term)
        return None
    return entry.definition
