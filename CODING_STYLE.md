JavaScript and CSS:

- Use spaces instead of hard tabs
- Use 4-space indents
- Control statements such as "if", "while", and "for":   `if (test) {`
  - Space after the statement name and before the (
  - Space after the )
- Use double quotes ("x") for strings
- All identifiers (e.g. variable names, function names) should be in camelCase
  and sufficiently detailed to make it clear what their purpose is, but not
  more than ~30 characters long
- Use a space after all ":" in dictionary definitions or CSS: `{"x": 0}`
- Within a single statement, be consistent in the use of \`Hi {x}\` vs.
  "Hi "+x
- Avoid global (or namespace-wide) variables unless absolutely necessary
- Avoid hard-coded constants that depend on the specific layout or size of
display elements
- Comments should be used to explain *why* something is being done, not *how*
- Use the prefix "op-" on all OPUS-specific HTML classes and ids
- Always use CSS classes instead of hard-coding style elements or colors in the
  HTML or JavaScript source
- Use "let" wherever appropriate instead of "var"
