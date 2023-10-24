## Installing OPUS Locally Using Ubuntu Linux
## NOTE: OPUS REQUIRES PYTHON 3.6 OR HIGHER

1. Install mysql if necessary

      sudo apt-get install mysql-server
      sudo apt-get install mysql-client
      sudo apt-get install libmysqlclient-dev

2. Ubuntu dependencies

  Ubuntu also requires the following packages be installed:

        apt-get install libncurses-dev xvfb libfontconfig

  and the patched version of wkhtmltopdf:

        wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
        sudo tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
        sudo mv wkhtmltox/bin/wkhtmlto* /usr/bin/

3. Create the mysql databases

  - Run the mysql command line:

          mysql [-u <username>] -p

  - In the mysql command line, create the two databases and the opus user:

          # OPUS databases
          create database opus_small;
          create database dictionary;

          # the OPUS web user
          create user 'USERNAME'@'localhost' identified by "PASSWORD";

4. Initialize the databases from dump files (ask the Ring-Moon Systems Node for these files)

        mysql opus_small [-u <username>] -p < opus_small.sql
        mysql dictionary [-u <username>] -p < dictionary.sql -p

5. Clone the repo

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/SETI/rms-opus.git

        However, it is a better practice to fork the repo first into your private GitHub account, and then clone from there.

6. Clone the other repos that are needed for support

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/SETI/rms-webtools.git

7. Create a virtualenv and install the dependencies

        cd <RMS-OPUS DIRECTORY>
        virtualenv --python=<YOUR PYTHON 3.x EXECUTABLE> venv

        source venv/bin/activate
        pip install -r requirements-python3.txt

8. Edit the opus_secrets.py file

  - Copy the template:

        cd <RMS-OPUS DIRECTORY>
        cp opus_secrets_template.py opus_secrets.py

    Update opus_secrets.py as needed for your system.

9. Make the logs directory

        mkdir logs

10. Run migrate:

    cd <RMS-OPUS DIRECTORY>/opus/application
    python manage.py migrate

11. Run the webserver

    python manage.py runserver
