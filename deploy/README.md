## The procedure is for deploy OPUS code base to production

if you are instead looking to update the OPUS database with new data, see import/README.md

lots of this will all be moved to fabric files.

    fab tests_local push deploy cache_reboot tests_prod

    **NOTE: this assumes the latest stable of search/models.py lives at ~/opus on the server, it will fetch the model from there and deploy it to production!!!

2. The release is now public! (Yes we have no development server) Manually make sure your most recent blog post links are still working.. (todo: script this!)

     open http://ringsnodesearchtool.blogspot.com/

3. Run the in-browser selenium tests

 	they are in Firefox->tools

4. Run the selenium tests:

     In the local repo:

         cd tests
         source venv/bin/activate
         python api_tests.py
