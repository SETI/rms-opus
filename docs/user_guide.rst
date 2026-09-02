.. _user_guide:

User Guide
==========

This guide is for running an OPUS server of your own: installing the distribution,
building the database from a set of PDS holdings, putting a web server in front of the
application, and operating it afterwards.

It assumes a system administrator comfortable with a Unix server, MySQL and a web server,
and someone who knows what the PDS holdings are. It assumes **nothing about how OPUS is
built**: no Python beyond running a ``pip install``, no knowledge of the pipeline's or the
application's internals, and no tests. Everything it asks you to run is a command the
distribution installs.

.. toctree::
   :maxdepth: 1

   user_guide_installation
   user_guide_web_server
   user_guide_deployment

:ref:`user_guide_installation` is the whole of bringing one up from nothing: the
prerequisites, the ``pip install``, the one configuration file OPUS reads, the database,
the static files, and a first import -- including what a full-holdings import involves and
how to tell whether it succeeded. :ref:`user_guide_web_server` is the layer in front of
the application: worked nginx configurations with gunicorn and with uWSGI, Apache with
``mod_wsgi``, and the three things any of them has to arrange. :ref:`user_guide_deployment`
is the running of it: replacing the database with a newly imported one, what must always
be done after an import, and the log-analyzer cron jobs.

Two other guides sit beside this one. The :ref:`Public Web API guide <api_guide>`
documents the HTTP interface an OPUS server offers, for people querying one rather than
running one. :ref:`dev_guide` is for people modifying OPUS itself, and is where the
internals, the test suites and the contribution process are described.
