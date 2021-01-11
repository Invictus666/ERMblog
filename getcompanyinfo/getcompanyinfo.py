#### This program scrapes naukri.com's page and gives our result as a
#### list of all the job_profiles which are currently present there.
import sys
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.chrome.options import Options  # for suppressing the browser

import time

stock = sys.argv[1]

#url of the page we want to scrape
url = "https://www.sgx.com/securities/equities/" + stock

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-logging")
options.add_argument('--log-level=3')
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=options)
driver.get(url)

# this is just to ensure that the page is loaded
time.sleep(5)

html = driver.page_source

# this renders the JS code and stores all
# of the information in static HTML code.

# Now, we could simply apply bs4 to html variable
soup = BeautifulSoup(html, 'html.parser')
#print(soup.prettify())

company_name = soup.find("h1").get_text()
print("Company : " + company_name + "\n")

company_info = soup.find("div",{"class": "widget-stocks-company-info-item-summary mb-4 text-body"}).get_text()
company_info = company_info.partition('.')[0] + '.'
print("Company info : \n")
print(company_info)


driver.close() # closing the webdriver
