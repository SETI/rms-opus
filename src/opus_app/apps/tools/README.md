# tools

This is where you can put utility functions that might be good for all apps to use.

Two modules here are not general-purpose helpers and are worth naming:

- `dictionary.py` holds the `Definitions` and `Contexts` models for the
  database-backed data dictionary, and `get_def_for_tooltip()`, the lookup behind the
  UI's 'info' tooltips. The tables they read are written by the import pipeline's
  `--import-dictionary` step, never by the web application.
- `file_size.py` formats a byte count for the cart interface. Its output is public
  API, so change it only deliberately.
