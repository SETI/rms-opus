import settings
from django.apps import apps
from django import forms
from search.views import get_param_info_by_slug, is_single_column_range
from tools.app_utils import (get_mult_name,
                             get_numeric_suffix,
                             strip_numeric_suffix)

from opus_support import parse_form_type

import logging
log = logging.getLogger(__name__)


class MultiFloatField(forms.Field):
    pass

class SearchForm(forms.Form):
    """
    >>>> from search.forms import *
    >>>> auto_id = False
    >>>> slug1 = 'planet'
    >>>> slug2 = 'target'
    >>>> form_vals = { slug1:None, slug2:None }
    >>>> SearchForm(form_vals, auto_id=auto_id).as_ul()

    """
    def __init__(self, form_vals, *args, **kwargs):
        grouping = kwargs.pop('grouping', None)
        super(SearchForm, self).__init__(form_vals, *args, **kwargs)

        for slug in form_vals:
            param_info = get_param_info_by_slug(slug, 'search')
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
                        attrs={'tabindex': 0, 'class': 'STRING'}
                     ),
                )

            if form_type in settings.RANGE_FORM_TYPES:
                choices = ((x,x) for x in settings.RANGE_QTYPES)
                slug_no_num = strip_numeric_suffix(slug)
                num = get_numeric_suffix(slug)

                label = 'max' if num == '2' else 'min'

                # placeholder for input hints (only apply to Min input for now)
                if num == '2':
                    # Get the hints for slug2 from slug1 field in database
                    pi_slug1 = get_param_info_by_slug(slug[:-1] + '1', 'search')
                    hints = pi_slug1.field_hints2 if pi_slug1.field_hints2 else ''
                else:
                    hints = param_info.field_hints1 if param_info.field_hints1 else ''

                # dropdown only available when ranges info is available
                ranges = param_info.get_ranges_info()
                dropdown_class = ('op-ranges-dropdown-menu dropdown-toggle'
                                  if ranges else '')
                data_toggle = 'dropdown' if ranges else ''

                self.fields[slug] = MultiFloatField(
                    required=False,
                    label=label.capitalize(),
                    widget=forms.TextInput(
                        attrs={
                            'class': 'op-range-input-'+label+' RANGE '+dropdown_class,
                            'placeholder': hints,
                            'autocomplete': 'off',
                            'data-slugname': slug_no_num,
                            'data-bs-toggle': data_toggle,
                            'aria-haspopup': 'true',
                            'aria-expanded': 'false'
                        }
                    ),
                )
                # Make sure order is min, max
                if not is_single_column_range(param_info.param_qualified_name()):
                    self.fields['qtype-'+slug_no_num] = forms.CharField(
                        required=False,
                        label='',
                        widget=forms.Select(
                            choices=choices,
                            attrs={'tabindex': 0, 'class': 'RANGE'}
                        ),
                    )
                    self.field_order = [slug_no_num+'1', slug_no_num+'2',
                                        'qtype-'+slug_no_num]
                else:
                    self.field_order = [slug_no_num+'1', slug_no_num+'2']

            elif form_type in settings.MULT_FORM_TYPES:
                param_qualified_name = param_info.param_qualified_name()
                mult_param = get_mult_name(param_qualified_name)
                model = apps.get_model('search', mult_param.title().replace('_',''))

                # grouped mult fields
                choices = [(mult.label, mult.label) for mult in
                               model.objects
                               .filter(grouping=grouping, display='Y')
                               .order_by('disp_order')]

                if param_qualified_name == 'obs_surface_geometry_name.target_name':
                    self.fields[slug] = forms.CharField(
                            label='',
                            widget=forms.RadioSelect(attrs={'class': 'singlechoice'},
                                                     choices=choices),
                            required=False)
                else:
                    self.fields[slug] = forms.CharField(
                            label='',
                            widget=forms.CheckboxSelectMultiple(attrs={'class': 'multichoice'},
                                                                choices=choices),
                            required=False)

        if form_type in settings.RANGE_FORM_TYPES:
            my_fields = self.fields
            self.fields = {}
            self.fields[slug_no_num+'1'] = my_fields[slug_no_num+'1']
            self.fields[slug_no_num+'2'] = my_fields[slug_no_num+'2']
            if 'qtype-'+slug_no_num in my_fields:
                self.fields['qtype-'+slug_no_num] = my_fields['qtype-'+slug_no_num]
