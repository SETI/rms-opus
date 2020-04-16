from jinja2 import Environment, FileSystemLoader, StrictUndefined

JINJA_ENVIRONMENT = Environment(
    loader=FileSystemLoader("templates/"),
    autoescape=True,
    # line_statement_prefix='#',
    line_comment_prefix='##',
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True
)
