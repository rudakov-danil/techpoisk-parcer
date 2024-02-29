from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
import sqlite3
import json
import time
import random

conn = sqlite3.connect(r'C:\Python_projects\parcer\db\products.db')
c = conn.cursor()

#получение url из таблицы products
c.execute("SELECT url FROM products")
urls = c.fetchall()

# Список прокси
proxies = [
  '45.8.211.113:80',
  '45.8.211.90:80',
  '185.221.160.176:80',
]

proxy_index = 0


def get_proxy():
    global proxy_index

    proxy = proxies[proxy_index]
    proxy_index = (proxy_index + 1) % len(proxies)

    return proxy

def scrape_full_characteristics_regard():
    for url in urls:

        proxy = get_proxy()
        options = ChromeOptions()
        options.add_argument('--proxy-server=%s' % proxy)

        driver = uc.Chrome(options=options)

        proxy_options = {
            'proxy': {
                'http': proxy,
                'https': proxy,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

        driver.get(url[0])

        characteristics = []

        chars = driver.find_elements(By.CSS_SELECTOR, "div.CharacteristicsItem_item__QnlK2")

        for char in chars:
            key = char.find_element(By.CSS_SELECTOR, "div.CharacteristicsItem_left__ux_qb").text.split('\n')[0]
            value = char.find_element(By.CSS_SELECTOR, "div.CharacteristicsItem_value__fgPkc").text

            characteristics.append({
                'key': key,
                'value': value
            })
        time.sleep(random.randint(3,10))

        print(characteristics)

        # Преобразуем список со словарями в JSON
        characteristics_json = json.dumps(characteristics, ensure_ascii=False)

        # Сохраняем данные в виде JSON
        c.execute("UPDATE products SET characteristics=? WHERE url=?",
                (characteristics_json, url[0]))

        conn.commit()

        # закрыть драйвер через N итераций
        if driver.requests % 10 == 0:
            driver.quit()
            driver = uc.Chrome(options=options)

scrape_full_characteristics_regard()