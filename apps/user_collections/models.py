# this is not being used

from django.db import models

# stores all user collection data?
class UserCollectionsTemplate(models.Model):
    ring_obs_id = models.CharField(max_length=40)
    collection_meta=models.ForeignKey("UserCollectionsMeta")

class UserCollectionsMeta(models.Model):
    session_id =  models.CharField(max_length=32, blank=True, null=True)
    product_types = models.TextField(blank=True,null=True)
    extra_products = models.TextField(blank=True,null=True) # like browse images
    timestamp = models.DateTimeField(auto_now=True)

    # last_save = DateField.auto_now_add
