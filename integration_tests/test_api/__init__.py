"""The golden-response API suite.

Each test issues one OPUS API request and compares the whole response with a
recorded one, either written into the test or kept as a file under
`responses/`. Between them they are this rewrite's primary evidence that the
public API did not change; see TEST_API_README.md for how to run them and how
to regenerate a recorded response.
"""

