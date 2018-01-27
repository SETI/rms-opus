# These are actually API Tests

If you are looking for the Django tests, the are in apps/ and described
in deploy/README.md

These tests send http requests to a public opus API, identified at base url set in config.py

The list of opus urls to check are in result_counts.txt (although it doesn't use the base_urls found in that text file)

Run these Tests:

    python api_tests.py


This layer of testing is a way to test the public deployed API is behaving normally,
and it is also data integrity tests. The urls found in result_counts.txt are
manually added by doing opus searches. 

Initial setup: install requirements and create a conda environment, and activate it:

    conda create -n opus_tests --file requirements.txt   
    source activate opus_tests

• tests in result_counts.text were originally exported as csv from this google doc: these were originally exported as csv from [this google doc](https://docs.google.com/spreadsheets/d/1zy3FX0vCGqAnm6vidZI9HJyEzatW3q57HQn0ef9Fsso/edit?usp=sharing)
