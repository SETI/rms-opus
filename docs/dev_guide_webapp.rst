.. _dev_guide_webapp:

The Web Application
===================

:mod:`opus_app` is the Django project that serves the OPUS user interface and the public
web API out of the database an import wrote. It runs under a WSGI server behind nginx or
Apache, it is configured by the same TOML file as everything else in OPUS, and it holds
no metadata of its own: every value it returns was computed by
:ref:`dev_guide_import` and stored in :ref:`dev_guide_database`.

Its Django apps are ``search``, ``results``, ``metadata``, ``cart``, ``ui``, ``help`` and
``paraminfo``, over a ``tools`` app holding what they share, and they are documented
together here.

Start with :ref:`dev_guide_webapp_overview`, which follows one request from the URL to
the answer; :ref:`dev_guide_webapp_running` is how to start the thing at all. The
remaining pages are the shared machinery, then each app in the order a user meets it, and
finally what to do to add to any of them.

.. toctree::
   :maxdepth: 1

   dev_guide_webapp_overview
   dev_guide_webapp_running
   dev_guide_webapp_tools
   dev_guide_webapp_search
   dev_guide_webapp_results
   dev_guide_webapp_ui
   dev_guide_webapp_extending
