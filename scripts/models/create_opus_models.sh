#!/bin/sh
# Run from the repository root, against a fully imported database.
rm -f /tmp/_*models.py
python manage.py inspectdb > /tmp/_models.py
if [ `grep Cache /tmp/_models.py | wc -l` -ne 0 ]
then
  echo "Must clear out caches before running!"
else
  # Now hide all the new classes because there might be tables in the DB
  # we don't want to expose models for
  sed -e 's/^class /class ZZ/' < /tmp/_models.py > /tmp/___models.py
  # Then unhide the ones we actually want
  sed -e 's/^class ZZ\(Mult\|Obs\|Partables\|TableNames\|UserSearches\)/class \1/' < /tmp/___models.py > /tmp/__models.py
  # The dictionary Contexts is still handing around badly
  sed -e 's/Contexts,/ZZContexts,/' < /tmp/__models.py > /tmp/_models.py
  # Fix up problems with opus_id, where Django deletes the _id on the end for some reason
  sed -e 's/opus =/opus_id =/' < /tmp/_models.py > /tmp/__models.py
  sed -e "s/opus_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING)/opus_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_opus_id', db_column='opus_id')/g" < /tmp/__models.py > /tmp/_models.py
  sed -e "s/opus_id = models.ForeignKey('ObsGeneral', models.DO_NOTHING)/opus_id = models.ForeignKey('ObsGeneral', models.DO_NOTHING, related_name='%(class)s_opus_id', db_column='opus_id')/g" < /tmp/_models.py > /tmp/__models.py
  sed -e "s/obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)/obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_general_id', db_column='obs_general_id')/g" < /tmp/__models.py > /tmp/_models.py
  sed -e "s/obs_general = models.ForeignKey('ObsGeneral', models.DO_NOTHING)/obs_general = models.ForeignKey('ObsGeneral', models.DO_NOTHING, related_name='%(class)s_general_id', db_column='obs_general_id')/g" < /tmp/_models.py > /tmp/__models.py
  # Then get rid of any Auth or Django tables that are left
  sed -e "s/'Django/'ZZDjango/g" < /tmp/__models.py | sed -e "s/'Auth/'ZZAuth/g" | sed -e "s/(Auth/(ZZAuth/g" > src/opus_app/apps/search/models.py
  # inspectdb emits one long line per field, so the raw output is unreadable and
  # every regeneration diff is unreviewable. The generator is the only durable
  # place to fix that: a hand-edit to the output is destroyed by the next run.
  # The file is excluded from `ruff check` (see [tool.ruff] exclude in
  # pyproject.toml), but ruff honours an explicitly named path regardless of the
  # exclusion, so this formats it.
  ruff format src/opus_app/apps/search/models.py
fi
