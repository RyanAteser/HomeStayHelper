import base64
import zlib
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import logging
import sqlite3
from PIL import Image
from io import BytesIO

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraping.log'
)


def create_table():
    conn = sqlite3.connect('data/listing_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vrbo_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_source BLOB,
            price TEXT,
            beds TEXT,
            ratings TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_into_db(image_data, price, beds, ratings):
    conn = sqlite3.connect('data/listing_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO vrbo_listings (image_source, price, beds, ratings) VALUES (?, ?, ?, ?)
    ''', (image_data, price, beds, ratings))
        print("Insertion Successful")
    except Exception as E:
        (print('Failed to insert data: ', E))
    conn.commit()
    conn.close()


def scrape_vrbo(url):
    create_table()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        data = []

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))).click()

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        listings = soup.find_all('div', class_='uitk-spacing uitk-spacing-margin-blockstart-three')
        logging.info(f"Scraping URL: {url}")

        for listing in listings:
            ab_img = listing.find_all('img', class_='uitk-image-media')
            ab_price_per_night = listing.find('div',
                                              class_='uitk-text uitk-type-300 uitk-text-default-theme is-visually-hidden')
            ab_beds = listing.find('div',
                                   class_='uitk-text uitk-text-spacing-half truncate-lines-2 uitk-type-300 uitk-text-default-theme')
            ab_ratings = listing.find('span', class_='is-visually-hidden')

            unit_data = {
                'image_sources': [],
                'price': "Not available",
                'beds': "Not available",
                'ratings': "Not available"
            }

            if ab_img:
                for img in ab_img:
                    src = img.get('src')
                    # print(src)
                    if src:
                        response = requests.get(src)
                        image_data = response.content

                        compressed_image = zlib.compress(base64.urlsafe_b64encode(image_data))
                        print("Compression len:", len(compressed_image))
                        insert_into_db(compressed_image, unit_data['price'], unit_data['beds'], unit_data['ratings'])

                        unit_data['image_sources'].append(compressed_image)
                        print(f"Original data length: {len(image_data)}")

                    else:
                        unit_data['image_sources'].append(None)
                        print("Image data is missing")

            if ab_price_per_night:
                unit_data['price'] = ab_price_per_night.text.strip()
            if ab_beds:
                unit_data['beds'] = ab_beds.text.strip()
            if ab_ratings:
                unit_data['ratings'] = ab_ratings.text.strip()

            data.append(unit_data)

    except Exception as e:
        logging.error(f"Error: {e}")
        raise
    finally:
        driver.quit()

    logging.info(f"Scraping URL: {url}")
    return data


# Example usage:
vrbo_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
           "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=& "
scrape_vrbo(vrbo_url)

