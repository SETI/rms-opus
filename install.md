## Installing OPUS Locally Using Ubuntu Linux
## NOTE: OPUS REQUIRES PYTHON 3.6 OR HIGHER

1. Install mysql if necessary

      sudo apt install mysql-server
      sudo apt install mysql-client
      sudo apt install libmysqlclient-dev

2. Ubuntu dependencies

  Ubuntu also requires the following packages be installed:

        apt install libncurses-dev xvfb libfontconfig

  and the patched version of wkhtmltopdf:

        wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
        sudo tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
        sudo mv wkhtmltox/bin/wkhtmlto* /usr/bin/

3. Create the mysql databases

  - Run the mysql command line:

          mysql [-u <username>] -p

  - In the mysql command line, create the opus user:

          # the OPUS web user
          create user 'USERNAME'@'localhost' identified by "PASSWORD";

4. Clone the repo

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/SETI/rms-opus.git

        However, if you plan to make modifications, it is a better practice to fork the
        repo first into your private GitHub account, and then clone from there.

6. Clone the other repos that are needed for support

        cd <YOUR_PROJECTS_DIRECTORY>
        git clone https://github.com/SETI/rms-pdsfile.git

7. Create a virtualenv and install the dependencies

        cd <RMS-OPUS DIRECTORY>
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements-python3.txt

6. Edit the opus_secrets.py file

  - Copy the template:

        cd <RMS-OPUS DIRECTORY>
        cp opus_secrets_template.py opus_secrets.py

    Update opus_secrets.py as needed for your system.

7. Make the logs directory

        mkdir logs

8. Run migrate:

    cd <RMS-OPUS DIRECTORY>/opus/application
    python manage.py migrate

9. Run the webserver

    python manage.py runserver
