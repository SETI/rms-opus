These tests run against the production webserver api endpoints.

THe list of urls and expected result counts are found in result_counts.txt


Run the Tests:

    python api_tests.py


- initial setup: install requirements and create a conda environment, and activate it:

    conda create -n opus_tests --file requirements.txt   
    source activate opus_tests

• tests in result_counts.text were originally exported as csv from this google doc: these were originally exported as csv from [this google doc](https://docs.google.com/spreadsheets/d/1zy3FX0vCGqAnm6vidZI9HJyEzatW3q57HQn0ef9Fsso/edit?usp=sharing)
