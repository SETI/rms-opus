from django import forms
from metadata.views import *
from django.db.models import get_model
from paraminfo.models import *
from tools.app_utils import *
import settings

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

        if not value: return

        for num in value:
            try:    float(num)
            except: raise forms.ValidationError("value must be a number: " + num[0:20] + '...')


class MultiTimeField(forms.Field):

    # forms.Field.blank=True

    def validate(self, value):
        # Use the parent's handling of required fields, etc.
        super(MultiFloatField(blank=True), self).validate(value)

        for num in value:
            try:    float(num)
            except: raise forms.ValidationError("value must be a number: " + num[0:20] + '...')


class SearchForm(forms.Form):
    """
    problem:
    this only uses default form type, we want to pass in user defined form types,
    qtypes gets played here!

    >>>> from opus.search.forms import *
    >>>> auto_id = False
    >>>> slug1 = 'planet'
    >>>> slug2 = 'target'
    >>>> form_vals = { slug1:None, slug2:None }
    >>>> SearchForm(form_vals, auto_id=auto_id).as_ul()

    """
    def __init__(self, *args, **kwargs):
        grouped = True if 'grouping' in kwargs else False # for the grouping of mult widgets
        grouping = kwargs.pop('grouping', None) # this is how you pass kwargs to the form class, yay!
        super(SearchForm, self).__init__(*args, **kwargs)

        # this makes getMultName() below not choke, circular import issue? not sure..but this fixes
        from opus.metadata.views import getMultName

        for slug,values in args[0].items():
            try:
                form_type = ParamInfo.objects.get(slug=slug).form_type
            except ParamInfo.DoesNotExist:
                continue    # this is not a query param, probably a qtype, move along

            if form_type == 'STRING':
                choices =  (('contains','contains'),('begins','begins'),('ends','ends'),('matches','matches'),('excludes','excludes'))
                self.fields[slug] = forms.CharField(
                    widget = forms.TextInput(
                    attrs={'class':'STRING', 'size':'50', 'tabindex':0}),
                    required=False,
                    label = '')
                self.fields['qtype-'+slug] = forms.CharField(
                     required=False,
                     label = '',
                     widget=forms.Select(
                        choices=choices,
                        attrs={'tabindex':0}
                     ),
                )

            if form_type in settings.RANGE_FIELDS:
                choices =  (('any','any'),('all','all'),('only','only'))
                slug_no_num = stripNumericSuffix(slug)
                num = getNumericSuffix(slug)
                label = 'min' if num == '1' else 'max'
                self.fields[slug] = MultiFloatField(
                     required=False,
                     label = label,
                     widget = forms.TextInput(attrs={'class':label}),
                )
                self.fields['qtype-'+slug_no_num] = forms.CharField(
                     required=False,
                     label = '',
                     widget=forms.Select(
                        choices=choices,
                        attrs={'tabindex':0}
                     ),
                )
                self.fields.keyOrder = [slug_no_num+'1', slug_no_num+'2', 'qtype-'+slug_no_num]  # makes sure min is first! boo ya!

            elif form_type in settings.MULT_FIELDS:
                #self.fields[slug]= MultiStringField(forms.Field)
                param_name = ParamInfo.objects.get(slug=slug).name
                mult_param = getMultName(param_name)
                model      = get_model('search',mult_param.title().replace('_',''))

                #grouped mult fields:
                if grouped:
                    choices = [(mult.label, mult.label) for mult in model.objects.filter(grouping=grouping)]
                else:
                    choices = [(mult.label, mult.label) for mult in model.objects.all()]

                self.fields[slug] = forms.MultipleChoiceField(
                        # label = ParamInfo.objects.get(slug=slug).label,
                        label = '',
                        choices = choices,
                        widget = forms.CheckboxSelectMultiple(attrs={'class':'multichoice'}),
                        required=False)


"""
class SearchForm(forms.Form):
    #planet_id = forms.CharField(required=False, validators=[MultiStringField])
    #planet_id = forms.MultipleChoiceField(required=False, widget = forms.CheckboxSelectMultiple(choices = ((5,'Jupiter'),(6,'Saturn')) ), validators=[MultiStringField])
    planet_id = MultiStringField(forms.Field)
    planet_id = forms.MultipleChoiceField(
                    label = 'planet',
                    #queryset=MultPlanetId.objects.all(),
                    choices = [('', '----------')] + [(mult.label, mult.label) for mult in MultPlanetId.objects.all()],
                    widget = forms.CheckboxSelectMultiple(attrs={'class':'multichoice'}),
                    required=False)

    ring_radius1 = MultiFloatField(required=False)
    ring_radius2 = MultiFloatField(required=False)

"""