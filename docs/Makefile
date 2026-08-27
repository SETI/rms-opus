# Minimal makefile for Sphinx documentation.
#
# `make html` builds under both gates the documentation has to pass: -W turns every
# warning into an error and -n reports every cross-reference that does not resolve.
# scripts/run-all-checks.sh runs `make html SPHINXOPTS="-W"` on top of that.

SPHINXOPTS    ?= -W -n
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help Makefile

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
