## The procedure is for deploy OPUS code base to production

if you are instead looking to update the OPUS database with new data, see import/README.md

lots of this will all be moved to fabric files.

    fab push deploy

you can also do:

    fab memcache_reboot

 **NOTE: this assumes the latest stable of search/models.py lives at ~/opus on the server, it will fetch the model from there and deploy it to production!!!

deploy static assets to s3 if needed (or see next)

    python ../manage.py collectstatic

you can deploy one-off static files with s3cmd instead of collectstatic, for example:

    s3cmd put static_media/js/browse.js s3://opus-static/js/.


