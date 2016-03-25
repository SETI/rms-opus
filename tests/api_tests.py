from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import json
import csv

api_endpoint = "http://tools.pds-rings.seti.org/opus/api/meta/result_count.json?"
filename = 'result_counts.txt'

with open(filename, 'rb') as csvfile:

    filereader = csv.reader(csvfile)
    for row in filereader:

        q_str, expected, info = row

        url_hash = q_str.split('#/')[1].strip()
        api_url = api_endpoint + url_hash

        driver = webdriver.Firefox()
        driver.get(api_url)
        soup = BeautifulSoup(driver.page_source)
        dict_from_json = json.loads(soup.find("body").text)

        print "checking.. " + api_url
        print "expecting " + expected
        print dict_from_json['data'][0]['result_count']
        assert dict_from_json['data'][0]['result_count'] >= int(expected)
        driver.close()

print "OK!"
