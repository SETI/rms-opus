"""Tests for the Django app that need the imported database.

These call the view functions and their helpers directly rather than through
the URL router, so they can drive an argument no URL can produce. What makes
them belong here rather than in `tests/` is the database: nearly every one
reaches a query against the imported schema.
"""
