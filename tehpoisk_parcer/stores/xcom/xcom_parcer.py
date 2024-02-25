import re
import sqlite3
import time
from difflib import SequenceMatcher

import requests
import json

import selenium
import undetected_chromedriver as uc
from price_parser import Price
from undetected_chromedriver import ChromeOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

options = ChromeOptions()
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options, driver_executable_path='chromedriver.exe', version_main=116)
driver.maximize_window()
og_tab = driver.current_window_handle
driver.switch_to.new_window('tab')
SEARCH_PARAMS = 'view=tiles&sort=p&direction=asc'
conn = sqlite3.connect('test_items.db')


def parcer(cat_link, query, cat_name):
    driver.get(f'https://www.xcom-shop.ru/catalog/kompyuternye_komplektyyuschie/{cat_link}/?{query}&{SEARCH_PARAMS}')
    counter = 0
    add_counter = 0
    while True:
        parent_catalog = WebDriverWait(driver, 15).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div.catalog_items')))
        items = parent_catalog.find_elements(By.CSS_SELECTOR, 'div.catalog_item__inner')
        time.sleep(5)
        for item in items:
            try:
                item_tuple = get_tuple(item, cat_name)
            except ValueError:
                print('----------------------bad item-------------------------------')
                continue
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT tag,info,shops FROM {cat_name} WHERE tag = ?", (item_tuple,))
                db_item = cur.fetchone()
                assert db_item is not None
                shops = dict(json.loads(db_item[2]))
                price = Price.fromstring(
                    item.find_element(By.CSS_SELECTOR, 'div.catalog_item__new_price').text).amount.__int__()
                url = item.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').get_attribute('href')
                shops.update(xcom={"price": price, "url": url})
                cur.execute(f"update {cat_name} set shops = ? where (tag = ?)",
                            (json.dumps(shops), item_tuple))
            except AssertionError:
                print(f'there is no such tag in the table: {item_tuple}')
                cur = conn.cursor()
                url = item.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').get_attribute('href')
                price = Price.fromstring(
                    item.find_element(By.CSS_SELECTOR, 'div.catalog_item__new_price').text).amount.__int__()
                image_urls = f"{page.find_element(By.CSS_SELECTOR, 'a.catalog_item__image--tiles').find_element(By.CSS_SELECTOR, 'img').get_attribute('src').removesuffix('210.jpg')}500.jpg"
                shops = dict()
                shops.update(xcom={"price": price, "url": url})
                cur.execute(f"insert into {cat_name} values (?,?,?,?,?)",
                            (item_tuple, '', json.dumps(shops), image_urls,''))
                print('item added')
                add_counter += 1
                # cur = conn.cursor()
                # cur.execute(f"SELECT shops FROM {table_name} WHERE tag = ?", (tag,))
                # db_item = cur.fetchone()
                # assert db_item is not None
                # shops = dict(json.loads(db_item[0]))
                # shops.update(xcom={"price": price, "url": link})
                # new_shops = json.dumps(shops)
                # cur.execute(f'update ssd set shops = ? where (tag = ?)', (new_shops, tag))
            # except Exception as e:
            #     print('cannot find item in dict')
            #     print(e)
            # except AssertionError:
            #     print('new item')
                # click on an item and take needed data and insert in a database OR add url to list for later
            counter += 1
        try:
            pages = WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.navigation span')))
            print('new page')
            active_page = False
            last_page = False
            for page in pages:
                last_page = True
                if active_page:
                    print('page found')
                    try:
                        driver.find_element(By.CSS_SELECTOR,  'div.popmechanic-close').click()
                    except NoSuchElementException:
                        pass
                    page.click()
                    print('page clicked')
                    last_page = False
                    time.sleep(7)
                    break
                if page.get_attribute('class') == 'active':
                    active_page = True
                    continue
            if last_page:
                print(f'last page, total items extracted: {counter}, {add_counter}')
                conn.commit()
                break
        except TimeoutException:
            print('bad')
            driver.quit()
            conn.commit()
            break
        except KeyboardInterrupt as e:
            driver.quit()
            conn.commit()
            raise e
    conn.commit()
    driver.quit()



def get_tuple(page, cat_name):
    match cat_name:
        case 'cpu':
            info_string = page.find_element(By.CSS_SELECTOR, 'div.catalog_item__description').text.lower()
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            line = ''
            intel_line = re.search('intel i[0-9]', part_name)
            if intel_line is not None:
                part_name = part_name.replace('intel', 'intel core')
            amd_line = re.search('amd threadripper', part_name)
            if amd_line is not None:
                part_name = part_name.replace('amd threadripper', 'amd ryzen threadripper')
            if part_name.find('intel') != -1:
                part_name = part_name.replace('-', ' ')
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'pentium', 'celeron'])
            else:
                lines = list(
                    ['athlon', 'a6', 'a8', 'a12', 'epyc', 'ryzen threadripper', 'ryzen 3',
                     'ryzen 5', 'ryzen 7', 'ryzen 9'])
            for line_name in lines:
                if part_name.find(line_name) != -1:
                    line = line_name
                    if part_name.find('ryzen') != -1 and part_name.find('pro') != -1:
                        line = f'{line_name} pro'
                    break
            if line == 'pentium':
                part_name = str(part_name).replace(' gold', '')
            if line == 'ryzen 5':
                part_name = part_name.replace(' oem', '')
            if line == '':
                print(part_name)
                print('SOMETHING WRONG WITH THE NAME')
            print(info_string)
            if re.search('w/o cooler box|w/.o cooler box|box w/.o cooler|box w/o cooler|boxed without cooler|box w/&shy;o cooler|w/&shy;o cooler box',info_string) is not None:
                print(f'COOLERLESS {info_string}')
                delivery_type = 'box (без кулера)'
            elif info_string.find('box') != -1:
                delivery_type = 'box'
            else:
                delivery_type = 'oem'
            part_name = f'{part_name} {delivery_type}'
            return part_name
        case 'mb':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            return part_name
        case 'ram':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            try:
                part_name = full_name.rsplit(' ',maxsplit=1)[1]
                brand = re.search('hp',full_name)
                if brand is not None:
                    part_name.replace('#abb','')
            except IndexError:
                raise ValueError
            return part_name
        case 'gpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            try:
                part_name = full_name.split('(')[1].split(')')[0]
            except IndexError:
                print('not tag in the name')
                part_name = page.find_element(By.CSS_SELECTOR, 'div.catalog_item__partnumber').text.lower()
            mistakes = re.search(
                'gv-n3050aorus e-8gd0|radeon rx 6650 xt mech 2x 8g oc|rtx 3060 ventus 2x oc ru|arc a750|gv-n4070aero oc-12gb',
                part_name)
            if mistakes is not None:
                if mistakes.group(1) is not None:
                    part_name = 'gv-n3050aorus e-8gd'
                if mistakes.group(2) is not None:
                    part_name = 'rx 6650 xt mech 2x 8g oc'
                if mistakes.group(3) is not None:
                    part_name = 'rtx 3060 ventus 2x oc ru'
                if mistakes.group(4) is not None:
                    part_name = 'a750 astro 2x 8g'
                if mistakes.group(5) is not None:
                    part_name = 'gv-n4070aero oc-12gd'
            return part_name
        case 'ssd':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name
        case 'hdd':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name
        case 'spu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            return part_name
        case 'pc_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            return part_name
        case 'cool_cpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            return part_name
        case 'cool_lck':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            return part_name
        case 'cool_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog_item__name').text.lower()
            part_name = full_name
            return part_name




if __name__ == '__main__':
    parcer('videokarty/', '', 'gpu')
