import json
import pprint
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_selenium_page(link):
    try:
        s = Service(executable_path='../chromedriver.exe')
        o = webdriver.ChromeOptions()
        o.add_argument('--disable-blink-features=AutomationControlled')
        o.add_argument("--headless")
        o.add_argument("--no-sandbox")
        driver = webdriver.Chrome(service=s, options=o)

        try:
            driver.get('https://www.respublica.ru' + link)
            time.sleep(2)
            page_source = driver.page_source
            adult_message = driver.find_elements(By.CLASS_NAME, 'adult-message')
            if adult_message:
                btn_yes = driver.find_element(By.CLASS_NAME, 'adult-button')
                btn_yes.click()
                time.sleep(1)

            btn = driver.find_element(by=By.CLASS_NAME, value='card-blocks').find_elements(by=By.TAG_NAME, value='li')[
                1].find_element(by=By.TAG_NAME, value='button')
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'properties'))
            WebDriverWait(driver, 10).until(element_present)
            prop_list = driver.find_elements(By.CLASS_NAME, 'property')
            prop_dict = {i.text.split(':')[0]: i.text.split(':')[1].strip() for i in prop_list}
        finally:
            driver.close()
            driver.quit()
        return [page_source, prop_dict]
    except Exception as e:
        with open('webdriver_error.txt', 'a+') as file:
            file.write(f'{link}\n{e}\n\n')
