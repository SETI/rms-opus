.. _dev_guide_conventions:

Coding Conventions
==================

The rules this repository follows are checked in, in ``.cursor/rules/``, and they are
the specification rather than this summary. **That directory listing is the authority
on which rules exist**; the table below is a reading aid, and each rule file carries a
one-line description at its top.

.. list-table::
   :header-rows: 1

   * - Rule
     - Covers
   * - ``python.mdc``
     - Python coding style: naming, structure, typing, error handling.
   * - ``python_testing.mdc``
     - Test design, and how to critique a test suite.
   * - ``doc_python.mdc``
     - The documentation system, prose conventions, docstrings, and the Sphinx build
       gates.
   * - ``doc_dev_guide.mdc``
     - This guide's own structure and completeness rules.
   * - ``doc_readme.mdc``
     - The ``README``.
   * - ``doc_user_guide.mdc``, ``doc_how_to.mdc``
     - The other documentation kinds, for reference.
   * - ``pull_request.mdc``
     - How a pull request is written and opened.
   * - ``git_workflow.mdc``
     - Branching and commits.
   * - ``dependency_management.mdc``
     - Adding and pinning dependencies.
   * - ``environment.mdc``
     - Development environment and CI.
   * - ``security.mdc``
     - Security expectations.
   * - ``bug_report.mdc``
     - Reporting a defect.

What the tools enforce
----------------------

Every rule that *can* be checked mechanically is, and
``scripts/run-all-checks.sh`` runs the checks (see :ref:`dev_guide_environment` for
the list and what configures each one). Three of them are worth knowing about before
writing code:

* **mypy runs strict over the whole repository**, with no module silenced by an
  ``ignore_errors`` entry -- that list is empty. What remains is ``exclude``, for the
  paths that are not project source, and ``ignore_missing_imports``, for the
  third-party packages that ship neither annotations nor a typeshed stub. Read the
  current contents of both out of ``[tool.mypy]``; each entry is documented where it
  sits, and counting them here would only go stale. A tree that
  cannot pass the checker is not a configuration problem: annotate it, or say at the
  site -- with the reason -- what the checker cannot see, which is what
  ``# type: ignore[...]`` is for. ``warn_unused_ignores`` is on, so each of those has
  to keep earning its place.
* **ruff's per-file-ignores table is empty**, and adding a row to it is not the way to
  land code that does not pass. Fix the code, or suppress the one rule on the one line
  with ``# noqa: <CODE>`` and the reason, which ``RUF100`` then keeps honest by
  failing when the suppression stops being needed. A handful of codes are ignored
  globally instead, listed in ``extend-ignore`` with a reason for each.
* **bandit's skip list is one entry** (``B101``, the narrowing assertions the type
  annotations rest on); everything else is a per-line ``# nosec <ID> - <reason>`` at
  the statement it covers.

Deviations
----------

One rule is deliberately waived for this repository, and it is written down where it
applies rather than only here:

* **Public web API backwards compatibility is preserved**, against the general
  no-back-compat policy. An OPUS URL that worked before has to keep working; the
  guide in :ref:`api_guide` is what it has to keep matching. The one deliberate
  exception is ``/apiguide.pdf``, which redirects (302) to the published guide
  rather than serving a generated PDF, since the PDF is not built here; the URL
  still resolves, and ``test_help_api.py`` pins the redirect.

Docstrings
----------

Every module, class, method and function carries a docstring, in Google style with a
``Parameters:`` section, and the API reference is generated from them -- so a thin
docstring is a hole in the published documentation rather than a private matter.

There is one standing exemption, and it is deliberate: the ``field_obs_*`` methods of
the obs hierarchy do not carry individual docstrings. Each class that has them says so
once in its own docstring. The authoritative statement of what one of those methods
returns is its schema column plus the test that checks the correspondence, which is
checkable, where a thousand near-identical hand-written sentences would be a thousand
chances to be wrong.
