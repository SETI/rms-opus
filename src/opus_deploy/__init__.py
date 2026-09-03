"""The server deploy chain, and the command that writes it somewhere it can be run.

The chain itself is shell: it stops a web server, builds a virtual environment, installs
the released distribution into it, generates that installation's ``opus.toml``, runs the
import and the management commands, and starts the web server again. It ships here so
that a server with no checkout has it, and `opus_deploy.scripts` is the one Python module
in this package -- the ``opus_deploy_scripts`` command, which copies the chain out of the
installation and into a directory of the operator's choosing.

**The copy is the point, not a convenience.** A deploy upgrades ``rms-opus``, and these
scripts are part of ``rms-opus``: run from inside the installation being upgraded, a
script would be replaced by ``pip`` while bash was still reading it.
"""
