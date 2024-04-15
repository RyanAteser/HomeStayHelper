import pandas as pd
import requests
from bs4 import BeautifulSoup



import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import requests
from PIL import Image
import sqlite3
from io import BytesIO
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)


# Define custom exceptions
class ScrapingError(Exception):
    pass


class DatabaseError(Exception):
    pass


def convert_data(image_data):
    try:
        # Create a BytesIO object from image_data
        image_stream = BytesIO(image_data)

        # Open image using PIL
        img = Image.open(image_stream)

        # Create a temporary file to save the image
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file_path = temp_file.name

        # Save the image to the temporary file
        img.save(temp_file_path, format='JPEG', quality=50)  # Adjust quality as needed

        # Close the temporary file
        temp_file.close()

        # Return the path of the temporary file
        return temp_file_path

    except Exception as e:
        logging.error(f"Error converting image data: {e}")
        return None


def insert_into_db(image_data, price, beds, ratings):
    conn = sqlite3.connect('data/listing_data.db')
    cursor = conn.cursor()
    try:
        query = '''
            INSERT INTO vrbo_listings (image_source, price, beds, ratings) VALUES (?, ?, ?, ?)
        '''
        data_tuple = (image_data, price, beds, ratings)
        cursor.execute(query, data_tuple)
        conn.commit()
        logging.info("Insertion Successful")
    except sqlite3.Error as error:
        logging.error(f"Failed to insert data: {error}")
        raise DatabaseError("Database error occurred")
    finally:
        cursor.close()
        conn.close()


def scrape_vrbo(url):
    # Initialize Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        data = []

        # Simulate scrolling to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for images to load
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_='gsgwcjk atm_10yczz8_kb7nvz atm_10yczz8_cs5v99__1ldigyt atm_10yczz8_11wpgbn__1v156lz atm_10yczz8_egatvm__qky54b atm_10yczz8_qfx8er__1xolj55 atm_10yczz8_ouytup__w5e62l g8ge8f1 atm_1d13e1y_p5ox87 atm_yrukzc_1od0ugv atm_10yczz8_cs5v99_vagkz0_1ldigyt atm_10yczz8_11wpgbn_vagkz0_1h2hqoz g14v8520 atm_9s_11p5wf0 atm_d5_j5tqy atm_d7_1ymvx20 atm_dl_1mvrszh atm_dz_hxz02 dir dir-ltr')

        logging.info(f"Scraping URL: {url}")
        print(listings)
        for listing in listings:
            # Extracting image sources
            print("getting images:")
            ab_img = listing.find_all('img', class_='itu7ddv atm_e2_idpfg4 atm_vy_idpfg4 atm_mk_stnw88 atm_e2_1osqo2v__1lzdix4 atm_vy_1osqo2v__1lzdix4 i1cqnm0r atm_jp_pyzg9w atm_jr_nyqth1 i1de1kle atm_vh_yfq0k3 dir dir-ltr')
            print("Success: ",ab_img)
            # Extracting price per night
            print("Getting Price per Night: ")
            ab_price_per_night = listing.find('span', class_='_1y74zjx')
            print("Success : ", ab_price_per_night)
            price = ab_price_per_night.text.strip() if ab_price_per_night else "Not available"

            # Extracting number of beds
            ab_beds = listing.find('span', class_='a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr')
            beds = ab_beds.text.strip() if ab_beds else "Not available"

            # Extracting ratings
            ab_ratings = listing.find('span', class_='t1a9j9y7 atm_da_1ko3t4y atm_dm_kb7nvz atm_fg_h9n0ih dir dir-ltr"><span class="r4a59j5 atm_h_1h6ojuz atm_9s_1txwivl atm_7l_jt7fhx atm_84_evh4rp dir dir-lt')
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
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        raise ScrapingError("Error occurred during scraping")
    finally:
        driver.quit()
    return data



