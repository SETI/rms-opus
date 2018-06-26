# this is not being used

from django.db import models

class Collections(models.Model):
    session_id = models.CharField(max_length=80)
    obs_general_id = models.ForeignKey('ObsGeneral', models.DO_NOTHING)
    opus_id = models.CharField(max_length=80)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'collections'

    def save(self, *args, **kwargs):
        #check if thing to be saved exists, replace into instead ... or something()
        super(Collections, self).save(*args, **kwargs) # Call the "real" save() method.
