"""Entry point for ``python -m opus_log_analyzer``, which runs the log analyzer.

The error analyzer has no ``python -m`` form because a package has only one
``__main__``; it is run as ``python -m opus_log_analyzer.error_analyzer``.
"""

from opus_log_analyzer.log_analyzer import main

if __name__ == '__main__':
    main()
