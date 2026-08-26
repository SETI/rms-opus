"""The Django form behind the Search tab's widgets.

A widget is built from the slugs it covers: each slug's `param_info` row says how
that field is searched, and the form grows the inputs that go with it.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django import forms
from django.apps import apps
from django.conf import settings

from opus_app.apps.search.views import get_param_info_by_slug, is_single_column_range
from opus_app.apps.tools.app_utils import get_mult_name, get_numeric_suffix, strip_numeric_suffix
from opus_support import parse_form_type

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

log = logging.getLogger(__name__)


class MultiFloatField(forms.Field):
    """The field a range endpoint's input is built from.

    It adds nothing to `django.forms.Field`; everything that makes the input a range
    endpoint comes from the widget the field is given.
    """

    pass

class SearchForm(forms.Form):
    """The search inputs for the fields named by a mapping of slug to value.

    Each slug's `param_info` row says how its field is searched, and the matching
    text input, range endpoint, dropdown or checkbox group is added to the form
    under that slug. A text field also gets the qtype dropdown that goes beside it,
    and so does a range field whose two endpoints are separate columns.
    """
    def __init__(self, form_vals: Mapping[str, Any], *args: Any, **kwargs: Any) -> None:
        """Build the inputs for every slug in the mapping.

        Where the last slug built was a range endpoint, the form is then reduced to
        that field's two endpoints, in min then max order, followed by its qtype
        dropdown if it has one.

        Parameters:
            form_vals: The initial value for each field to build, keyed by slug.
                It is also what the form is bound to, so it is what
                `django.forms.Form` reads its data from.
            *args: Passed on to `django.forms.Form`.
            **kwargs: Passed on to `django.forms.Form`, except `grouping`, which
                selects the group of mult values to offer for a mult field.
        """
        grouping = kwargs.pop('grouping', None)
        super().__init__(form_vals, *args, **kwargs)

        for slug in form_vals:
            param_info = get_param_info_by_slug(slug, 'search')
            # Everything below dereferences param_info unconditionally, so a slug
            # that names no field is a fault rather than an input case. The one
            # caller resolves each slug before it builds the mapping.
            assert param_info is not None
            (form_type, _form_type_format,
             _form_type_unit_id) = parse_form_type(param_info.form_type)

            if form_type == 'STRING':
                choices: Iterable[tuple[str, str]] = ((x,x) for x in settings.STRING_QTYPES)
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
                    # The same reliance as above: the hints of the field's other
                    # endpoint are read without checking that it was found.
                    assert pi_slug1 is not None
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
