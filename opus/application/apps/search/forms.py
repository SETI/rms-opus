import settings
from collections import OrderedDict
from django.apps import apps
from django import forms
from search.views import get_param_info_by_slug, is_single_column_range
from paraminfo.models import ParamInfo
from tools.app_utils import (get_mult_name,
                             get_numeric_suffix,
                             strip_numeric_suffix)

from opus_support import parse_form_type

import logging
log = logging.getLogger(__name__)


class MultiStringField(forms.Field):

    def validate(self, value):
        # Use the parent's handling of required fields, etc.
        super(MultiStringField, self).validate(value)

        max_length = 25
        for mult in value:
            if len(mult) > max_length:
                raise forms.ValidationError("string value is too long, limit is " + max_length + ': ' + mult[0:20] + '...')


class MultiFloatField(forms.Field):

    # forms.Field.blank=True

    def validate(self, value):
        # Use the parent's handling of required fields, etc.
        super(MultiFloatField, self).validate(value)

        if not value:
            return

        if type(value).__name__ != 'str':
            value = [value]

        # for num in value:
        #     try:    float(num)
        #     except: raise forms.ValidationError("value must be a number: " + num[0:20] + '...')


class MultiTimeField(forms.Field):

    # forms.Field.blank=True

    def validate(self, value):
        # Use the parent's handling of required fields, etc.
        super(MultiFloatField(blank=True), self).validate(value)

        for num in value:
            try:
                float(num)
            except:
                raise forms.ValidationError("value must be a number: " + num[0:20] + '...')


class SearchForm(forms.Form):
    """
    >>>> from search.forms import *
    >>>> auto_id = False
    >>>> slug1 = 'planet'
    >>>> slug2 = 'target'
    >>>> form_vals = { slug1:None, slug2:None }
    >>>> SearchForm(form_vals, auto_id=auto_id).as_ul()

    """
    def __init__(self, *args, **kwargs):
        grouped = 'grouping' in kwargs # for the grouping of mult widgets
        grouping = kwargs.pop('grouping', None) # this is how you pass kwargs to the form class, yay!
        super(SearchForm, self).__init__(*args, **kwargs)

        for slug,values in args[0].items():
            if slug.startswith('qtype-'):
                continue
            param_info = get_param_info_by_slug(slug, 'search')

            if not param_info:
                log.error(
                    "SearchForm: Could not find param_info entry for slug %s",
                    str(slug))
                continue  # todo this should raise end user error

            try:
                form_type = param_info.form_type
            except ParamInfo.DoesNotExist:
                continue    # this is not a query param, probably a qtype, move along

            (form_type, form_type_format,
             form_type_unit_id) = parse_form_type(param_info.form_type)

            if form_type == 'STRING':
                choices = ((x,x) for x in settings.STRING_QTYPES)
                self.fields[slug] = forms.CharField(
                    widget=forms.TextInput(
                        attrs={'class': 'STRING',
                               'size': '50',
                               'tabindex': 0,
                               'data-slugname': slug
                               }),
                    required=False,
                    label='')
                self.fields['qtype-'+slug] = forms.CharField(
                     required=False,
                     label='',
                     widget=forms.Select(
                        choices=choices,
                        attrs={'tabindex':0, 'class':'STRING'}
                     ),
                )

            if form_type in settings.RANGE_FORM_TYPES:
                choices = ((x,x) for x in settings.RANGE_QTYPES)
                slug_no_num = strip_numeric_suffix(slug)
                num = get_numeric_suffix(slug)
                if not num:
                    slug = slug + '1'

                label = 'max' if num == '2' else 'min'

                pi = get_param_info_by_slug(slug, 'search')

                # placeholder for input hints (only apply to Min input for now)
                if num == '2':
                    # Get the hints for slug2 from slug1 field in database
                    pi_slug1 = get_param_info_by_slug(slug[:-1] + '1', 'search')
                    hints = pi_slug1.field_hints2 if pi_slug1.field_hints2 else ''
                else:
                    hints = pi.field_hints1 if pi.field_hints1 else ''

                # dropdown only available when ranges info is available
                ranges = pi.get_ranges_info()
                dropdown_class = 'op-ranges-dropdown-menu dropdown-toggle' if ranges else ''
                data_toggle = 'dropdown' if ranges else ''

                self.fields[slug] = MultiFloatField(
                    required=False,
                    label=label.capitalize(),
                    widget=forms.TextInput(
                        attrs={
                            'class': 'op-range-input-' + label + ' RANGE ' + dropdown_class,
                            'placeholder': hints,
                            'autocomplete': 'off',
                            'data-slugname': slug_no_num,
                            'data-toggle': data_toggle,
                            'aria-haspopup': 'true',
                            'aria-expanded': 'false'
                        }
                    ),
                )
                if not is_single_column_range(pi.param_qualified_name()):
                    self.fields['qtype-'+slug_no_num] = forms.CharField(
                        required=False,
                        label='',
                        widget=forms.Select(
                            choices=choices,
                            attrs={'tabindex':0, 'class':"RANGE"}
                        ),
                    )
                    self.field_order = [slug_no_num+'1', slug_no_num+'2', 'qtype-'+slug_no_num]  # makes sure min is first! boo ya!
                else:
                    self.field_order = [slug_no_num+'1', slug_no_num+'2']  # makes sure min is first! boo ya!

            elif form_type in settings.MULT_FORM_TYPES:
                # self.fields[slug]= MultiStringField(forms.Field)
                try:
                    param_qualified_name = ParamInfo.objects.get(slug=slug).param_qualified_name()
                except ParamInfo.DoesNotExist:
                    param_qualified_name = ParamInfo.objects.get(old_slug=slug).param_qualified_name()
                except ParamInfo.DoesNotExist:
                    continue # XXX
                mult_param = get_mult_name(param_qualified_name)
                model      = apps.get_model('search',mult_param.title().replace('_',''))

                # grouped mult fields:
                if grouped:
                    choices = [(mult.label, mult.label) for mult in model.objects.filter(grouping=grouping, display='Y').order_by('disp_order')]
                else:
                    choices = [(mult.label, mult.label) for mult in model.objects.filter(display='Y').order_by('disp_order')]

                if param_qualified_name == 'obs_surface_geometry_name.target_name':
                    self.fields[slug] = forms.CharField(
                            # label = ParamInfo.objects.get(slug=slug).label,
                            label='',
                            widget=forms.RadioSelect(attrs={'class':'singlechoice'}, choices=choices),
                            required=False)
                else:
                    self.fields[slug] = forms.CharField(
                            # label = ParamInfo.objects.get(slug=slug).label,
                            label='',
                            widget=forms.CheckboxSelectMultiple(attrs={'class':'multichoice'}, choices=choices),
                            required=False)

        # XXX RF - This is awful. It takes the last form_type from the above loop, but
        # is it possible the loop went more than once??

        # hack to get range fields into the right orde since after Django 1.7 this is deprecated:
        # self.fields.keyOrder = [slug_no_num+'1', slug_no_num+'2', 'qtype-'+slug_no_num]  # makes sure min is first! boo ya!
        if form_type in settings.RANGE_FORM_TYPES:
            my_fields = self.fields
            self.fields = OrderedDict()
            self.fields[slug_no_num+'1'] = my_fields[slug_no_num+'1']
            self.fields[slug_no_num+'2'] = my_fields[slug_no_num+'2']
            if 'qtype-'+slug_no_num in my_fields:
                self.fields['qtype-'+slug_no_num] = my_fields['qtype-'+slug_no_num]
