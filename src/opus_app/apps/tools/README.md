# tools

This is where you can put utility functions that might be good for all apps to use.

Two modules here are not general-purpose helpers and are worth naming:

- `dictionary.py` holds the `Definitions` and `Contexts` models for the
  database-backed data dictionary, and `get_def_for_tooltip()`, the lookup behind the
  UI's 'info' tooltips. They lived in a `dictionary` app of their own until the Django
  5.2 upgrade removed it; the tables are written by the import pipeline's
  `--import-dictionary` step, never by the web application.
- `file_size.py` formats a byte count for the cart interface, replacing the
  `hurry.filesize` dependency. Its output is public API, so change it only
  deliberately.
