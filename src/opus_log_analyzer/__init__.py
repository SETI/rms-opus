"""The OPUS log analyzer: it turns Apache access and error logs into readable reports.

The package holds two programs, not a library. `opus_log_analyzer.log_analyzer`
summarizes user sessions from access logs and is what ``python -m opus_log_analyzer``
runs; `opus_log_analyzer.error_analyzer` correlates error-log entries with the requests
that produced them. Both are internal to the ``rms-opus`` distribution, with no API
stability guarantees for outside users.

The modules directly under this package are generic log-analysis machinery; the
OPUS-specific knowledge (slugs, query parsing, report layout) lives in the
`opus_log_analyzer.opus` subpackage, which the log analyzer loads by module name through
its ``--configuration`` option. That subpackage is unrelated to the Django application
package, which is named ``opus_app``.

This module deliberately imports nothing. The package's modules import each other by
absolute path (``from opus_log_analyzer.log_entry import LogEntry``), and an empty
package root keeps that graph free of import cycles.
"""
