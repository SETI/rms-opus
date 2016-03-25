These are selenium tests, meant to run against the production webserver api endpoints

a list of urls and expected result counts are found in result_counts.txt, these are exported as csv from a google doc:
https://docs.google.com/spreadsheets/d/1zy3FX0vCGqAnm6vidZI9HJyEzatW3q57HQn0ef9Fsso/edit?usp=sharing

Run: 

    python api_tests.py 


To install the requirements in this directory: 

    virtualenv --python=/usr/local/bin/python2.7 venv --distribute
    source venv/bin/activate    
    pip install -r requirements.txt

