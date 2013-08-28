# Once you deploy a database to OPUS 1 this procedure will magically update OPUS 2 with the same data.

http://localhost/wikka/wikka.php?wakka=Opus2Import

# take a backup
```
mysqldump --opt opus > opus.sql -p
```

# make back up copies of a few utility tables
```
mysql opus < backup_util_tables.sql -p -v
```

# first rsync local to pds-tools at ~/lballard/opus
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
