# this is not being used

"""The `cart` table, which records what each session has selected.

A row names the session, the observation it selected, and whether that observation
is in the cart itself or in the session's recycle bin. The table is created by the
import pipeline rather than by a migration, so Django is told not to manage it.
"""

from django.db import models


class Cart(models.Model):
    """One observation held by one session, in its cart or in its recycle bin."""

    session_id = models.CharField(max_length=80)
    obs_general = models.ForeignKey('search.ObsGeneral', models.DO_NOTHING)
    opus_id = models.CharField(max_length=40)
    recycled = models.IntegerField()
    timestamp = models.DateTimeField()

    class Meta:
        """Model options: the table the rows come from, which Django does not manage."""

        managed = False
        db_table = 'cart'
