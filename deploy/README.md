## The procedure is for deploy OPUS code base to production

if you are instead looking to update the OPUS database with new data, see import/README.md

lots of this will all be moved to fabric files.

    fab push deploy memcache_reboot

you can also do:

    fab memcache_reboot

 **NOTE: this assumes the latest stable of search/models.py lives at ~/opus on the server, it will fetch the model from there and deploy it to production!!!

deploy static assets to s3 if needed (or see next)

    python ../manage.py collectstatic

you can deploy one-off static files with s3cmd instead of collectstatic, for example:
you might have to fucking 'make public' on s3 if you do this

    s3cmd put static_media/css/main.css s3://opus-static/css/main.css

    s3cmd put static_media/js/widgets.js s3://opus-static/js/widgets.js
    s3cmd put static_media/js/search.js s3://opus-static/js/search.js
    s3cmd put static_media/js/opus.js s3://opus-static/js/opus.js
    s3cmd put static_media/js/browse.js s3://opus-static/js/browse.js
    s3cmd put static_media/js/widgets.js s3://opus-static/js/widgets.js
    s3cmd put static_media/js/hash.js s3://opus-static/js/hash.js
    s3cmd put static_media/js/hash.js s3://opus-static/js/hash.js
    s3cmd put static_media/js/hash.js s3://opus-static/js/hash.js


