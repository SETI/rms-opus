## Installing OPUS Locally Using Windows
## NOTE: OPUS REQUIRES PYTHON 3.6 OR HIGHER

1. Install mysql if necessary

  Download the installer from https://dev.mysql.com/downloads/windows

2. Create the mysql databases

  - Run the mysql command line:

          mysql -u <username> -p

  - In the mysql command line, create the 3 databases and the opus user:

          # OPUS databases  
          create database opus;
          create database dictionary;

          # The OPUS web user
          create user 'USERNAME'@'localhost' identified by "PASSWORD";

3. Initialize the databases from dump files (ask the Ring-Moon Systems Node for these files)

        mysql opus_small [-u <username>] -p < opus_small.sql
        mysql dictionary [-u <username>] -p < dictionary.sql -p

5. Clone the repo

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/SETI/pds-opus.git

        However, it is a better practice to fork the repo first into your private GitHub account, and then clone from there.  

6. Clone the other repos that are needed for support

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/SETI/pds-tools.git
        git clone https://github.com/SETI/pds-webtools.git

7. Create a virtualenv and install the dependencies

        cd <PDS-OPUS DIRECTORY>
        virtualenv --python=<YOUR PYTHON 3.x EXECUTABLE> venv

        venv\Scripts\activate
        cd windows
        pip install -r requirements-windows.txt
        pip install mysqlclient-1.3.13-cp36-cp36m-win_amd64.whl # Replace 36 with 37 if using Python 3.7

8. Edit the secrets.py file

  - Copy the template:

        cd <PDS-OPUS DIRECTORY>
        copy opus_secrets_template.py opus_secrets.py

    Update opus_secrets.py as needed for your system.

9. Make the logs directory

        mkdir logs

10. Run migrate:

    cd <PDS-OPUS DIRECTORY>/opus/application
    python manage.py migrate

11. Run the webserver

    python manage.py migrate
