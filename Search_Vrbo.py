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

def scrape_vrbo(url):
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
                    if src:
                        # Assume src is a URL, adjust if it's a file path or other
                        response = requests.get(src)
                        image_data = response.content
                        print(image_data)
                        print(f'Src: {len(image_data)}')

                        compressed_data = zlib.compress(image_data)
                        unit_data['image_sources'].append(compressed_data)

                        print(f"Original data length: {len(image_data)}")
                        print(f"Compressed data length: {len(compressed_data)}")
            else:
                unit_data['image_sources'].append(None)

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

    insert_into_db(data)
    print(data)


def download_image(image_sources):
    image_blobs = []

    for image_data in image_sources:
        try:
            if image_data:
                jpeg_data = zlib.compress(image_data)
                image_blobs.append(base64.urlsafe_b64encode(jpeg_data))
            else:
                image_blobs.append(None)
        except Exception as e:
            print(f"Error processing image: {e}")
            image_blobs.append(None)

    return image_blobs


def insert_into_db(data):
    conn = sqlite3.connect('data/listing_data.db')
    cursor = conn.cursor()
    invalid_count = 0

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vrbo_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price TEXT,
                beds TEXT,
                ratings TEXT,
                image_source BLOB
            )
        ''')

        for row in data:
            if 'image_sources' in row and 'price' in row and 'beds' in row and 'ratings' in row:
                price = row['price']
                beds = row['beds']
                ratings = row['ratings']

                for image_data in row['image_sources']:
                    try:
                        cursor.execute('''
                            INSERT INTO vrbo_listings (price, beds, ratings, image_source)
                            VALUES (?, ?, ?, ?)
                        ''', (str(price), str(beds), str(ratings), image_data))
                        print(f"Inserting values: {price}, {beds}, {ratings}, Image data")
                    except Exception as image_insert_error:
                        print(f"Error inserting image into database: {image_insert_error}")
                        invalid_count += 1

                if not row['image_sources']:
                    invalid_count += 1

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting into database: {e}")
        conn.rollback()
    finally:
        conn.close()

    if invalid_count > 0:
        print(f"Ignore: {invalid_count} invalid rows found.")

# Example URL of VRBO listings
vrbo_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
           "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=& "
scrape_vrbo(vrbo_url)

