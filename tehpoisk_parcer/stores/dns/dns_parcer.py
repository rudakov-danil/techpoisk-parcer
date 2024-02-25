import json
import queue
import re
import time
import sqlite3
import undetected_chromedriver as uc
from price_parser import Price
from selenium.webdriver import ActionChains
from undetected_chromedriver import ChromeOptions
from translatepy import Translator
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

options = ChromeOptions()
options.set_capability("pageLoadStrategy", "none")
driver = uc.Chrome(options=options, driver_executable_path='../chromedriver.exe', version_main=116)
og_tab = driver.current_window_handle
driver.maximize_window()
conn = sqlite3.connect('../test_items.db')

categories = list(
    (('https://www.dns-shop.ru/catalog/17a899cd16404e77/processory/', 'cpu'),
    ('https://www.dns-shop.ru/catalog/17a89a0416404e77/materinskie-platy/', 'mb'),
    ('https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/', 'gpu'),
    ('https://www.dns-shop.ru/catalog/17a89a3916404e77/operativnaya-pamyat-dimm/', 'ram'),
    ('https://www.dns-shop.ru/catalog/17a89c5616404e77/korpusa/', 'pc_case'),
    ('https://www.dns-shop.ru/catalog/17a89c2216404e77/bloki-pitaniya/', 'spu'),
    ('https://www.dns-shop.ru/catalog/8a9ddfba20724e77/ssd-nakopiteli/', 'ssd'),
    ('https://www.dns-shop.ru/catalog/dd58148920724e77/ssd-m2-nakopiteli/', 'ssd'),
    ('https://www.dns-shop.ru/catalog/17a8914916404e77/zhestkie-diski-35/', 'hdd'),
    ('https://www.dns-shop.ru/catalog/17a9cc2d16404e77/kulery-dlya-processorov/', 'cool_cpu'),
    ('https://www.dns-shop.ru/catalog/17a9cc9816404e77/sistemy-zhidkostnogo-oxlazhdeniya/', 'cool_lck'),
    ('https://www.dns-shop.ru/catalog/17a9cf0216404e77/ventilyatory-dlya-korpusa/', 'cool_case'))
     )


def search_hrefs(cat_link: str, cat_name):
    driver.get(cat_link)
    try:
        driver.find_element(By.CSS_SELECTOR, 'button.v-confirm-city__btn_foO').click()
    except NoSuchElementException:
        pass
    add_counter = 0
    counter = 0
    while True:
        try:
            webpage = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.products-page__list')))
        except TimeoutException as e:
            driver.quit()
            print(e)
            return
        time.sleep(5)
        items_list = webpage.find_elements(By.CSS_SELECTOR, 'div.catalog-product')
        for item in items_list:
            try:
                item_tuple = get_tuple(item, cat_name)
            except ValueError:
                print('----------------------bad item-------------------------------')
                continue
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT tag,shops FROM {cat_name} WHERE tag = ?", (item_tuple,))
                db_item = cur.fetchone()
                assert db_item is not None
                shops = dict(json.loads(db_item[1]))
                url = item.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').get_attribute('href')
                price = Price.fromstring(item.find_element(By.CSS_SELECTOR, 'div.product-buy__price').text).amount.__int__()
                shops.update(dns={'price': price, 'url': url})
                cur.execute(f"update {cat_name} set shops = ? where (tag = ?)",
                            (json.dumps(shops), item_tuple))
                counter += 1
            except AssertionError:
                print(f'there is no such tag in the table: {item_tuple}')
                cur = conn.cursor()
                url = item.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').get_attribute('href')
                price = Price.fromstring(
                    item.find_element(By.CSS_SELECTOR, 'div.product-buy__price').text).amount.__int__()
                image_urls = item.find_element(By.CSS_SELECTOR, 'div.catalog-product__image').find_element(
                    By.CSS_SELECTOR, 'source').get_attribute('srcset')
                shops = dict()
                shops.update(dns={"price": price, "url": url})
                cur.execute(f"insert into {cat_name} values (?,?,?,?,?)",
                            (item_tuple, '', json.dumps(shops), image_urls, ''))
                print('item added')
                add_counter += 1
        try:
            # Пагинация, работает у всех категорий одинаково
            show_more = WebDriverWait(driver, 15).until(expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button.pagination-widget__show-more-btn')))
            print('there is a button')
            # link = show_more.get_attribute('data-url')
            # curr_page = driver.current_window_handle
            # if driver.window_handles.__len__() > 6:
            #     driver.switch_to.window(driver.window_handles[0])
            #     driver.close()
            #     driver.switch_to.window(driver.window_handles[0])
            #     driver.close()
            #     driver.switch_to.window(curr_page)
            # driver.switch_to.new_window('tab')
            # driver.get(f'https://www.dns-shop.ru{link}&stock=now')
            pages = driver.find_element(By.CSS_SELECTOR, 'ul.pagination-widget__pages')
            page = pages.find_elements(By.CSS_SELECTOR, 'li.pagination-widget__page')
            next_page = page[len(page)-2]
            ActionChains(driver).scroll_to_element(next_page).perform()
            time.sleep(5)
            ActionChains(driver).move_to_element(next_page).click().perform()
            time.sleep(20)
            print('new page')
        except TimeoutException:
            print('end of a category')
            print(counter, add_counter)
            conn.commit()
            conn.close()
            break
    driver.quit()

def get_tuple(page, cat_name):
    match cat_name:
        case 'cpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower()
            part_name = re.search('intel[\w\W]*box|amd[\w\W]*box|intel[\w\W]*oem|amd[\w\W]*oem', full_name).group()
            line = ''
            part_name = part_name.replace('-', ' ')
            if line == 'pentium':
                part_name = str(part_name).replace(' gold', '')
            # if info['author'] == 'intel' and part_name.find('i3') != -1:
            #     line = 'core i3'
            # print(f'part_name {part_name}')
            cooler = re.search('(box[\w\W]* кулер)|(box)|(oem[\w\W]* кулер)',full_name)
            if cooler is not None:
                if cooler.group(2) is not None:
                    part_name = part_name.replace('box', 'box (без кулера)')
                else:
                    part_name = part_name.replace('oem', 'oem (с кулером)')
            print(part_name)
            return part_name
        case 'mb':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix(
                'материнская плата ')
            part_name = full_name.split(' [')[0]
            return part_name
        case 'ram':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix(
                'оперативная память ')
            try:
                part_name = full_name.split(' [', maxsplit=1)[1].split(']')[0]
            except IndexError:
                raise ValueError
            print(part_name)
            return part_name
        case 'gpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix(
                'видеокарта ')
            try:
                part_name = full_name.split(' [', maxsplit=1)[1].split(']')[0].replace('rev', '').removesuffix(' 1.1').removesuffix(' 1.0').removeprefix('geforce ')
            except IndexError:
                raise ValueError
            print(part_name)
            return part_name
        case 'ssd':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower()
            try:
                part_name = full_name.split(' [', maxsplit=1)[1].split(']')[0]
            except IndexError:
                raise ValueError
            print(part_name)
            return part_name
        case 'hdd':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower()
            try:
                part_name = full_name.split(' [', maxsplit=1)[1].split(']')[0]
            except IndexError:
                raise ValueError
            print(part_name)
            return part_name
        case 'spu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.app-catalog-9gnskf').text.lower().removeprefix(
                'блок питания ')
            part_name = full_name.split(' [', maxsplit=1)[0]
            print(part_name)
            return part_name
        case 'pc_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix(
                'корпус ')
            color = re.search('черный|белый|розовый|серебристый|серый|синий',full_name)
            part_name = full_name.split(' [', maxsplit=1)[0]
            if color is not None:
                color_en = Translator().translate(color.group(),'English')
                part_name = part_name.replace(color.group(),color_en.result.__str__())
                if re.search('black|white|pink|silver|gray|blue',part_name) is None:
                    part_name = f'{part_name} {color_en}'
            print(part_name)
            return part_name
        case 'cool_cpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix('кулер для процессора ')
            color = re.search('черный|белый|розовый|серебристый|серый|синий', full_name)
            part_name = full_name.split(' [', maxsplit=1)[0]
            if color is not None:
                color_en = Translator().translate(color.group(), 'English')
                part_name = part_name.replace(color.group(), color_en)
                if re.search('black|white|pink|silver|gray|blue',part_name) is None:
                    part_name = f'{part_name} {color_en}'
            print(part_name)
            return part_name
        case 'cool_lck':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix(
                'система охлаждения ').removeprefix(
                'комплект для сборки сжо ')
            part_name = full_name.split(' [', maxsplit=1)[0]
            if re.search('black|white|pink|silver|gray|blue', part_name) is None:
                print('---------------WHITE SWAP---------------')
                print(part_name)
                part_name = part_name.replace('wh', 'white')
            print(part_name)
            return part_name
        case 'cool_case':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.catalog-product__name').text.lower().removeprefix(
                'вентилятор ').removeprefix(
                'комплект вентиляторов ').removeprefix(
                'реверсный вентилятор ')
            'msi max'
            'no series rgb series tf series wf series id-cooling xf series'
            part_name = full_name.split(' [', maxsplit=1)[0]
            series = re.search('no series|rgb series|tf series|wf series|xf series', part_name)
            if series is not None:
                part_name = part_name.replace(series.group(),full_name.split('[')[1].split(']')[0])
            if re.search('msi max', part_name) is not None:
                part_name = f'msi mag max {full_name.split("[")[1].split("]")[0]}'
            print(part_name)
            return part_name



if __name__ == '__main__':
    # for cat in categories:
    #     search_hrefs(f'{cat[0]}?stock=now-today-tomorrow',cat[1])
    search_hrefs('https://www.dns-shop.ru/catalog/17a9cf0216404e77/ventilyatory-dlya-korpusa/?stock=now-today-tomorrow', 'cool_case')
