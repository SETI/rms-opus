# Once you deploy a database to OPUS 1 this procedure will magically update OPUS 2 with the same data.

# backup the database
```
mysqldump --opt opus > opus.sql -p
```

# make database backup copies of a few utility tables
```
mysql opus < backup_util_tables.sql -p -v
```

# rsync local to pds-tools at ~/lballard/opus
```
git push
bash deploy/deploy_opus_local.bash
```

# then run the fab file:
```
fab -H lballard@pds-rings-tools.seti.org deploy_opus2:volumes=COISS_2060,NHJULO_1001,COCIRS_5403
or
fab -H lballard@pds-rings-tools.seti.org deploy_opus2:volumes=all

```
The fab file does the following on the server specified on the command line:

1. generates the django models for the 'search' app at search/models.py by reading tables
from OPUS1

2. django uses the search/models.py spec to generate the OPUS2 table schema.

3. rmakes it's own custom text dump of the OPUS1 database

4. imports the text dump into the OPUS2 schema


