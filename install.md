## Installing OPUS Locally

1. Install mysql if necessary

  - Ubuntu:

          sudo apt-get install mysql-server
          sudo apt-get install mysql-client
          sudo apt-get install libmysqlclient-dev

  - Windows:

    Download the installer from https://dev.mysql.com/downloads/windows

* Create the mysql databases

    - Run the mysql command line:

          mysql -p

    - In the mysql command line, create the 3 databases and the opus user:

          # opus databases:  
          create database opus_small;  
          create database dictionary;
          create database opus_metrics;

          # the opus web user:
          create user 'USERNAME'@'localhost' identified by "PASSWORD";  # see secrets_template.py

* Initialize the databases from dump files (ask the Ring-Moon Systems Node for these files)

      mysql opus_small < opus_small.sql -p
      mysql dictionary < dictionary.empty.sql -p
      mysql opus_metrics < opus_metrics.empty.sql -p

* Ubuntu dependencies

  Ubuntu also requires the following package be installed:

      apt-get install libncurses-dev

* Clone the repo

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/<YOUR GITHUB USER NAME>/opus.git  # please fork this repo!  

* Update the pds-tools submodule

        cd opus
        git submodule init
        git submodule update

* Create a virtualenv and install the dependencies

      virtualenv --python=<YOUR PYTHON 2.7 EXECUTABLE> venv

  - Non-Windows:

        source venv/bin/activate
        pip install -r requirements.txt
        pip install -r pds-tools/requirements.txt

  - Windows:

        venv\Scripts\activate
        pip install -r requirements-windows.txt
        pip install -r pds-tools/requirements.txt

    You also need to install the MySQLdb Python package. Unfortunately, installing this under Windows is often difficult. See https://stackoverflow.com/questions/645943/integrating-mysql-with-python-in-windows for suggestions.
    
* Edit the secrets.py file

  - Copy the template:

    - Non-Windows:

          cp secrets_template.py secrets.py

    - Windows:

          copy secrets_template.py secrets.py

  - Change DB_USER to your mysql user
  - Change DB_PASS to your mysql password
  - Change SECRET_KEY to a unique key (generators are available on the web)
  - Change TAR_FILE_PATH to a directory where "shopping cart" tar files can be stored
  - Change FILE_PATH to the location of the Cassini data volumes
  - Change DERIVED_PATH to the location of the Cassini calibrated data volumes
  - Change IMAGE_PATH to the location of the Cassini browse images

    For example:

        FILE_PATH  = '/seti/external/cassini/volumes/COISS_2xxx/'
        DERIVED_PATH  = '/seti/external/cassini/derived/COISS_2xxx/'
        IMAGE_PATH = '/seti/external/cassini/browse/COISS_2xxx/'

* Edit the settings_local.py file

  - Copy the template:

    - Non-Windows:

          cp settings_local_example.py settings_local.py

    - Windows:

          copy settings_local_example.py settings_local.py

  - Be sure to provide the full path to the OPUS Django directory

* Make the logs directory

      mkdir logs

* To run the tests or server for the first time you may need to run migrate (try them first and see):

    - If you are starting with a dump of an opus database, drop the following tables for the migrate to work:

          # in mysql command line:  
          use opus_small;
          drop table django_admin_log;
          drop table django_content_type;
          drop table django_session;
          drop table django_site;

    - then run the migrate command:

          python manage.py migrate

* Run the tests

    - the tests run against the same database as the app. Ignore errors about missing files, ObsMovies, or ObsMissionHubble

          python manage.py test apps

* Run the webserver

        python manage.py runserver
