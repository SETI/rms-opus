# Deploy OPUS code base to pds-tools:

local:

git push
bash deploy/deploy_opus_local.bash

then on pds-tools:
sudo bash deploy_opus.bash

# deploy static files to s3:
python manage.py collectstatic

# you can deploy one-off static files with s3cmd instead of collectstatic, for example:
s3cmd put static_media/js/browse.js s3://opus-static/js/.

# to tell Apache you've done that use:
sudo touch *.wsgi

# The End.




# background:

# deploy/deploy_opus_local.bash:
cd ~/
rm -rf ~/opus
git clone git@bitbucket.org:ringsnode/opus-2.git
mv opus-2 opus
python opus/deploy/deploy.py
rsync -r -vc -e ssh opus lballard@pds-rings-tools.seti.org:~/.


# deploy_opus.bash:
backup_filename="opus_`eval date +%Y%m%d.%H.%m.%s`"
cp -r [DJANGO_DIR/opus] [BACKUP_DIR]/$backup_filename
sudo cp -r opus /home/django/djcode/.
sudo touch /home/django/djcode/opus/apache/mod.wsgi
sudo touch /home/django/djcode/opus/mod.wsgi
echo "opus directory copied to  /home/django/djcode/."
echo "touched mod.wsgi"




