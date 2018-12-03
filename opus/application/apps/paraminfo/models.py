from django.db import models
from dictionary.views import get_def_for_tooltip

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

    def param_name(self):
        return self.category_name + '.' + self.name

    def get_tooltip(self):
        definition = get_def_for_tooltip(self.dict_name, self.dict_context)
        return definition

    def body_qualified_label(self):
        # Appended "- Ring" or "- <Surface Body>"
        append_to_label = None

        if 'obs_surface_geometry__' in self.category_name:
            # append the target name to surface geo widget labels
            try:
                append_to_label = self.category_name.split('__')[1].title()
            except KeyError:
                pass
        elif 'obs_ring_geometry' in self.category_name:
            append_to_label = 'Ring'

        if append_to_label:
            return self.label + ' [' + append_to_label + ']'
        else:
            return self.label

    def body_qualified_label_results(self):
        # Appended "- Ring" or "- <Surface Body>"
        append_to_label = None

        if 'obs_surface_geometry__' in self.category_name:
            # append the target name to surface geo widget labels
            try:
                append_to_label = self.category_name.split('__')[1].title()
            except KeyError:
                pass
        elif 'obs_ring_geometry' in self.category_name:
            append_to_label = 'Ring'

        if append_to_label:
            return self.label_results + ' [' + append_to_label + ']'
        else:
            return self.label_results

    def get_units(self):
        # put parenthesis around units (units)
        if self.units:
            return '(' + self.units + ')'
        else:
            return self.units
