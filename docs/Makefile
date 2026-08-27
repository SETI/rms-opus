# Minimal makefile for Sphinx documentation.
#
# `make html` builds under both gates the documentation has to pass: -W turns every
# warning into an error and -n reports every cross-reference that does not resolve.
# scripts/run-all-checks.sh names the same pair explicitly, so the gate does not
# depend on this default.

SPHINXOPTS    ?= -W -n
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help Makefile

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
