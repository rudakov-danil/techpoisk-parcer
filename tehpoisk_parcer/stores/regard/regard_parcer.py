import os
import sqlite3
import time
import json
import re
from price_parser import Price
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

options = ChromeOptions()
options.headless = True
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options, driver_executable_path='chromedriver.exe', version_main=122)
driver.maximize_window()
og_tab = driver.current_window_handle
driver.switch_to.new_window('tab')
conn = sqlite3.connect('test_items.db')

cats = list({('1001/processory', 'cpu', ''),
             ('1000/materinskie-platy', 'mb', ''),
             ('1010/operativnaya-pamyat', 'ram', '?q=eyJieUNoYXIiOnsiNDgiOnsidmFsdWVzIjpbMTc4XSwiZXhjZXB0IjpmYWxzZX19fQ'),
             ('1013/videokarty', 'gpu', ''),
             ('1015/nakopiteli-ssd', 'ssd', ''),
             ('1014/zhestkie-diski-hdd', 'hdd', ''),
             ('1225/bloki-pitaniya', 'spu', ''),
             ('1032/korpusa', 'pc_case', ''),
             ('5162/kulery-dlya-processorov', 'cool_cpu', ''),
             ('1008/vodyanoe-okhlazhdenie-svo', 'cool_lck', '?q=eyJieUNoYXIiOnsiODY0MyI6eyJ2YWx1ZXMiOlszMTA1MCwzMTA0OCwzMTA0M10sImV4Y2VwdCI6ZmFsc2V9fX0'),
             ('1004/ventilyatory-dlya-korpusa', 'cool_case', '')
             })


def parcer(cat_link,cat_name,params):
    driver.get(f'https://www.regard.ru/catalog/{cat_link}{params}')
    time.sleep(5)
    driver.find_element(By.CLASS_NAME, 'ArchiveAndModificationsControls_wrap__3wMFA').find_element(By.CSS_SELECTOR, 'div.Checkbox_wrap__Mwvom').click()
    time.sleep(1)
    # driver.find_elements(By.CSS_SELECTOR, 'button.IconRectangle_wrap__K0zz9')[1].click()
    time.sleep(3)
    driver.find_element(By.CSS_SELECTOR, 'button.PaginationViewChanger_countSetter__btn__SNmYX').click()
    time.sleep(3)
    elements = driver.find_elements(By.CSS_SELECTOR, 'div.PaginationViewChanger_countSetter__option__Gmsq4')
    element_to_click = elements[3]
    element_to_click.click()
    time.sleep(5)
    counter = 0
    add_counter = 0
    while True:
        items = driver.find_elements(By.CSS_SELECTOR, 'div.CardMain_wrap___uIuh.CardMain_tile__2jDya')
        for item in items:
            url = item.find_element(By.CSS_SELECTOR, 'a.CardText_link__C_fPZ').get_attribute('href')
            try:
                price = Price.fromstring(
                    item.find_element(By.CSS_SELECTOR, 'span.CardPrice_price__YFA2m').text).amount.__int__()
            except NoSuchElementException:
                print("Not in a stock")
                continue
            try:
                item_tuple = get_tuple(item, cat_name)
                print(item_tuple)
            except ValueError:
                print('----------------------bad item-------------------------------')
                continue
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT tag,info,shops FROM {cat_name} WHERE tag = ?", (item_tuple,))
                db_item = cur.fetchone()
                assert db_item is not None
                shops = dict(json.loads(db_item[2]))
                shops.update(regard={"price": price, "url": url})
                print(shops)
                cur.execute(f"update {cat_name} set shops = ? where (tag = ?)",
                            (json.dumps(shops), item_tuple))
                counter += 1
            except AssertionError:
                print(f'there is no such tag in the table: {item_tuple}, adding a new tag')
                cur = conn.cursor()
                url = item.find_element(By.CSS_SELECTOR, 'a.CardText_link__C_fPZ').get_attribute('href')
                price = Price.fromstring(
                    item.find_element(By.CSS_SELECTOR, 'span.CardPrice_price__YFA2m').text).amount.__int__()
                shops = dict()
                shops.update(regard={"price": price, "url": url})
                image_urls = f"{item.find_element(By.CSS_SELECTOR, 'img.CardImageSlider_image__W65ZP').get_attribute('src')}0"
                cur.execute(f"insert into {cat_name} values (?,?,?,?,?)",
                            (item_tuple, '', json.dumps(shops), image_urls, ''))
                print('item added')
                add_counter += 1
        try:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'button.Pagination_loadMore__u1Wm_')))
            pages = driver.find_elements(By.CSS_SELECTOR, 'li.Pagination_item__t3jDI')
            active_page = False
            for page in pages:
                if active_page:
                    page.click()
                    print('page clicked')
                    time.sleep(5)
                    break
                if page.get_attribute('class') == 'Pagination_item__t3jDI Pagination_item_active__EY7gp':
                    active_page = True
            time.sleep(7)
        except TimeoutException:
            print(f'last page, total items extracted: {counter}')
            print(f'new items {add_counter}')
            conn.commit()
            break
        except KeyboardInterrupt as e:
            conn.commit()
            driver.close()
            driver.switch_to(og_tab)
            raise e
        finally:
            print('THE END')
            conn.commit()
            driver.quit()
            os.system("taskkill /im chrome.exe /f")
    driver.close()
    driver.switch_to.window(og_tab)
    driver.switch_to.new_window('tab')


def get_tuple(page, cat_name):
    info = dict()
    match cat_name:
        case 'cpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'процессор ')
            part_name = re.search('intel[\w\W]*|amd[\w\W]*', full_name).group()
            part_name = part_name.split(' box')[0].split(' oem')[0].replace(' - ', ' ').replace('-', ' ')
            line = ''
            if part_name.find('intel') != -1:
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'celeron'])
            else:
                lines = list(
                    ['sempron', 'athlon', 'athlon x2', 'a6', 'fx', 'a8', 'a12', 'epyc', 'ryzen threadripper', 'ryzen 3',
                     'ryzen 5', 'ryzen 7', 'ryzen 9'])
            for line_name in lines:
                if part_name.find(line_name) != -1:
                    line = line_name
                    if line_name == 'athlon' and part_name.find('pro') != -1:
                        line = 'pro athlon'
                    if part_name.find('ryzen') != -1 and part_name.find('pro') != -1:
                        line = f'{line_name} pro'
                    info['line'] = line
                    break
            if line == 'pentium':
                part_name = part_name.replace(' gold', '')
            if part_name.find('threadripper') != -1 and part_name.find('ryzen') == -1:
                part_name = part_name.replace('threadripper', 'ryzen threadripper')
            print(line)
            if full_name.find('box (без кулера)') != -1:
                delivery_type = 'box (без кулера)'
            elif full_name.find('box') != -1:
                delivery_type = 'box'
            elif full_name.find('oem (с кулером)') != -1:
                delivery_type = 'oem (с кулером)'
            else:
                delivery_type = 'oem'
            part_name = f'{part_name} {delivery_type}'
            return part_name
        case 'mb':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix('материнская плата ')
            if re.search('onboard', full_name) is not None:
                raise ValueError
            part_name = full_name
            return part_name
        case 'ram':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix('оперативная память ')
            print(full_name)
            try:
                part_name = full_name.split('(', maxsplit=1)[1].split(')')[0]
            except IndexError:
                raise ValueError
            return part_name
        case 'gpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'видеокарта ')
            try:
                part_name = page.find_element(By.CSS_SELECTOR, 'img.CardImageSlider_image__W65ZP').get_attribute('alt').rsplit('(', maxsplit=1)[1].split(')')[0].lower()
            except NoSuchElementException:
                print('no pic')
                part_name = full_name.split('(')[1].split(')')[0]
            return part_name
        case 'ssd':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'накопитель ssd ')
            try:
                part_name = full_name.split(' (')[1].split(')')[0]
            except IndexError:
                part_name = full_name.split(' ',maxsplit=1)[1]
            return part_name
        case 'hdd':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower()
            part_name = full_name.split(' (')[1].split(')')[0]
            if re.search('ultrastar', full_name) is not None:
                part_name = full_name.rsplit(' (', maxsplit=1)[1].split(')')[0]
            return part_name
        case 'spu':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'блок питания ')
            part_name = full_name.split(' ', maxsplit=1)[1].rsplit(' (', maxsplit=1)[0]
            return part_name
        case 'pc_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'корпус ')
            part_name = full_name.rsplit(' (',maxsplit=1)[0].rsplit('usb',maxsplit=1)[0]
            spu = re.search(' [0-9]*w', part_name)
            if spu is not None:
                part_name = part_name.replace(f' {spu.group()}','')
            return part_name
        case 'cool_cpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix('кулер ')
            part_name = full_name.split(' (')[0]
            return part_name
        case 'cool_lck':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'система жидкостного охлаждения ').removeprefix('система жидкостного охлаждения : ')
            part_name = full_name.split(' (')[0]
            return part_name
        case 'cool_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'div.CardText_title__7bSbO').text.lower().removeprefix(
                'вентиляторы ').removeprefix(
                'вентилятор ').removeprefix(
                'для корпуса ')
            part_name = full_name.split(' (')[0].split(',')[0].split(' [')[0]
            return part_name


if __name__ == '__main__':
    # for cat in cats:
    #     print(cat)
    parcer('1013/videokarty', 'gpu', '')
    conn.close()
    driver.quit()

# for cpu replace(' - ', '')
# driver.execute_script("window.history.go(-1)")
