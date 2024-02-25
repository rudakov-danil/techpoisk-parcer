import re
import sqlite3
import time
import requests
import json
from price_parser import Price
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
options = ChromeOptions()
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options, driver_executable_path='chromedriver.exe', version_main=114)
driver.maximize_window()
driver.switch_to.new_window('tab')
conn = sqlite3.connect('../test_items.db')
time.sleep(10)

def search_hrefs(cat_link, query,cat_name):
    driver.get(
        f'https://www.citilink.ru/catalog/{cat_link}/?{query}')
    time.sleep(5)
    driver.find_element(By.CSS_SELECTOR, 'button.css-1jfe691').click()
    counter = 0
    add_counter = 0
    while True:
        try:
            time.sleep(5)
            WebDriverWait(driver, 10).until(expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.app-catalog-127ajd9')))
            cards = driver.find_elements(By.CSS_SELECTOR, 'div.app-catalog-l9pqdy')
            for card in cards:
                ActionChains(driver).scroll_to_element(card).perform()
                try:
                    if card.find_element(By.CSS_SELECTOR, 'span.app-catalog-ctwgzm').text == 'Уценка':
                        print('Уценка')
                        continue
                except NoSuchElementException:
                    pass
                try:
                    item_tuple = get_tuple(card, cat_name)
                except ValueError:
                    print('----------------------bad item-------------------------------')
                    continue
                url = card.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').get_attribute('href')
                price = Price.fromstring(card.find_element(By.CSS_SELECTOR, 'span.e1j9birj0').text).amount.__int__()
                try:
                    image_urls = card.find_element(By.CSS_SELECTOR, 'div.app-catalog-lxji0k').find_element(
                        By.CSS_SELECTOR, 'img.app-catalog-1ljntpj').get_attribute('src')
                except NoSuchElementException:
                    try:
                        image_urls = card.find_element(By.CSS_SELECTOR, 'div.app-catalog-bv8utj').find_element(
                            By.CSS_SELECTOR, 'img.app-catalog-15kpwh2').get_attribute('src')
                    except NoSuchElementException:
                        image_urls = ''
                try:
                    cur = conn.cursor()
                    cur.execute(f"SELECT tag,info,shops FROM {cat_name} WHERE tag = ?", (item_tuple[0],))
                    db_item = cur.fetchone()
                    assert db_item is not None
                    shops = dict(json.loads(db_item[2]))
                    shops.update(citilink={"price": price, "url": url})
                    cur.execute(f"update {cat_name} set shops = ? where (tag = ?)",
                                (json.dumps(shops), item_tuple[0]))
                    counter += 1
                except AssertionError:
                    print(f'there is no such tag in the table: {item_tuple[0]}')
                    cur = conn.cursor()
                    shops = dict()
                    shops.update(citilink={"price": price, "url": url})
                    cur.execute(f"insert into {cat_name} values (?,?,?,?)",
                                (item_tuple[0], '', json.dumps(shops), image_urls))
                    print('item added')
                    add_counter += 1
            try:
                pagination = driver.find_element(By.CSS_SELECTOR, 'div.app-catalog-1bvjdtk')
                WebDriverWait(pagination, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'button.app-catalog-1ryoxjb')))
                ActionChains(driver).scroll_to_element(pagination).perform()
                pages = pagination.find_elements(By.CSS_SELECTOR, 'a.app-catalog-peotpw')
                time.sleep(20)
                next_page = pages[len(pages)-1].get_attribute('href')
                driver.switch_to.new_window('tab')
                driver.get(next_page)
                time.sleep(10)
                raise TimeoutException
            except TimeoutException:
                print(f'the end with {counter} items and {add_counter} items')
                conn.commit()
                driver.quit()
                break

        except TimeoutException:
            driver.quit()
            break

def get_tuple(page, cat_name):
    info = dict()
    match cat_name:
        case 'cpu':
            info_table = page.find_element(By.CSS_SELECTOR, 'ul.app-catalog-q1moq7')
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix('процессор ')
            part_name = full_name.split(',')[0]
            line = ''
            if part_name.find('intel') != -1:
                info['author'] = 'intel'
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'celeron'])
            else:
                info['author'] = 'amd'
                lines = list(
                    ['sempron','athlon', 'a6', 'a8', 'a12', 'epyc', 'ryzen threadripper', 'ryzen 3',
                     'ryzen 5', 'ryzen 7', 'ryzen 9'])
            for line_name in lines:
                if part_name.find(line_name) != -1:
                    line = line_name
                    if part_name.find('ryzen') != -1 and part_name.find('pro') != -1:
                        line = f'{line_name} pro'
                    info['line'] = line
                    break
            if line == 'pentium':
                part_name = str(part_name).replace(' gold', '').replace(' dual-core', '')
            if line == '':
                print(part_name)
                print('SOMETHING WRONG WITH THE NAME')
            if full_name.find('box') != -1:
                delivery_type = 'box'
            else:
                delivery_type = 'oem'
            part_name = f'{part_name} {delivery_type}'
            return part_name
        case 'mb':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'материнская плата ')
            if re.search('ret', full_name) is not None:
                print(full_name)
                raise ValueError
            part_name = full_name
            return part_name
        case 'ram':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'оперативная память ')
            name = re.search('( ddr[0-9]* - [0-9]*x [0-9]*гб)|( ddr[0-9]* - [0-9]*гб| ddr[0-9]*l - [0-9]*гб)',full_name)
            if name.group() is not None:
                try:
                    part_name = full_name.removesuffix(name.group()).rsplit(' ',maxsplit=1)[1]
                except IndexError:
                    print(full_name)
                    raise ValueError
            else:
                raise ValueError
            return part_name, json.dumps(info)
        case 'gpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'видеокарта ')
            info_table = page.find_element(By.CSS_SELECTOR, 'ul.app-catalog-q1moq7')
            sh_specs = info_table.find_elements(By.CSS_SELECTOR, 'li.app-catalog-12y5psc')
            model = sh_specs[0].text.split(': ')[1].split(',')[0]
            try:
                part_name = page.find_element(By.CSS_SELECTOR,'a.app-catalog-9gnskf').get_attribute('title').split('[')[1].split(']')[0]
            except IndexError:
                part_name = full_name.split(f'{model} ')[1]
                if re.search('sapphire', full_name) is not None:
                    part_name = part_name.split(' ')[0]
            return part_name
        case 'ssd':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'ssd накопитель ')
            if re.search('ret', full_name) is not None:
                print(full_name)
                raise ValueError
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name
        case 'hdd':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'ssd накопитель ')
            if re.search('ret', full_name) is not None:
                print(full_name)
                raise ValueError
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name
        case 'spu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'блок питания ')
            part_name = full_name.split(' ', maxsplit=1)[1].split(',')[0]
            return part_name
        case 'pc_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'корпус ')
            part_name = full_name.split(' ', maxsplit=1)[1].split(',')[0]
            return part_name
        case 'cool_cpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'устройство охлаждения(кулер) ')
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name
        case 'cool_lck':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'система водяного охлаждения ')
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name
        case 'cool_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'вентилятор ')
            part_name = full_name.rsplit(' ', maxsplit=1)[1]
            return part_name, json.dumps(info)


if __name__ == '__main__':
    search_hrefs('moduli-pamyati','sorting=price_asc&pf=discount.any%2Crating.any&f=discount.any%2Crating.any%2C2798_28&pprice_min=590&pprice_max=34990&price_min=590&price_max=34990&view_type=list', 'ram')
