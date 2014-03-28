from django.db import models

# Create your models here.


##############################################
#
#  put grouping models here
#  see opus/README.txt
#
##############################################

class GroupingTargetName(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(unique=True, max_length=50, blank=True, null = True)
    label = models.CharField(unique=True, max_length=50, blank=True, null = True)
    disp_order = models.IntegerField(null=True, blank=True)
    display = models.CharField(max_length=9)
    default_fade = models.CharField(max_length=9)

    def __unicode__(self):
        return self.label

    class Meta:
        db_table = u'grouping_target_name'
