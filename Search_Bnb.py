import logging
import time

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
def scrape_airbnb(url, max_pages=None):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        data = []

        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_8ssblpx")))

        # Simulate scrolling to load more listings
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Adjust the sleep time as needed
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            if new_scroll_height == scroll_height:
                break
            scroll_height = new_scroll_height

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_=' dir dir-ltr')

        logging.info(f"Scraping URL: {url}")

        for listing in listings:
            # Extracting image source
            image = listing.find('img', class_='itu7ddv atm_e2_idpfg4 atm_vy_idpfg4 atm_mk_stnw88 atm_e2_1osqo2v__1lzdix4 atm_vy_1osqo2v__1lzdix4 i1cqnm0r atm_jp_pyzg9w atm_jr_nyqth1 i1de1kle atm_vh_yfq0k3 dir dir-ltr')
            image_source = image['src'] if image else None

            # Extracting price per night
            price_element = listing.find('span', class_='_1y74zjx')
            price = price_element.text.strip() if price_element else "Not available"

            # Extracting number of beds
            beds_element = listing.find('div', class_='a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr')
            beds = beds_element.text.strip() if beds_element else "Not available"

            # Extracting ratings
            ratings_element = listing.find('span', class_='t1a9j9y7 atm_da_1ko3t4y atm_dm_kb7nvz atm_fg_h9n0ih dir dir-ltr')
            ratings = ratings_element.text.strip() if ratings_element else "Not available"

            unit_data = {
                'image_source': image_source,
                'price': price,
                'beds': beds,
                'ratings': ratings
            }

            data.append(unit_data)

    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        raise ScrapingError("Error occurred during scraping")
    finally:
        driver.quit()

    return data


# Example usage:
airbnb_url = "https://www.airbnb.com/s/Seattle--WA--United-States/homes"
max_pages = 5  # Number of pages to scrape, set to None to scrape all available pages
scraped_data = scrape_airbnb(airbnb_url, max_pages)
print(scraped_data)
