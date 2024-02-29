from selenium.webdriver.common.by import By
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

options = ChromeOptions()
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options, driver_executable_path=r"C:\Python_projects\parcer\chromedriver.exe")
driver.maximize_window()

def scrape_full_characteristics_regard():
    for url in urls:
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

scrape_full_characteristics_regard()