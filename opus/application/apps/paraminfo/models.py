from django.db import models
from dictionary.views import get_def_for_tooltip

from search.models import TableNames

import opus_support

class ParamInfo(models.Model):
    """
    This model describes every searchable param in the database.
    Each has attributes like display, display order, query type, slug, etc.
    """
    category_name = models.CharField(max_length=150)
    name = models.CharField(max_length=87)
    form_type = models.CharField(max_length=100, blank=True, null=True)
    display = models.CharField(max_length=1)
    display_results = models.IntegerField()
    disp_order = models.IntegerField()
    label = models.CharField(max_length=240, blank=True, null=True)
    label_results = models.CharField(max_length=240, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    old_slug = models.CharField(max_length=255, blank=True, null=True)
    units = models.CharField(max_length=75, blank=True, null=True)
    intro = models.CharField(max_length=1023, blank=True, null=True)
    tooltip = models.CharField(max_length=255, blank=True, null=True)
    dict_context = models.CharField(max_length=255, blank=True, null=True)
    dict_name = models.CharField(max_length=255, blank=True, null=True)
    sub_heading = models.CharField(max_length=150, blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        db_table = ('param_info')
        ordering = ('category_name', 'sub_heading', 'disp_order')

    def __unicode__(self):
        return u"%s" % self.name

    def param_qualified_name(self):
        return self.category_name + '.' + self.name

    def get_tooltip(self):
        definition = get_def_for_tooltip(self.dict_name, self.dict_context)
        return definition

    def body_qualified_label(self):
        # Append "[Ring]" or "[<Surface Body>]" or "[Mission]" or "[Instrument]"
        if self.label is None: # pragma: no cover
            return None

        append_to_label = None

        pretty_name = (TableNames.objects
                       .get(table_name=self.category_name).label)
        pretty_name = pretty_name.replace(' Surface Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Mission Constraints', '')
        pretty_name = pretty_name.replace(' Constraints', '')

        if pretty_name == 'Surface':
            return self.label
        return self.label + ' [' + pretty_name + ']'

    def body_qualified_label_results(self):
        # Append "[Ring]" or "[<Surface Body>]" or "[Mission]" or "[Instrument]"
        if self.label_results is None:
            return None

        append_to_label = None

        pretty_name = (TableNames.objects
                       .get(table_name=self.category_name).label)
        pretty_name = pretty_name.replace(' Surface Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Mission Constraints', '')
        pretty_name = pretty_name.replace(' Constraints', '')

        if pretty_name in ['General', 'PDS', 'Wavelength', 'Image', 'Surface']:
            return self.label_results
        return self.label_results + ' [' + pretty_name + ']'

    def get_units(self):
        # Put parentheses around units (units)
        if self.units:
            return '(' + opus_support.UNIT_TRANSLATION[self.units] + ')'
        else:
            return ''

    def fully_qualified_label_results(self):
        ret = self.body_qualified_label_results()
        if ret is None: # pragma: no cover
            return None
        units = self.get_units()
        if units != '':
            ret += ' '+units
        return ret
