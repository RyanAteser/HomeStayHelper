import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from io import BytesIO
from PIL import Image
import sqlite3
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)


def convert_data(image_data):
    try:
        image_stream = BytesIO(image_data)
        img = Image.open(image_stream)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, format='JPEG', quality=200)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        logging.error("Error converting image data: %s", e)
        return None


def insert_into_db(image_data, price, beds, ratings):
    try:
        with sqlite3.connect('data/listing_data.db') as conn:
            cursor = conn.cursor()
            query = '''INSERT INTO vrbo_listings (image_source, price, beds, ratings) VALUES (?, ?, ?, ?)'''
            cursor.execute(query, (image_data, price, beds, ratings))
            conn.commit()
            logging.info("Insertion successful")
    except sqlite3.Error as e:
        logging.error("Failed to insert data: %s", e)
        raise Exception("Database error occurred")


def scrape_bnb(url):
    compressed_image = []
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    data = []
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_='listing_class')  # Update this with the correct class
        for listing in listings:
            # Extracting image sources
            print("getting images:")
            ab_img = listing.find_all('img',
                                      class_='itu7ddv atm_e2_idpfg4 atm_vy_idpfg4 atm_mk_stnw88 atm_e2_1osqo2v__1lzdix4 atm_vy_1osqo2v__1lzdix4 i1cqnm0r atm_jp_pyzg9w atm_jr_nyqth1 i1de1kle atm_vh_yfq0k3 dir dir-ltr')
            print("Success: ", ab_img)
            # Extracting price per night
            print("Getting Price per Night: ")
            ab_price_per_night = listing.find('span', class_='_1y74zjx')
            print("Success : ", ab_price_per_night)
            price = ab_price_per_night.text.strip() if ab_price_per_night else "Not available"

            # Extracting number of beds
            ab_beds = listing.find('span',
                                   class_='a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr')
            beds = ab_beds.text.strip() if ab_beds else "Not available"

            # Extracting ratings
            ab_ratings = listing.find('span',
                                      class_='t1a9j9y7 atm_da_1ko3t4y atm_dm_kb7nvz atm_fg_h9n0ih dir dir-ltr"><span class="r4a59j5 atm_h_1h6ojuz atm_9s_1txwivl atm_7l_jt7fhx atm_84_evh4rp dir dir-lt')
            ratings = ab_ratings.text.strip() if ab_ratings else "Not available"

            unit_data = {
                'image_sources': [],
                'price': price,
                'beds': beds,
                'ratings': ratings
            }

            for img in ab_img:
                src = img.get('src')

                if src:
                    response = requests.get(src)
                    image_data = response.content
                    compressed_image = convert_data(image_data)
                    if compressed_image is None:
                        logging.error("Failed to convert image data")
                        continue

                    unit_data['image_sources'].append(compressed_image)

            # Insert data into the database
            insert_into_db(compressed_image, price, beds, ratings)

            data.append(unit_data)
            logging.info(f"Fetching data from {url}")
            # Assume you fetch data here
            data = "fetched data"
            if not data:
                logging.warning(f"No data returned from {url}")
                return None
        return data
        return "Data fetched and processed"
    except Exception as e:
        logging.error("Error during scraping: %s", e)
        raise
    finally:
        driver.quit()


