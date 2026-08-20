import logging

from opus_app.apps.dictionary.models import Definitions

log = logging.getLogger(__name__)


def get_def_for_tooltip(term, context):
    """Get a dictionary definition for (i) tooltips in the OPUS UI."""
    try:
        entry = Definitions.objects.get(context__name=context, term=term)
    except Definitions.DoesNotExist:
        # We allow mult tooltips to be None
        if not context.startswith('MULT_'): # pragma: no cover - import error
            log.error('No tooltip definition for context "%s" term "%s"',
                      context, term)
        return None
    return entry.definition
