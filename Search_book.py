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
        img.save(temp_file_path, format='JPEG', quality=200)  # Adjust quality as needed

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


import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_booking(url):
    logging.basicConfig(level=logging.INFO)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        hotel_list = soup.find_all('div', class_='c066246e13 d8aec464ca')

        data = []
        for hotel in hotel_list:
            image = hotel.find('img', class_='f9671d49b1')
            price_element = hotel.find('div', class_='a4b53081e1')
            beds_element = hotel.find('div', class_='fc367255e6')
            ratings_element = hotel.find('div', class_='a3b8729ab1 d86cee9b25')

            unit_data = {
                'image_source': image.get('src') if image else None,
                'price': price_element.text.strip() if price_element else "Not available",
                'beds': beds_element.text.strip() if beds_element else "Not available",
                'ratings': ratings_element.text.strip() if ratings_element else "Not available"
            }
            data.append(unit_data)

        if not data:
            logging.warning("No data fetched from the URL.")
            return None

        return data
    except Exception as e:
        logging.error("Failed to scrape data due to an error.", exc_info=True)
        raise
    finally:
        driver.quit()

# Example usage of the function


checkOut = "2024-05-08"
checkIn = "2024-05-05"
# Example usage:
booking_url = f"https://www.booking.com/searchresults.html?ss=Kyoto&ssne=Kyoto&ssne_untouched=Kyoto&efdco=1&label" \
              f"=gen173nr-1FCAEoggI46AdIM1gEaLQCiAEBmAExuAEXyAEM2AEB6AEB" \
              f"-AECiAIBqAIDuAKaq_awBsACAdICJGZkNTIwZTFmLTZiODItNGM1ZS05Mzk1LTM2ZTNhNTE0Y2U3YtgCBeACAQ&aid=304142" \
              f"&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_id=-235402&dest_type=city&checkin=" \
              f"{checkIn}&checkout={checkOut}&group_adults=2&no_rooms=1&group_children=0 "



