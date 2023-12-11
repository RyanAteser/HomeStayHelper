from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
import logging


# ... (Rest of the scraping function)
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log message format
    filename='scraping.log'  # Specify the file to write logs to
)


def insert_into_db(data):
    conn = sqlite3.connect('data/listing_data.db')
    cursor = conn.cursor()
    invalid_count = 0  # Variable to track the count of invalid rows

    try:
        # Add the missing column if it doesn't exist
        cursor.execute('''
            PRAGMA table_info(vrbo_listings)
        ''')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        if 'image_source' not in column_names:
            cursor.execute('''
                ALTER TABLE vrbo_listings
                ADD COLUMN image_source TEXT
            ''')

        for row in data:
            if len(row) == 4:  # Assuming each row has four values: price, beds, ratings, img_src
                price, beds, ratings, image_source = row
                cursor.execute('''
    INSERT INTO vrbo_listings (price, beds, ratings, image_source)
    VALUES (?, ?, ?, ?)
            ''', (price, beds, ratings, image_source))
            else:
                invalid_count += 1

        conn.commit()  # Commit changes after all data has been inserted
    except sqlite3.Error as e:
        print(f"Error inserting into database: {e}")
        conn.rollback()
    finally:
        conn.close()

    if invalid_count > 0:
        print(f"Ignore: {invalid_count} invalid rows found.")


def scrape_vrbo(url):
    price_text = []
    beds_text = []
    ratings_text = []
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)
        data = []

        WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))).click()

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        listings = soup.find_all('div', class_='uitk-spacing uitk-spacing-margin-blockstart-three')
        logging.info(f"Scraping URL: {url}")

    # Log data extraction
        logging.debug(f"Extracted data: {data}")
    except Exception as e:
        # Log exceptions or errors
        logging.error(f"Error: {e}")
        raise

    try:
        for listing in listings:

            ab_img = listing.find_all('img', class_='uitk-image-media')
            ab_price_per_night = listing.find('div', class_='uitk-text uitk-type-300 uitk-text-default-theme '
                                                        'is-visually-hidden')
            ab_beds = listing.find('div', class_='uitk-text uitk-text-spacing-half truncate-lines-2 uitk-type-300 '
                                             'uitk-text-default-theme')
            ab_ratings = listing.find('span', class_='is-visually-hidden')

        # Extract data and append as a unit to the 'data' list
            unit_data = []
            image_sources = []
            if ab_img:
                for img in ab_img:
                    src = img.get('src')
                    if src:
                        image_sources.append(src)
                else:
                    image_sources.append("Not Available")
            else:
                image_sources.append("Not Available")



            if ab_price_per_night:
                price_text = ab_price_per_night.text.strip()
                unit_data.append(price_text)
            else:
                unit_data.append("Not available")

            if ab_beds:
                unit_data.append(ab_beds.text.strip())
                beds_text = ab_beds.text.strip()
            else:
                unit_data.append("Not available")


            if ab_ratings:
                unit_data.append(ab_ratings.text.strip())
                ratings_text = ab_ratings.text.strip()
            else:
                unit_data.append("Not available")

            unit_data = {
                'image_sources': image_sources,
                'price': price_text,
                'beds': beds_text,
                'ratings': ratings_text
            }
            data.append(unit_data)
    except Exception as e:
        # Log exceptions or errors
        logging.error(f"Error: {e}")
        raise

    insert_into_db(data)
    driver.quit()

    print(data)  # For testing purposes, you can print the extracted data


# Example URL of VRBO listings
vrbo_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
           "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=&theme=&userIntent= "
scrape_vrbo(vrbo_url)
