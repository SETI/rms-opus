# The procedure is for deploy OPUS code base to production

if you are instead looking to update the OPUS database with new data, see import/README.md

lots of this will all be moved to fabric files.


locally, push code to remote repo on Bitbucket, check it out at ~/. (anything but dev dir)

```
git push
```

then rsync to ~/. on server (not production dir) (this way cuz couldn't clone bitbucket from server)

```
bash deploy/deploy_opus_local.bash
```

take backup of production

```
rsync -r -vc /home/django/djcode/opus ~/backups/.

```


on the server move to production:

```
sudo rsync -r -vc ~/opus /home/django/djcode/.
```



rsync -r -vc -e ~/opus /home/django/djcode/.


then on pds-tools: **NOTE: this assumes the latest stable of search/models.py lives at ~/opus on the server, it will fetch the model from there and deploy it to production!!!


deploy static assets to s3 if needed (or see next)

```
python manage.py collectstatic
```

you can deploy one-off static files with s3cmd instead of collectstatic, for example:

```
s3cmd put static_media/js/browse.js s3://opus-static/js/.
```

then on server copy to production?
same rsync?

don't forget to tell Apache you've updated the code:

```
sudo touch *.wsgi
```

To deploy, be sure and reset the memcached, kill what is currently running then
issue the same commands again, find them like so:

```
ps aux | grep memcache
```


## The End.




background:

deploy/deploy_opus_local.bash:
push the opus repo, change to a new directory, clone the remote repo, rsync the directory to staging
git push
cd ~/
rm -rf ~/opus
git clone git@bitbucket.org:ringsnode/opus2.git
mv opus2 opus
python opus/deploy/deploy.py
rsync -r -vc -e ssh --exclude .git --exclude static_media opus lballard@pds-rings-tools.seti.org:~/.



deploy_opus.bash:
backup_filename="opus_`eval date +%Y%m%d.%H.%m.%s`"
cp -r [DJANGO_DIR/opus] [BACKUP_DIR]/$backup_filename
sudo cp -r opus /home/django/djcode/.
sudo touch /home/django/djcode/opus/apache/mod.wsgi
sudo touch /home/django/djcode/opus/mod.wsgi
echo "opus directory copied to  /home/django/djcode/."
echo "touched mod.wsgi"




