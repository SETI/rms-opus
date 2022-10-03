from django.db import models
from dictionary.views import get_def_for_tooltip

import json

from search.models import TableNames

import settings

from opus_support import (display_result_unit,
                          get_default_unit,
                          get_unit_display_name,
                          is_valid_unit,
                          parse_form_type)

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
    referred_slug = models.CharField(max_length=255, blank=True, null=True)
    ranges = models.TextField()
    field_hints1 = models.CharField(max_length=255, blank=True, null=True)
    field_hints2 = models.CharField(max_length=255, blank=True, null=True)
    intro = models.CharField(max_length=1023, blank=True, null=True)
    tooltip = models.CharField(max_length=255, blank=True, null=True)
    dict_context = models.CharField(max_length=255, blank=True, null=True)
    dict_name = models.CharField(max_length=255, blank=True, null=True)
    dict_context_results = models.CharField(max_length=255, blank=True, null=True)
    dict_name_results = models.CharField(max_length=255, blank=True, null=True)
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

    def get_tooltip_results(self):
        if self.dict_name_results:
            definition = get_def_for_tooltip(self.dict_name_results,
                                             self.dict_context_results)
        else:
            definition = get_def_for_tooltip(self.dict_name, self.dict_context)
        return definition

    def get_link_tooltip(self):
        table_label = (TableNames.objects
                      .get(table_name=self.category_name).label)
        return (f'This field is a link to one available under {table_label}. '+
                'It is provided here for your convenience.')

    def body_qualified_label(self):
        # Append "[Ring]" or "[<Surface Body>]" or "[Mission]" or "[Instrument]"
        if self.label is None: # pragma: no cover
            return None

        pretty_name = (TableNames.objects
                       .get(table_name=self.category_name).label)
        pretty_name = pretty_name.replace(' Surface Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Mission Constraints', '')
        pretty_name = pretty_name.replace(' Constraints', '')

        if (pretty_name == 'Surface' or
            f'[{pretty_name}]' in self.label):
            return self.label
        return self.label + ' [' + pretty_name + ']'

    def body_qualified_label_results(self, referred=False):
        # Append "[Ring]" or "[<Surface Body>]" or "[Mission]" or "[Instrument]"
        if self.label_results is None:
            return None

        pretty_name = (TableNames.objects
                       .get(table_name=self.category_name).label)
        pretty_name = pretty_name.replace(' Surface Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Mission Constraints', '')
        pretty_name = pretty_name.replace(' Constraints', '')

        if (pretty_name in ['General', 'PDS', 'Wavelength', 'Image',
                            'Occultation/Reflectance Profiles', 'Surface']
            and not referred):
            return self.label_results
        # Make sure "[Ring]", "[<Surface Body>]", etc is not duplicated in the
        # label for referred slug.
        if f'[{pretty_name}]' in self.label_results:
            return self.label_results
        return self.label_results + ' [' + pretty_name + ']'

    def get_default_unit(self, override_unit=None):
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(self.form_type)
        if form_type_unit_id and display_result_unit(form_type_unit_id):
            if override_unit:
                unit = override_unit
            else:
                unit = get_default_unit(form_type_unit_id)
            display_name = get_unit_display_name(form_type_unit_id, unit)
            return display_name
        return ''

    def get_units(self, override_unit=None):
        # Put parentheses around units (units)
        display_name = self.get_default_unit(override_unit)
        if display_name:
            return ('(' + display_name + ')')
        return display_name

    def is_valid_unit(self, unit):
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(self.form_type)
        if form_type_unit_id and display_result_unit(form_type_unit_id):
            return is_valid_unit(form_type_unit_id, unit)
        return False

    def fully_qualified_label_results(self):
        ret = self.body_qualified_label_results()
        if ret is None: # pragma: no cover
            return None
        units = self.get_units()
        if units != '':
            ret += ' '+units
        return ret

    def is_string(self):
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(self.form_type)
        return form_type == 'STRING'

    def is_string_or_mult(self):
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(self.form_type)
        return form_type == 'STRING' or form_type in settings.MULT_FORM_TYPES

    def get_ranges_info(self):
        """
        Get the ranges info except units & qtype
        """
        ranges = {}
        if self.ranges:
            ranges = json.loads(self.ranges)
        return ranges
