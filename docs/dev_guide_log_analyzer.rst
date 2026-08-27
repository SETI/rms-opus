.. _dev_guide_log_analyzer:

The Log Analyzer
================

:mod:`opus_log_analyzer` turns a server's Apache logs into readable reports. It is two
programs rather than a library, and it is deliberately split into generic machinery
and site-specific knowledge so that the generic half could analyze another site's
logs.

* :mod:`opus_log_analyzer.log_analyzer` summarizes user sessions from access logs.
  The ``opus_log_analyzer`` console script runs it, and ``python -m opus_log_analyzer``
  runs the same ``main``.
* :mod:`opus_log_analyzer.error_analyzer` pairs error-log entries with the requests
  that caused them. The ``opus_error_analyzer`` console script runs it, and
  ``python -m opus_log_analyzer.error_analyzer`` runs the same ``main``. It names the
  module rather than the package because a package has one ``__main__`` and the log
  analyzer holds it.

The modules directly under the package are the generic half. The
:mod:`opus_log_analyzer.opus` subpackage is the OPUS-specific half: it knows what a
slug means, what a query does, and what the report should look like. **It is unrelated
to the Django application package**, which is named :mod:`opus_app`.

How a run is put together
-------------------------

Reading an access log is a pipeline:

1. :class:`~opus_log_analyzer.log_entry.LogReader` parses log lines into
   :class:`~opus_log_analyzer.log_entry.LogEntry` objects.
2. :class:`~opus_log_analyzer.log_parser.LogParser` groups them into per-host
   sessions.
3. The configuration interprets each session in the vocabulary of the site being
   analyzed, and renders the report from the packaged Jinja templates.

:mod:`opus_log_analyzer.jinga_environment` builds the Jinja environment the report
templates are rendered in; :mod:`opus_log_analyzer.ip_to_host_converter` resolves client
addresses; :mod:`opus_log_analyzer.cronjob_utils` expands the dated log-file globs the
cron jobs pass. :mod:`opus_log_analyzer.manifest` reads OPUS download manifests and
summarizes what they contain -- it sits with the generic modules but is OPUS-specific,
and its only importer is :mod:`opus_log_analyzer.opus.html_generator`.

``--batch`` and ``--cronjob`` are the modes that work. The other three modes read an
argument the parser never defines and fail before doing any work; they are recorded as
known defects rather than fixed here.

Writing a configuration
-----------------------

The analyzer reaches everything site-specific through a **configuration**: it looks
for a class named ``Configuration`` in the module ``--configuration`` names, which
defaults to :mod:`opus_log_analyzer.opus.configuration`. Naming another module by its
full dotted path is what analyzing a different site looks like::

    opus_log_analyzer --configuration myproject.configuration ...

A configuration should subclass
:class:`~opus_log_analyzer.abstract_configuration.AbstractConfiguration`. That is not
enforced, but a configuration has to supply what the abstract class declares either
way. The analyzer constructs it once per run, handing it the parsed command-line
arguments as keyword arguments.

The three methods that matter:

``create_session_info(uses_html)``
    Returns a session info -- the object that interprets one user's session. The flag
    says whether the caller can render HTML; see *Markup* below.

``create_batch_html_generator(host_infos_by_ip)``
    Returns the object that gives the report template whatever site-specific
    information it needs. For OPUS that is the names of the session flags and the
    base URL the report's links are built from.

``show_summary(sessions, output)``
    Renders the summary the ``--summary`` mode asks for -- which is one of the three
    modes that crash before reaching it, so this method is part of the contract but is
    not reachable today. A :class:`~opus_log_analyzer.log_parser.Session` carries the
    client's address, the time the session started, its log entries, and the session
    info built for it.

Writing a session info
----------------------

A session info should subclass
:class:`~opus_log_analyzer.abstract_configuration.AbstractSessionInfo`; again this is
not enforced, and again the contract has to be met either way.

``parse_log_entry(entry, log_id)``
    Called once per log entry, in order, and is where all the work is. It decides what
    the entry means, keeping whatever state it needs to read an entry in the context
    of the ones before it. It returns a pair: a sequence of zero or more strings
    naming the actions the request performed -- an empty sequence means "ignore this
    entry, produce no output for it" -- and either None or a relative URL that would
    show the reader roughly what the user saw.

``get_icon_flags()``
    Called once, after the session has ended, to collect the actions the session
    performed. Returning nothing is meaningful: a session with no flags is dropped
    from the report rather than shown empty.

Markup
------

When ``create_session_info`` was passed ``uses_html=True``, the strings
``parse_log_entry`` returns may be ordinary strings or ``markupsafe.Markup`` -- a
string already known to be safe to insert into HTML. Passing an object to ``Markup``
converts it to text and marks it safe **without escaping**; ``Markup.escape`` is what
escapes instead::

    >>> Markup('Hello, <em>World</em>!')
    Markup('Hello, <em>World</em>!')
    >>> Markup.escape('Hello, <em>World</em>!')
    Markup('Hello &lt;em&gt;World&lt;/em&gt;!')

:class:`~opus_log_analyzer.abstract_configuration.AbstractSessionInfo` offers
``safe_format``, a ``Markup`` version of ``format``: the format string must itself be
valid HTML, any argument that is already ``Markup`` is interpolated as it is, and
every other argument is escaped first.

Deployment
----------

The three cron templates in ``scripts/server/log_analyzer/`` are what runs the
analyzer on a server: a nightly update, a monthly report, and a full refresh. They are
templates because each installation fills in its own paths; nothing substitutes or
executes them automatically. See :ref:`dev_guide_deployment`.

Known defects
-------------

The log analyzer is not maintained to the same standard as the rest of OPUS, and its
known defects are filed rather than fixed: issues
`#1449 <https://github.com/SETI/rms-opus/issues/1449>`__,
`#1450 <https://github.com/SETI/rms-opus/issues/1450>`__,
`#1451 <https://github.com/SETI/rms-opus/issues/1451>`__ and
`#1452 <https://github.com/SETI/rms-opus/issues/1452>`__ cover them. Read them before
changing anything here; several of the surprises are already written down.

API reference
-------------

:doc:`api_opus_log_analyzer`
