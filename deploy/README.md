## The procedure is for deploy OPUS code base to production

if you are instead looking to update the OPUS database with new data, see import/README.md

lots of this will all be moved to fabric files.

    fab tests_local push deploy cache_reboot tests_prod

 **NOTE: this assumes the latest stable of search/models.py lives at ~/opus on the server, it will fetch the model from there and deploy it to production!!!

