"""OPUS-specific configuration for the generic log-analysis engine.

The modules above this package know nothing about OPUS: they parse Apache
logs into sessions and render reports. This package supplies the OPUS
vocabulary -- how to read a search slug, what a query change means, which
flags an session icon stands for -- through the `AbstractConfiguration`
interface, and is the default `--configuration` module.
"""
