import os
import sys
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

conn = sqlite3.connect('test_items.db') 

import time
import os
import json
import re
import traceback
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from stores.citilink.citilink_describer import describer_citilink
from stores.dns.dns_describer import describer_dns
from stores.onlinetrade.ot_describer import describer_ot
from stores.xcom.xcom_describer import describer_xcom
from stores.regard.regard_describer import describer_regard

options = ChromeOptions()
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options, driver_executable_path='chromedriver.exe')
driver.maximize_window()
og_tab = driver.current_window_handle
conn = sqlite3.connect('test_items.db')



def searcher(cat_name):
    try:
        counter = 0
        if counter >= 20:
            raise ValueError
        cur = conn.cursor()
        tic = time.perf_counter()
        # driver.get('https://www.regard.ru/product/411818/processor-intel-core-i7-12700k-oem')
        # driver.quit()
        # return
        cur.execute(f"SELECT tag,full_info,shops FROM {cat_name}")
        db_item = cur.fetchall()
        shop_prev = ''
        for item in db_item:
            if item[1] is not None and item[1] != '':
                print("This item already filled with info")
                continue
            links = dict(json.loads(item[2]))
            shop_iter = iter(links)
            shop_name = next(shop_iter)
            # Проверка на наличие доп магазина для облегчения обхода банов парсера
            # if shop_name == shop_prev:
            #     try:
            #         shop_name = (next(shop_iter))
            #     except StopIteration:
            #         shop_name == shop_prev
            # shop_prev = shop_name
            # Создание и переход к новому окну
            driver.switch_to.window(og_tab)
            driver.switch_to.new_window('tab')
            # Запуск страницы
            try:
                driver.get(links[shop_name]['url'])
            except KeyError:
                driver.get(links[shop_name]['href'])
            time.sleep(1)
            print(shop_name)
            # парсинг: 0 - краткие, 1 - полные характеристики
            item_tuple = parcer(shop_name, cat_name)
            print(type(item_tuple))

# ПЕРЕНЕСТИ ФУНКЦИОНАЛ В ОТДЕЛЬНЫЙ МЕТОД
            while True:
                missing_info = checker(item_tuple[1])
                if len(missing_info) != 0:
                    driver.switch_to.window(og_tab)
                    driver.switch_to.new_window('tab')
                # Запуск страницы
                    try:
                        driver.get(links[shop_name]['url'])
                    except KeyError:
                        driver.get(links[shop_name]['href'])
                    missing_items = parcer(next(shop_iter),cat_name)
                    for item in missing_info:
                        item_tuple[0][item] = missing_items[0][item]
                else:
                    break
            # try:
            #     item_tuple = parcer(shop_name, cat_name)
            # except AttributeError:
            #     print('BAD SITE PARAMETERS')
            #     driver.close()
            #     driver.switch_to.window(og_tab)
            #     driver.switch_to.new_window('tab')
            #     temp = next(iter(links))
            #     driver.get(links[temp]['url'])
            #     item_tuple = parcer(temp,cat_name)
            cur.execute(f'update {cat_name} set info = ?,full_info = ? where tag = ?',
                        (item_tuple[0], json.dumps(item_tuple[1]), item[0]))
            driver.close()
            counter+=1
            print(time.perf_counter() - tic)
        driver.quit()
        conn.commit()
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    finally:
        conn.commit()
        driver.quit()
        os.system("taskkill /im chrome.exe /f")
        



def parcer(shop_name, cat_name):
    match shop_name:
        case 'regard':
            # логика проверки 
            return describer_regard(cat_name,driver)
        case 'xcom':
            return describer_xcom(cat_name,driver)
        case 'dns':
            return describer_dns(cat_name,driver)
        case 'citilink':
            return describer_citilink(cat_name,driver)
        case 'onlinetrade':
            return describer_ot(cat_name,driver)

def filler(info):
    return 0

def checker(info:dict):
    missing_info = []
    for tab in info.keys():
        if info[tab] is None:
            print("an item")
            missing_info.append(tab)
    return missing_info


if __name__ == '__main__':
    searcher('hdd')
