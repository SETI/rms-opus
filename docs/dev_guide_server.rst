.. _dev_guide_server:

Running an OPUS Server
======================

Everything about a server rather than a checkout: bringing one up from nothing, putting a
web server in front of it, and operating it afterwards. A developer who only wants OPUS
running on their own machine wants :ref:`dev_guide_environment` and
:ref:`dev_guide_webapp_running` instead -- those are shorter, install from source, and
stop at Django's development server.

The three pages are in the order the work happens, and each says what the next one
assumes.

.. toctree::
   :maxdepth: 1

   dev_guide_installation
   dev_guide_web_server
   dev_guide_deployment

:ref:`dev_guide_installation` is the installation itself: the prerequisites, the
distribution from PyPI, the configuration file, the database, the static files and a
first import. :ref:`dev_guide_web_server` is the layer in front of it -- worked nginx
configurations with gunicorn and with uWSGI, and Apache with ``mod_wsgi`` -- and the
contract every one of them has to satisfy. :ref:`dev_guide_deployment` is what happens
afterwards: the Node's own deploy chain, what always has to be done when the database
changes, the runbook for replacing one, and the cron jobs behind the log reports.
