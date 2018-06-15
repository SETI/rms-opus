from django.db import models

"""
def customModelName(request_get):
    name = models.ForeignKey("MultClassId", null=True, blank=True)
    value = models.CharField(max_length=200)
    units = models.CharField(max_length=20)
"""

"""

def customRelatedFileSpecName(request_get):

    opus_id = models.ForeignKey("Observations", null=True, blank=True)
    name = models.ForeignKey("Observations", null=True, blank=True)
    value = models.CharField(max_length=200)
    units = models.CharField(max_length=20)

    def __unicode__(self):
        return self.label

    class Meta:
        db_table = u'custom_related_file_spec_names '

"""
