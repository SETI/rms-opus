"""The `param_info` table, which describes every field OPUS can search or display.

One row per field of the observation tables. The model's methods are what the
interface asks for a field's label, its tooltip and its units, so a template can
render a field without knowing anything else about it.
"""

import json
from typing import Any

from django.conf import settings
from django.db import models

from opus_app.apps.search.models import TableNames
from opus_app.apps.tools.dictionary import get_def_for_tooltip
from opus_support import (
    display_result_unit,
    get_default_unit,
    get_unit_display_name,
    is_valid_unit,
    parse_form_type,
)


class ParamInfo(models.Model):
    """One searchable or displayable field, as the `param_info` table describes it.

    A row carries what the interface needs to present one column of one observation
    table: the category and name that identify it, how it is searched (`form_type`),
    the slug it is named by in the API, its display flags and ordering, the labels
    and dictionary tooltips shown for it, and the ranges offered for it.
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
        """Model options: the table the rows come from, and the order they come in."""

        db_table = ('param_info')
        ordering = ('category_name', 'sub_heading', 'disp_order')

    def __unicode__(self) -> str:
        """Return the field's column name."""
        return f"{self.name}"

    def param_qualified_name(self) -> str:
        """Return the field's category and column name, joined by a period.

        Returns:
            The name that identifies this field across all the observation tables,
            such as `obs_general.instrument_id`.
        """
        return self.category_name + '.' + self.name

    def get_tooltip(self) -> str | None:
        """Return the dictionary definition shown as this field's tooltip.

        Returns:
            The definition of the field's dictionary term, or None when the term is
            not defined.
        """
        definition = get_def_for_tooltip(self.dict_name, self.dict_context)
        return definition

    def get_tooltip_results(self) -> str | None:
        """Return the dictionary definition shown as this field's results tooltip.

        Returns:
            The definition of the field's results dictionary term, falling back to
            the term used for its search tooltip when it names no separate one, or
            None when the term is not defined.
        """
        if self.dict_name_results:
            definition = get_def_for_tooltip(self.dict_name_results,
                                             self.dict_context_results)
        else:
            definition = get_def_for_tooltip(self.dict_name, self.dict_context)
        return definition

    def get_link_tooltip(self) -> str:
        """Return the tooltip shown for a field that only links to another one.

        Returns:
            A sentence naming the category the field is really part of.

        Raises:
            TableNames.DoesNotExist: If no table is registered under the field's
                category name.
        """
        table_label = (TableNames.objects
                      .get(table_name=self.category_name).label)
        return (f'This field is a link to one available under {table_label}. '+
                'It is provided here for your convenience.')

    def body_qualified_label(self) -> str | None:
        """Return the field's search label with the body it describes appended.

        A geometry or mission field is one of many with the same label, so the body,
        mission or instrument its category names is appended in brackets. Nothing is
        appended for the surface-geometry category, whose body is chosen by the user
        rather than fixed, or to a label that already carries the bracketed name.

        Returns:
            The label to show for the field on the Search tab.

        Raises:
            TableNames.DoesNotExist: If no table is registered under the field's
                category name.
        """
        # Append "[Ring]" or "[<Surface Body>]" or "[Mission]" or "[Instrument]"
        pretty_name = (TableNames.objects
                       .get(table_name=self.category_name).label)
        pretty_name = pretty_name.replace(' Surface Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Geometry Constraints', '')
        pretty_name = pretty_name.replace(' Mission Constraints', '')
        pretty_name = pretty_name.replace(' Constraints', '')

        # `label` is nullable in param_info, and a row that leaves it unset raises
        # TypeError on both lines below rather than being handled the way
        # body_qualified_label_results handles a missing label_results. That is a
        # real fault rather than a typing artifact, so it is recorded here instead of
        # being annotated away.
        if (pretty_name == 'Surface' or
            f'[{pretty_name}]' in self.label): # type: ignore[operator]
            return self.label
        return self.label + ' [' + pretty_name + ']' # type: ignore[operator]

    def body_qualified_label_results(self, referred: bool = False) -> str | None:
        """Return the field's results label with the body it describes appended.

        This is `body_qualified_label` for the label shown beside a result: the
        body, mission or instrument the field's category names is appended in
        brackets. Nothing is appended for the categories that describe an
        observation as a whole, unless the field is reached through another field's
        referred slug, nor to a label that already carries the bracketed name.

        Parameters:
            referred: True when the label is for a field reached through another
                field's referred slug, which is named in full even in the categories
                that are otherwise left alone.

        Returns:
            The label to show beside a result, or None when the field has no results
            label at all.

        Raises:
            TableNames.DoesNotExist: If no table is registered under the field's
                category name.
        """
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

    def get_default_unit(self, override_unit: str | None = None) -> str | None:
        """Return the display name of the unit this field's results are shown in.

        Parameters:
            override_unit: A unit to describe instead of the field's own default.

        Returns:
            The name shown for the unit, the empty string for a field whose values
            carry no unit or whose unit is never shown beside a result, or None for
            a unit that has no display name.

        Raises:
            KeyError: If `override_unit` is not a unit of this field's unit system.
        """
        (_form_type, _form_type_format,
         form_type_unit_id) = parse_form_type(self.form_type)
        if form_type_unit_id and display_result_unit(form_type_unit_id):
            if override_unit:
                unit = override_unit
            else:
                # get_default_unit returns None only for a None unit_id, which the
                # test above has already excluded.
                unit = get_default_unit(form_type_unit_id) # type: ignore[assignment]
            display_name = get_unit_display_name(form_type_unit_id, unit)
            return display_name
        return ''

    def get_units(self, override_unit: str | None = None) -> str | None:
        """Return the display name of this field's unit, in parentheses.

        Parameters:
            override_unit: A unit to describe instead of the field's own default.

        Returns:
            The unit's display name wrapped in parentheses, or whatever
            `get_default_unit` gave back when there is no name to wrap.

        Raises:
            KeyError: If `override_unit` is not a unit of this field's unit system.
        """
        # Put parentheses around units (units)
        display_name = self.get_default_unit(override_unit)
        if display_name:
            return ('(' + display_name + ')')
        return display_name

    def is_valid_unit(self, unit: str) -> bool:
        """Check whether a unit is one this field's results can be shown in.

        Parameters:
            unit: The unit name to check, in any case.

        Returns:
            True if the field's values carry a unit that is shown beside a result
            and `unit` names one of that system's units.
        """
        (_form_type, _form_type_format,
         form_type_unit_id) = parse_form_type(self.form_type)
        if form_type_unit_id and display_result_unit(form_type_unit_id):
            return is_valid_unit(form_type_unit_id, unit)
        return False

    def fully_qualified_label_results(self) -> str | None:
        """Return the field's results label with its body and its units appended.

        Returns:
            The label `body_qualified_label_results` gives, followed by the units in
            parentheses when the field has any.
        """
        ret = self.body_qualified_label_results()
        units = self.get_units()
        # Both halves are nullable: a field with no results label, and a unit with
        # no display name, each reach this line as None and raise TypeError. That is
        # a real fault rather than a typing artifact, so it is recorded here instead
        # of being annotated away.
        if units != '':
            ret += ' '+units # type: ignore[operator]
        return ret

    def is_string(self) -> bool:
        """Check whether this field is searched as free text.

        Returns:
            True if the field's form type is `STRING`.
        """
        (form_type, _form_type_format,
         _form_type_unit_id) = parse_form_type(self.form_type)
        return form_type == 'STRING'

    def is_string_or_mult(self) -> bool:
        """Check whether this field is searched as free text or by choosing values.

        Returns:
            True if the field's form type is `STRING` or one of the mult form types.
        """
        (form_type, _form_type_format,
         _form_type_unit_id) = parse_form_type(self.form_type)
        return form_type == 'STRING' or form_type in settings.MULT_FORM_TYPES

    def get_ranges_info(self) -> dict[str, Any]:
        """Get the ranges info except units & qtype.

        Returns:
            The ranges the Search tab offers for this field, decoded from the
            field's `ranges` column, or an empty dict when it holds nothing.
        """
        ranges: dict[str, Any] = {}
        if self.ranges:
            ranges = json.loads(self.ranges)
        return ranges
