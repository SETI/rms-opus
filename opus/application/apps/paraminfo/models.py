from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from dictionary.views import get_def_for_tooltip, get_more_info_url

import logging
log = logging.getLogger(__name__)

RANK_CHOICES = (('0','Advanced'),('1','Basic'))

class ParamInfo(models.Model):
    """
    This model describes every searchable param in the database
    each has attributes like display, display order, query type, slug, etc..

    pretty sure this is deprecated:
    We provide searching accross different missions and instrument (ie: show me all
    Observations of the A ring where Voyager ISS was using the red filter and Cassini ISS
    was using a violet filter). This wouldn't work in a traditional relational database
    (you can't have an Observation that is *both* taken using the Cassini ISS and Voyager ISS)

    To acheive this we tag each parameter with 'mission' or 'instrument' if the field is
    specific to one of those datasets, and the query builder >>> insert model here <<< groups
    them appropriately to get all the data

    following our example above, the query issued would look like this:

    select observations.name from observations where
    (planet='Saturn' and target='A ring' and instrument = 'VGISS' and filter = "red")
    union
    (planet='Saturn' and target='A ring' and instrument = 'COISS' and filter = "violet")

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
    intro = models.CharField(max_length=150, blank=True, null=True)
    tooltip = models.CharField(max_length=255, blank=True, null=True)
    dict_context = models.CharField(max_length=255, blank=True, null=True)
    dict_name = models.CharField(max_length=255, blank=True, null=True)
    special_query = models.CharField(max_length=15, blank=True, null=True)
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
