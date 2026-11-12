"""How the database server compares two strings, for code that compares them itself.

Every OPUS string column but the ASCII ones uses the ``utf8mb4_0900_ai_ci`` collation,
which ignores case and accents. The import keys its cache of a field's mult values this
way, so that a value the server's unique key would call a duplicate finds the row already
there, and the web application keys its in-memory copies of the import's tables this way,
so that a lookup finds what a query would. An ASCII column (``ascii_general_ci``) ignores
case only; `UNSTORED_ASCII_CHARACTER` is the one ASCII character none may hold.
"""

from __future__ import annotations

import unicodedata

#: The character no ASCII column holds: the import refuses a value carrying it, and the
#: web application binds it in place of a character that has no ASCII form, so that it
#: matches nothing.
UNSTORED_ASCII_CHARACTER = '\x7f'


def collation_key(text: str) -> str:
    """Return the form of a string that the server's collation compares.

    The server compares strings with ``utf8mb4_0900_ai_ci``, which ignores case and
    accents, so two strings it calls equal have the same key here. The key is not the
    collation in full: it does not ignore what the collation ignores, such as a soft
    hyphen or an ASCII control character, and it maps some characters onto others the
    collation keeps apart (``¨`` onto a space). Two strings of printable ASCII have equal
    keys exactly when the collation calls them equal.

    Parameters:
        text: The string to compare.

    Returns:
        The string with its accents removed and its case folded.
    """
    decomposed = unicodedata.normalize('NFKD', text)
    return ''.join(char for char in decomposed if not unicodedata.combining(char)).casefold()
