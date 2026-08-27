# tools/dictionary.py
"""The PDS data dictionary tables and the tooltip lookup made against them.

`definitions` and `contexts` are written only by the import pipeline's
`--import-dictionary` step, never by the web application, which is why both models
are `managed = False`: Django is told the tables exist but must not create, alter or
drop them.

They live in `tools` because that is the app the rest of OPUS reaches into for
shared helpers: `paraminfo`, `ui` and `cart` are the three that use them.

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
        """Model options: the table the rows come from, which Django does not manage."""

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
        """Model options: the table the rows come from, which Django does not manage."""

        managed = False
        db_table = 'definitions'
        unique_together = (('term', 'context'),)


def get_def_for_tooltip(term: str | None, context: str | None) -> str | None:
    """Get a dictionary definition for (i) tooltips in the OPUS UI.

    Parameters:
        term: The dictionary term to look up. Nothing at all matches no definition,
            which is what a mult value with no stored value amounts to.
        context: The name of the context the term is defined in.

    Returns:
        The definition text, or None when the term is not defined in that context.
        A missing definition is logged as an error except for the ``MULT_`` contexts,
        where a mult value is allowed to carry no tooltip.
    """
    try:
        entry = Definitions.objects.get(context__name=context, term=term)
    except Definitions.DoesNotExist:
        # We allow mult tooltips to be None
        # A context of None matches no definition and then reaches this line, where
        # it raises AttributeError. Every ParamInfo column this is called with is
        # nullable, so that is a real fault rather than a typing artifact, and it is
        # recorded here instead of being annotated away.
        if not context.startswith('MULT_'): # type: ignore[union-attr] # pragma: no cover - import error
            log.error('No tooltip definition for context "%r" term "%r"',
                      context, term)
        return None
    return entry.definition
