import json
import pprint
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options


def get_selenium_page(link):
    s = Service(executable_path='../chromedriver.exe')
    o = webdriver.ChromeOptions()
    o.add_argument('--disable-blink-features=AutomationControlled')
    o.add_argument("--headless")
    driver = webdriver.Chrome(service=s, options=o)

    try:
        driver.get(link)
        time.sleep(3)
        page_source = driver.page_source
    finally:
        driver.close()
        driver.quit()

    return page_source
