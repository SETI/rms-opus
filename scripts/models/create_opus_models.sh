#!/bin/sh
# Run from the repository root, against a fully imported database.
rm -f /tmp/_*models.py
python manage.py inspectdb > /tmp/_models.py
# Now hide all the new classes because there might be tables in the DB
# we don't want to expose models for
sed -e 's/^class /class ZZ/' < /tmp/_models.py > /tmp/___models.py
# Then unhide the ones we actually want
sed -e 's/^class ZZ\(Mult\|Obs\|Partables\|TableNames\|UserSearches\)/class \1/' < /tmp/___models.py > /tmp/__models.py
# The dictionary Contexts is still handing around badly
sed -e 's/Contexts,/ZZContexts,/' < /tmp/__models.py > /tmp/_models.py
# Every obs_general_id names its relation to ObsGeneral, so that the many relations
# from one class to ObsGeneral do not clash
sed -e "s/obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)/obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_general_id', db_column='obs_general_id')/g" < /tmp/_models.py > /tmp/__models.py
sed -e "s/obs_general = models.ForeignKey('ObsGeneral', models.DO_NOTHING)/obs_general = models.ForeignKey('ObsGeneral', models.DO_NOTHING, related_name='%(class)s_general_id', db_column='obs_general_id')/g" < /tmp/__models.py > /tmp/_models.py
# A child keyed on obs_general_id holds it as both its primary key and its foreign key,
# which inspectdb writes as a one-to-one field; it names its relation the same way
sed -e "s/obs_general = models.OneToOneField(\('\{0,1\}ObsGeneral'\{0,1\}\), models.DO_NOTHING, primary_key=True)/obs_general = models.OneToOneField(\1, models.DO_NOTHING, primary_key=True, related_name='%(class)s_general_id', db_column='obs_general_id')/g" < /tmp/_models.py > /tmp/__models.py
mv /tmp/__models.py /tmp/_models.py
# inspectdb reads a BINARY column as text; user_searches.search_hash holds a digest's
# bytes, which only a BinaryField returns unaltered
sed -e "s/search_hash = models.CharField(unique=True, max_length=32)/search_hash = models.BinaryField(unique=True, max_length=32)/" < /tmp/_models.py > /tmp/__models.py
# Then get rid of any Auth or Django tables that are left
sed -e "s/'Django/'ZZDjango/g" < /tmp/__models.py | sed -e "s/'Auth/'ZZAuth/g" | sed -e "s/(Auth/(ZZAuth/g" > src/opus_app/apps/search/models.py
# inspectdb emits one long line per field, so the raw output is unreadable and
# every regeneration diff is unreviewable. The generator is the only durable
# place to fix that: a hand-edit to the output is destroyed by the next run.
# The file is excluded from `ruff check` (see [tool.ruff] exclude in
# pyproject.toml), but ruff honours an explicitly named path regardless of the
# exclusion, so this formats it.
ruff format src/opus_app/apps/search/models.py
