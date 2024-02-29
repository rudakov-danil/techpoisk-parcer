from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
import sqlite3
import time

conn = sqlite3.connect(r'C:\Python_projects\parcer\db\products.db')
c = conn.cursor()

# создание таблицы
#c.execute('''CREATE TABLE products (name text, url text, price text, image text)''')

url_category_regard = {'processors': 'https://www.regard.ru/catalog/1001/processory'}


options = ChromeOptions()
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options, driver_executable_path=r"C:\Python_projects\parcer\chromedriver.exe")
driver.maximize_window()

#запуск основной страницы, пагинация и обработка ошибки пагинации
def pagination(category_url):
    driver.get(category_url)
    driver.find_element(By.CLASS_NAME, 'ArchiveAndModificationsControls_wrap__3wMFA').find_element(By.CSS_SELECTOR,
                                                                                                   'div.Checkbox_wrap__Mwvom').click()

    while True:

        scrape_category_regard()

        try:
            # проверка наличия кнопки пагинации
            next_page = driver.find_element(By.CSS_SELECTOR, "button.Pagination_loadMore__u1Wm_")
        except NoSuchElementException:
            scrape_category_regard()
            break

        # скролл до кнопки пагинации
        driver.execute_script("arguments[0].scrollIntoView();", next_page)
        time.sleep(1)

        # Кликаем по кнопке
        next_page.click()

#глобальная переменная для хранения спарсенных url
scraped_urls = []

#парсинг элементов и запись в БД
def scrape_category_regard():

    # храним url товаров, которые уже спарсили
    global scraped_urls

    product_elements = driver.find_elements(By.CSS_SELECTOR, 'div.Card_listing__nGjbk.Card_wrap__hES44')

    # Извлекаем данные со страницы
    for product in product_elements:
        name = product.find_element(By.CSS_SELECTOR, "div.CardText_title__7bSbO").text
        url = product.find_element(By.CSS_SELECTOR, "a.CardText_link__C_fPZ").get_attribute("href")
        price = product.find_element(By.CSS_SELECTOR, "div.CardPrice_bottom__u40fT").text
        # in_stock = product.find_element(By.CSS_SELECTOR, "p.Card_inStockText__ciAyD").text
        image = product.find_element(By.CSS_SELECTOR, "img.CardImageSlider_image__W65ZP").get_attribute("src")

        if url not in scraped_urls:
            # Сохраняем данные в таблицу
            c.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?)",
                        (name, url, price, image, 'null'))

            scraped_urls.append(url)
        conn.commit()

scrape_category(url_category_regard['processors'])
