# ui/templatetags/multilines_template_tags.py
"""Let OPUS templates spread a single template tag over several lines.

Django's lexer splits a template with one regular expression, `template.base.tag_re`,
whose `.*?` cannot cross a newline, so `{{ foo }}` written over two lines is emitted
as literal text instead of being evaluated. Recompiling the same pattern with
`re.DOTALL` removes that restriction and changes nothing else.

**This module is not a template-tag library and must not be `{% load %}`ed.** It
defines no `register`, so Django never offers it as a library; the patch is applied
purely as an import side effect. The import is not accidental either: setting up the
DjangoTemplates engine walks the `templatetags` package of every installed app and
imports every module in it, keeping only those that define `register`. `ui` is an
installed app, so this module is imported before any template is rendered.

Monkeypatching a private-by-convention module global is fragile across upgrades, so
it carries the version it was last verified against.

**Verified against Django 5.2.17** (PR-09, 2026-08-23), by three separate checks:
`template.base.tag_re` is still a plain `re.Pattern` holding the pattern this
recompiles; `Lexer.tokenize` still resolves `tag_re` as a module global at call time,
so rebinding the attribute takes effect; and with the engine set up, `tag_re.flags`
has gained `re.DOTALL` and a template reading `A{{\\n  x\\n}}B` renders as `AXB`,
which it does not without the patch. Re-verify all three on the next Django upgrade.
"""

import re

from django.template import base

base.tag_re = re.compile(base.tag_re.pattern, re.DOTALL)
