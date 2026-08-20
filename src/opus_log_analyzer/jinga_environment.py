from jinja2 import Environment, PackageLoader, StrictUndefined

# The report templates ship inside the wheel, so they are located through the package
# rather than through the working directory. PackageLoader resolves 'templates/' against
# this package's installed location using importlib, which is what makes the reports
# render no matter where the analyzer is invoked from.
JINJA_ENVIRONMENT = Environment(
    loader=PackageLoader('opus_log_analyzer', 'templates'),
    autoescape=True,
    # line_statement_prefix='#',
    line_comment_prefix='##',
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True
)
