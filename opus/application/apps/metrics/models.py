from django.db import models

class Metrics(models.Model):
    session_id = models.CharField(max_length=50)
    ip_address = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'metrics'
        unique_together = ('session_id', 'ip_address')