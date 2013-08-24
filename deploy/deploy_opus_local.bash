git push
cd ~/
rm -rf ~/opus
git clone git@bitbucket.org:ringsnode/opus-2.git
mv opus-2 opus
# python opus/deploy/deploy.py
rsync -r -vc -e ssh --exclude .git --exclude static_media opus lballard@pds-rings-tools.seti.org:~/.
