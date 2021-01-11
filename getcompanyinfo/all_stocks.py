#### This program scrapes naukri.com's page and gives our result as a
#### list of all the job_profiles which are currently present there.

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.chrome.options import Options  # for suppressing the browser

import time
import re

#url of the page we want to scrape
url = "https://sgxdata.pebbleslab.com/index.asp?m=1&q=a"

options = Options()
options.add_argument("--headless")
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

target = soup.find_all("tr", {"class": "OddRow"}) + soup.find_all("tr", {"class": "EvenRow"})
#print(target)

for stock in target:
    stock_code = stock.find_all('td')[0].get_text()
    stock_namefs = str(stock.find_all('td')[1])

    m = re.search('>(.+?)<', stock_namefs)
    if m:
      stock_name = m.group(1)

    print(stock_code +':'+ stock_name)

driver.close() # closing the webdriver
