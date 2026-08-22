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

5. Create a virtualenv and install the dependencies

        cd <RMS-OPUS DIRECTORY>
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

    Then install rms-opus itself in editable mode so that the packages under
    `src/` (such as `opus_support`) are importable:

        pip install -e .

6. Write the opus.toml configuration file

  - Copy the template:

        cd <RMS-OPUS DIRECTORY>
        cp opus.toml.template opus.toml

    Update opus.toml as needed for your system, then point OPUS at it. OPUS has
    no default location for the file, so OPUS_CONFIG must be set in the
    environment of every OPUS process (the web server, `manage.py`, and the
    import pipeline):

        export OPUS_CONFIG=<RMS-OPUS DIRECTORY>/opus.toml

7. Make the logs directory

        mkdir logs

8. Run migrate:

    cd <RMS-OPUS DIRECTORY>
    python manage.py migrate

9. Run the webserver

    python manage.py runserver
