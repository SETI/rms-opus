# push the opus repo, change to a new directory, clone the remote repo, rsync the directory to staging
git push
cd ~/
rm -rf ~/opus
rm -rf ~/opus2
git clone git@bitbucket.org:ringsnode/opus2.git
mv opus2 opus
# python opus/deploy/deploy.py
rsync -r -vc -e ssh --exclude .git --exclude static_media opus lballard@pds-rings-tools.seti.org:~/.
