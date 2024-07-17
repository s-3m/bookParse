import json
import pprint
import time
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


def get_book_data(link):
    s = Service(executable_path='../chromedriver.exe')
    o = webdriver.ChromeOptions()
    o.add_argument("--ignore-certificate-errors")
    o.add_argument('--allow-running-insecure-content')
    o.add_argument('--disable-blink-features=AutomationControlled')
    # o.add_argument("--headless")
    driver = webdriver.Chrome(service=s, options=o)

    try:
        driver.get(link)
        time.sleep(2)
        page_source = driver.page_source
        buy_button = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[3]/div[1]/div[1]/div[2]/div['
                                                   '2]/div/a')
        buy_button.click()
        time.sleep(1)
        cart = driver.find_element(By.XPATH, '/html/body/header/div/div/div/div/div[2]/a[1]')
        cart.click()
        quantity_input = driver.find_element(By.XPATH, '/html/body/div[2]/div/div[1]/form/div[2]/div/div[1]/div['
                                                       '2]/div[4]/div/div/input')
        quantity_input.send_keys(Keys.BACKSPACE)
        quantity_input.send_keys('999')
        time.sleep(1)
        final_quantity = driver.find_element(By.XPATH, '/html/body/div[2]/div/div[1]/form/div[2]/div/div[2]/div['
                                                       '1]/div/div[2]/dl/dd').text.split('—')[-1].split(' ')[1]

    finally:
        driver.close()
        driver.quit()

    return final_quantity, page_source
