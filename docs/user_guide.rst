.. _user_guide:

User Guide
==========

This guide is for running an OPUS server of your own: installing OPUS, building the
database from a set of PDS holdings, putting a web server in front of the application,
and operating it afterwards.

Most of that is done by scripts the distribution ships. You create one virtual
environment, write the scripts out with ``opus_deploy_scripts``, and fill in one file of
settings describing your server; from then on an import is one command and a deploy is
another. There is nothing to clone and nothing to build.

It assumes a system administrator comfortable with a Unix server, MySQL and a web server,
and someone who knows what the PDS holdings are. It assumes **nothing about how OPUS is
built**: no Python beyond running a ``pip install``, no knowledge of the pipeline's or the
application's internals, and no tests.

.. toctree::
   :maxdepth: 1

   user_guide_installation
   user_guide_web_server
   user_guide_deployment

:ref:`user_guide_installation` is the whole of bringing one up from nothing, in six
steps: the prerequisites, the environment the scripts come from, writing them out, the
settings file, the first import, and the first deploy -- including what a full-holdings
import involves and how to tell whether it succeeded. :ref:`user_guide_web_server` is the
layer in front of the application: worked nginx configurations with gunicorn and with
uWSGI, Apache with ``mod_wsgi``, and the three things any of them has to arrange.
:ref:`user_guide_deployment` is the running of it afterwards: deploying a new release,
replacing the database with a newly imported one, what must always be done after an
import, and the log-analyzer cron jobs.

Two other guides sit beside this one. The :ref:`Public Web API guide <api_guide>`
documents the HTTP interface an OPUS server offers, for people querying one rather than
running one. :ref:`dev_guide` is for people modifying OPUS itself, and is where the
internals, the test suites and the contribution process are described.
