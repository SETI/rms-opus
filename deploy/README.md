# Deploying OPUS code 

These steps are for deploy code changes to remote web servers. For updating OPUS database with new data, see http://github.com/basilleaf/opus_admin


1. Run tests locally, push to server, move files to web root, refresh caches, run tests remotely 

        fab tests_local push deploy cache_reboot tests

2. Run the API Endpoint tests 

        cd ../tests
        source venv/bin/activate
        python api_tests.py  

3. Open some recent blog post pages in a browser, or other queries you want to be fast for other users.

        open http://ringsnodesearchtool.blogspot.com/


