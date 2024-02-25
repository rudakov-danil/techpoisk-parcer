import sqlite3
import time
import requests
import json
import re

from price_parser import Price
from translatepy.translators.translatecom import TranslateComTranslate
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException





def updater(shops):
    options = ChromeOptions()
    options.page_load_strategy = 'eager'
    driver = uc.Chrome(options=options, driver_executable_path='description_parcer/parcer/chromedriver.exe', version_main=116, headless=True)
    driver.maximize_window()
    og_tab = driver.current_window_handle
    driver.switch_to.new_window('tab')
    links = dict(json.loads(shops))
    for link in links.keys():
        shop_name = links[link]
        print(shop_name)
        driver.get(links[shop_name]['url'])
        match(shop_name):
            case 'dns':
                price = Price.fromstring(driver.find_element(By.CSS_SELECTOR, 'div.product-buy__price').text).amount.__int__()
                links[shop_name].update(price=price)
            case 'onlinetrade':
                price = Price.fromstring(driver.find_element(By.CSS_SELECTOR, 'div.catalog__displayedItem__actualPrice').find_element(By.CSS_SELECTOR, 'span.js__actualPrice')).amount.__int__()
                links[shop_name].update(price=price)
            case 'xcom':
                price = Price.fromstring(driver.find_element(By.CSS_SELECTOR, 'div.card-bundle-basket__price')).amount.__int__()
                links[shop_name].update(price=price)
            case 'regard':
                price = Price.fromstring(
                    driver.find_element(By.CSS_SELECTOR, 'div.PriceBlock_priceBlock__178uq')).amount.__int__()
                links[shop_name].update(price=price)
            case 'citilink':
                price = Price.fromstring(driver.find_element(By.CSS_SELECTOR, 'span.app-catalog-l635m1').text).amount.__int__()
                links[shop_name].update(price=price)
        driver.quit()
        return links
