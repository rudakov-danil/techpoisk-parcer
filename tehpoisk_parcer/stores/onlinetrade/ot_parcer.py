import json
import re
import time
import sqlite3
import undetected_chromedriver as uc
from price_parser import Price
from undetected_chromedriver import ChromeOptions
from selenium import webdriver

from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException

options = ChromeOptions()
options.set_capability("pageLoadStrategy", "eager")
driver = uc.Chrome(options=options, driver_executable_path='chromedriver.exe', version_main=114)
og_tab = driver.current_window_handle
driver.maximize_window()
driver.switch_to.new_window('tab')
conn = sqlite3.connect('../test_items.db')


# create unique search presets for each category as a list/dict
def search_hrefs(cat_link, cat_name):
    cat_id = cat_link.rsplit('c', maxsplit=1)[1]
    # driver.get(f'https://www.onlinetrade.ru/catalogue/{cat_link}/?sort=price-asc&selling[]=1&cat_id={cat_id}&browse_mode=4&per_page=45&naznachenie[]=%E4%EB%FF%20%F1%E8%F1%F2%E5%EC%ED%EE%E3%EE%20%E1%EB%EE%EA%E0')
    driver.get('https://www.onlinetrade.ru/catalogue/operativnaya_pamyat-c341/?selling[]=1&price1=550&price2=91699&naznachenie[]=%E4%EB%FF%20%F1%E8%F1%F2%E5%EC%ED%EE%E3%EE%20%E1%EB%EE%EA%E0&advanced_search=1&preset_id=0&rating_active=0&special_active=1&selling_active=1&producer_active=1&price_active=0&naznachenie_active=1&memory_type_ram_active=1&form_faktor_active=1&frequancy_active=1&obem_odnogo_modulya_active=1&volume_active=1&kol_modulei_active=1&podsvetka_active=1&latentnost_active=1&poddergka_ecc_active=1&buferizovannaya_active=1&cat_id=341&per_page=45&page=0&browse_mode=4&sort=price-asc&page=0')
    time.sleep(10)
    while True:
        time.sleep(10)
        try:
            webpage = WebDriverWait(driver, 15).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div.goods__items')))
        except TimeoutException as e:
            driver.quit()
            conn.commit()
            print(e)
            return
        items = webpage.find_elements(By.CSS_SELECTOR, 'div.indexGoods__item')
        for item in items:
            try:
                shops = dict()
                try:
                    item_tuple = get_tuple(item, cat_name)
                except ValueError:
                    print('----------------------bad item-------------------------------')
                    continue
                name = item.find_element(By.CSS_SELECTOR, 'a.indexGoods__item__name')
                url = name.get_attribute('href')
                price = Price.fromstring(
                    item.find_element(By.CSS_SELECTOR, 'span.price.js__actualPrice').text).amount.__int__()
                shops.update(onlinetrade={'price': price, 'url': url})
                image_urls = item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                print('got an item')
                cur = conn.cursor()
                try:
                    cur.execute(f"""insert into {cat_name} values (?,?,?,?)""",(item_tuple[0],item_tuple[1],json.dumps(shops),image_urls))
                except sqlite3.ProgrammingError as e:
                    raise e
                except sqlite3.IntegrityError:
                    print(f'item conflict, please check item with info: {item_tuple}')
            except Exception as e:
                conn.commit()
                raise e
        time.sleep(10)
        print('all urls on a page has been added')
        try:
            WebDriverWait(driver, 15).until(expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.button__gray')))
            print('there is a button')
            link = driver.find_element(By.CSS_SELECTOR, 'a.js__paginator__linkNext')
            time.sleep(25)
            link.click()
            print('button clicked')
            time.sleep(25)
            # УБРАТЬ ПОТОМ
            raise TimeoutException
        except TimeoutException:
            print('end of a category')
            conn.commit()
            break
        except Exception as err:
            print('KeyboardInterrupt')
            conn.commit()
            raise err
    driver.quit()
    conn.commit()

# сделать отдельную функцию для дозаполнения данных с других магазинов



# might do an insta item fill, while creating a list of items
def get_items(table_name, cat_name):
    try:
        with open(f'{cat_name}_urls.json') as urls_json:
            urls = json.load(urls_json)
            for url in urls:
                if urls[url] is True:
                    continue
                time.sleep(2)
                driver.get(url)
                time.sleep(5)
                try:
                    WebDriverWait(driver, 15).until(
                        expected_conditions.element_to_be_clickable((By.ID, 'ui-id-2'))).click()
                except TimeoutException:
                    driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[3]/form/div/div/input[3]').click()
                    WebDriverWait(driver, 15).until(
                        expected_conditions.element_to_be_clickable((By.ID, 'ui-id-2'))).click()
                # driver.find_element(By.ID, 'ui-id-2').click()
                time.sleep(10)
                # tag = driver.find_element(By.CSS_SELECTOR, 'div.descr__techicalBrand__item')\
                #     .find_element(By.CSS_SELECTOR, 'span.nowrap').text.lower().removesuffix('#aab')
                # spec_parent = driver.find_element(By.CSS_SELECTOR, 'div.productPage__shortProperties')
                # short_specs = ''
                # for chart in spec_parent.find_elements(By.CSS_SELECTOR, 'li.featureList__item'):
                #     short_specs += f'{chart.text} | '
                # assert short_specs != ''
                # full_spec_par = driver.find_element(By.CSS_SELECTOR, 'ul.featureList.js__backlightingClick')
                # full_specs = ''
                # for spec in full_spec_par.find_elements(By.CSS_SELECTOR, 'li.featureList__item'):
                #     full_specs += f'{spec.text} | '
                # assert full_specs != ''
                # image_parent = driver.find_element(By.CSS_SELECTOR, 'div.productPage__displayedItem__images')
                # try:
                #     imgs = image_parent.find_elements(By.CSS_SELECTOR, 'div.swiper-slide')
                #     imgs_url = ''
                #     assert len(imgs) != 0
                #     for img in imgs:
                #         imgs_url += f'{img.find_element(By.CSS_SELECTOR, "a.displayedItem__images__thumbLink").get_attribute("href")} | '
                # except AssertionError:
                #     imgs_url = driver.find_element(By.CSS_SELECTOR, 'a.productPage__displayedItem__images__bigLink').get_attribute('href')
                # price = int(driver.find_element(By.CSS_SELECTOR, 'div.catalog__displayedItem__actualPrice').find_element(By.CSS_SELECTOR, 'span.js__actualPrice').text.removesuffix('₽').replace(' ', ''))
                # name = driver.find_element(By.CSS_SELECTOR, 'div.productPage__card').find_element(By.CSS_SELECTOR, 'h1').text
                # item_tuple = (
                #     tag, name, short_specs, full_specs, json.dumps({'onlinetrade': {'price': price, 'url': url}}),
                #     imgs_url)
                # try:
                #     cur = conn.cursor()
                #     cur.execute(f"INSERT INTO {table_name} "
                #                 "VALUES (?,?,?,?,?,?)", item_tuple)
                #     urls[url] = True
                # except sqlite3.Error as e:
                #     raise e
                driver.close()
                driver.switch_to.window(og_tab)
                driver.switch_to.new_window('tab')
                time.sleep(5)
            conn.commit()
            conn.close()
        with open(f'{cat_name}_urls.json', 'w') as file:
            json.dump(urls, file)
            driver.quit()
    except KeyboardInterrupt as e:
        conn.commit()
        conn.close()
        with open(f'{cat_name}_urls.json', 'w') as file:
            json.dump(urls, file)
            driver.quit()
        raise e


# вместо page нужно просто карточку товара навести
def get_tuple(page, cat_name):
    info = dict()
    match cat_name:
        case 'cpu':
            # intel core i3-12400fk oem
            # ВСЮ ИНФУ О ПРОЦЕССОРАХ МОЖНО БРАТЬ С САЙТА, НЕ ПЕРЕХОДЯ НА ССЫЛКУ
            full_name = page.find_element(By.CSS_SELECTOR, 'a.indexGoods__item__name').text.lower()
            parent = page.find_element(By.CSS_SELECTOR, 'ul.featureList')
            sh_specs = parent.find_elements(By.CSS_SELECTOR, 'li.featureList__item')
            part_name = full_name.split(' box')[0].split(' oem')[0].split(' оем')[0]
            part_name = part_name.rsplit(' ', maxsplit=1)[0]
            part_name = part_name.replace('-', ' ')
            line = ''
            if part_name.find('intel') != -1:
                info['author'] = 'intel'
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'pentium', 'celeron'])
            else:
                info['author'] = 'amd'
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
                part_name = str(part_name).replace(' gold', '')
            if part_name.find('threadripper') != -1 and part_name.find('pro') == -1:
                part_name = part_name.replace('threadripper', 'threadripper pro')
            print(line)
            model = part_name.split(line)[1].strip()
            info['model'] = model
            delivery_type = sh_specs[len(sh_specs)-1].text.split(': ')[1].lower()
            part_name = f'{part_name} {delivery_type}'
            info['delivery_type'] = delivery_type
            info['socket'] = sh_specs[0].text.split(': ')[1].replace('-', '')
            info['core_number'] = int(sh_specs[2].text.split(': ')[1].split(' ')[0])
            info['core'] = sh_specs[1].text.split(': ')[1]
            info['clock_frequency'] = float(sh_specs[5].text.split(': ')[1].split(' ')[0])*1000
            try:
                boost_clock_frequency = float(sh_specs[4].text.split(': ')[1].split(' ')[0])*1000
            except ValueError:
                boost_clock_frequency = 0
            info['boost_clock_frequency'] = boost_clock_frequency
            info['threads_number'] = int(sh_specs[3].text.split(': ')[1].split(' ')[0])
            try:
                info['tdp'] = int(sh_specs[7].text.split(': ')[1].split(' ')[0])
            except ValueError:
                info['tdp'] = 0
            info['tech_process'] = 0
            info['integrated_video_core'] = sh_specs[6].text.split(': ')[1]
            print(part_name, info)
            image_urls = page.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
            return part_name, json.dumps(info), image_urls
        case 'mb':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.indexGoods__item__name').text.lower()
            if re.search('процессором|уценка', full_name) is not None:
                raise ValueError
            parent = page.find_element(By.CSS_SELECTOR, 'ul.featureList')
            sh_specs = parent.find_elements(By.CSS_SELECTOR, 'li.featureList__item')
            sh_len = len(sh_specs)
            part_name = full_name.split(' (', maxsplit=1)[0]
            info['author'] = full_name.split(' ', maxsplit=1)[0]
            info['chipset'] = sh_specs[1].text.split(': ')[1]
            info['socket'] = sh_specs[0].text.split(': ')[1]
            info['memory_type'] = sh_specs[2].text.split(': ')[1]
            info['memory_type_amount'] = sh_specs[3].text.split(': ')[1]
            form_factor = re.search('atx|matx|e-atx|mini-itx|thin mini-itx|mini-dtx|ceb|microatx', full_name)
            if form_factor is None:
                print(full_name)
                sh_specs[sh_len-1].click()
                info['form_factor'] = sh_specs[sh_len-2].text.split(': ')[1]
            else:
                info['form_factor'] = form_factor.group()
            info['m2_amount'] = 0
            print(full_name, info)
            return part_name, json.dumps(info)
            # потенциальные танцы с бубном
        case 'ram':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.indexGoods__item__name').text.lower().removeprefix('оперативная память ')
            if re.search('уценка', full_name) is not None:
                raise ValueError
            parent = page.find_element(By.CSS_SELECTOR, 'ul.featureList')
            sh_specs = parent.find_elements(By.CSS_SELECTOR, 'li.featureList__item')
            sh_len = len(sh_specs)
            brand = re.search('(hp)|(digma)|(silicon power)', full_name)
            if brand is not None:
                if brand.group(1) is not None:
                    part_name = full_name.rsplit(' ',maxsplit=1)[1].removeprefix('(').removesuffix('#abb')
                elif brand.group(2) is not None:
                    memory_amount = re.search('[0-9]*gb', full_name).group().removesuffix('gb')
                    num = f'0{memory_amount}'if len(memory_amount) == 2 else f"00{memory_amount}"
                    part_name = f'dgmad{sh_specs[0].text.lower().split(": ddr")[1].removesuffix("l")}{sh_specs[2].text.lower().split(": ")[1].removesuffix("мгц")[1]}{num}d'
                else:
                    try:
                        part_name = full_name.rsplit('(', maxsplit=1)[1].split(')')[0].split('/')[0]
                    except IndexError:
                        print(full_name)
                        raise ValueError
            else:
                try:
                    part_name = full_name.rsplit('(', maxsplit=1)[1].split(')')[0]
                except IndexError:
                    print(full_name)
                    raise ValueError
            author = re.search('kingston|amd|patriot memory|netac|g.skill|acer|adata|afox|agi|apacer|biwintech|cbr|corsair|crucial|digma|exegate|foxline|geil|gigabyte|hikvision|hp|hyxis|infortrend|kimtigo|kingmax|kingspec|ocpc|qnap|qumo|samsung|silicon power|team group|terramaster|thermaltake|transcend|тми', full_name)
            info['author'] = author.group()
            amount = sh_specs[sh_len - 1].text.lower().split(': ')[1]
            memory_amount = re.search('[0-9]*gb', full_name)
            if memory_amount is not None:
                info['memory_amount'] = memory_amount.group().split('gb')[0]
            else:
                single_mod = int(sh_specs[sh_len-2].text.lower().split(' гб')[0])
                info['memory_amount'] = single_mod*amount
            info['memory_type'] = sh_specs[0].text.split(': ')[1]
            info['memory_frequency'] = sh_specs[2].text.split(': ')[1]
            info['is_kit'] = amount
            info['memory_speed'] = sh_specs[3].text.split(': ')[1]
            info['latency'] = sh_specs[4].text.split(': ')[1]
            info['is_XMP'] = False
            print(full_name,info)
            # норм поиск, добавить find'Gb', но нет проверки на xmp
            return part_name, json.dumps(info)
        case 'gpu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.indexGoods__item__name').text.lower().removeprefix(
                'оперативная память ')
            if re.search('уценка', full_name) is not None:
                raise ValueError
            parent = page.find_element(By.CSS_SELECTOR, 'ul.featureList')
            sh_specs = parent.find_elements(By.CSS_SELECTOR, 'li.featureList__item')
            sh_len = len(sh_specs)
            info['author'] = ''
            info['model'] = ''
            info['video_card_author'] = ''
            info['memory_amount'] = ''
            info['interface'] = ''
            info['clock_frequency'] = ''
            info['memory_type'] = ''
            info['memory_frequency'] = ''

            # потенциальные танцы с бубном
            print(1)
        case 'ssd':

            # потенциальные танцы с бубном
            print(1)
        case 'hdd':
            # потенциальные танцы с бубном
            print(1)
        case 'spu':
            full_name = page.find_element(By.CSS_SELECTOR, 'a.indexGoods__item__name').text.lower().removeprefix(
                'блок питания ')
            if re.search('уценка', full_name) is not None:
                raise ValueError
            parent = page.find_element(By.CSS_SELECTOR, 'ul.featureList')
            sh_specs = parent.find_elements(By.CSS_SELECTOR, 'li.featureList__item')

            info['author'] = ''
            info['power'] = ''
            info['form_factor'] = ''
            info['fan_size'] = ''
            info['certificate'] = ''

            # потенциальные танцы с бубном
            print(1)
        case 'pc_case':
            # потенциальные танцы с бубном
            print(1)
        case 'cool_cpu':
            # потенциальные танцы с бубном
            print(1)
        case 'cool_lck':
            # потенциальные танцы с бубном
            print(1)
        case 'cool_case':
            # потенциальные танцы с бубном
            print(1)

    # cur = conn.cursor()
    # try:
    #     cur.execute()
    # except:
    #     print('some error while using database')
    #


if __name__ == '__main__':
    search_hrefs('operativnaya_pamyat-c341', 'ram')
