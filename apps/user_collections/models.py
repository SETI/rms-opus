# this is not being used

from django.db import models

class CollectionTable(models.Model):
    opus_id = models.CharField(max_length=60)
    session_id = models.CharField(primary_key=True, max_length=32)

    class Meta:
        managed = False
        db_table = 'collection_table'

    def save(self, *args, **kwargs):
        #check if thing to be saved exists, replace into instead ... or something()
        super(CollectionTable, self).save(*args, **kwargs) # Call the "real" save() method.
