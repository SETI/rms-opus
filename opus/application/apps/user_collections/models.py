# this is not being used

from django.db import models

class Collections(models.Model):
    session_id = models.CharField(max_length=80)
    obs_general = models.ForeignKey('search.ObsGeneral', models.DO_NOTHING)
    opus_id = models.CharField(max_length=80)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'collections'
