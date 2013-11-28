from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse    


class Group(models.Model):
    """  
    Param Groups
    
    the search interface has tons of params that can be searched, 
    so we divide them into groups, and divide each group into categories
    
    """
    name = models.CharField(max_length=150, blank=True)
    display = models.BooleanField(default=True)
    disp_order = models.IntegerField(blank=True, null=True)
    alert = models.TextField(blank=True, null=True)  

    class Meta:
        db_table = u'groups'
        ordering = ('disp_order',)

    def __unicode__(self):
        return self.name        



class Category(models.Model):     
    """
    Param Categories
    
    the search interface has tons of params that can be searched, 
    so we divide them into groups, and divide each group into categories
    
    """
    name = models.CharField(max_length=150, blank=True)
    label = models.CharField(max_length=108, blank=True)
    display = models.BooleanField(default=True)
    disp_order = models.IntegerField(blank=True, null=True)
    alert = models.TextField(blank=True, null=True)  
    group = models.ForeignKey(Group, blank=True, null = True)
    # group = models.ForeignKey(Groups, related_name="groups", blank=True, null = True)
    
    class Meta:
        db_table = u'categories' 
        ordering = ('disp_order',)

    def __unicode__(self):
        return self.name
        
                                
RANK_CHOICES = (('0','Advanced'),('1','Basic'))
      
class ParamInfo(models.Model):   
    """  
    This model describes every searchable param in the database (aka fields in the Observations model)
    each has attributes like display, display order, query type, slug, etc..
     
    A word about the mission and instrument fields: these are very important fields because
    they describe parameters are grouped in the data query string. 
    
    We allow for searching accross different missions and instrument (ie: show me all 
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
    category = models.ForeignKey(Category, blank=True, null = True)
    name = models.CharField(max_length=87)
    type = models.CharField(max_length=18, blank=True)
    length = models.IntegerField()
    slug = models.CharField(max_length=255, blank=True, null=True)
    post_length = models.IntegerField()
    form_type = models.CharField(max_length=21, blank=True, null = True)
    display = models.BooleanField()
    rank = models.CharField(max_length=48, blank=True, null=True, choices = RANK_CHOICES)
    disp_order = models.IntegerField()
    label = models.CharField(max_length=240, blank=True, null = True)
    intro = models.CharField(max_length=150, blank=True, null = True)
    category_name = models.CharField(max_length=150, blank=True)
    display_results = models.BooleanField()
    units = models.CharField(max_length=75, blank=True, null = True)
    tooltip = models.CharField(max_length=255, blank=True, null = True)
    dict_context = models.CharField(max_length=255, blank=True, null = True)
    dict_name = models.CharField(max_length=255, blank=True, null = True)
    checkbox_group_col_count = models.IntegerField(null=True, blank=True)
    special_query = models.CharField(max_length=15, blank=True, null = True)
    label_results = models.CharField(max_length=240, blank=True, null = True)
    onclick = models.CharField(max_length=75, blank=True, null = True)
    dict_more_info_context = models.CharField(max_length=255, blank=True, null = True)
    dict_more_info_name = models.CharField(max_length=255, blank=True, null = True)
    search_form = models.CharField(max_length=63, blank=True, null = True)
    mission = models.CharField(max_length=15, blank=True, null = True)
    instrument = models.CharField(max_length=15, blank=True, null = True)  
    sub_heading = models.CharField(max_length=150, blank=True, null = True)  
    # related_table_name = models.CharField(max_length=42, blank=True, null = True)
    # related_table_field_name = models.CharField(max_length=25, blank=True, null = True)
    
    
#    group = models.ForeignKey("Groups", blank=True, null = True)
                     
    class Meta:
        db_table = u'param_info'    
        ordering = ('disp_order',)

    def __unicode__(self):
        return u"%s" % self.name       
    
    # http://djangosnippets.org/snippets/2057/                           
    def save(self, *args, **kwargs):
        model = self.__class__
        # model.objects.update(group)

        if self.disp_order is None:
            # Append
            try:
                last = model.objects.order_by('-disp_order')[0]
                self.disp_order = last.disp_order + 1
            except IndexError:
                # First row
                self.disp_order = 0

        return super(ParamInfo, self).save(*args, **kwargs)
                                                               

    