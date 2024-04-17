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


def scrape_vrbo(url, max_pages=None):
    # Initialize Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        data = []

        page_count = 0
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))).click()

        # Simulate scrolling to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for images to load
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_='uitk-spacing uitk-spacing-margin-blockstart-three')

        logging.info(f"Scraping URL: {url}")

        for listing in listings:
            # Extracting image sources
            ab_img = listing.find_all('img', class_='uitk-image-media')

            # Extracting price per night
            ab_price_per_night = listing.find('div',
                                              class_='uitk-text uitk-type-300 uitk-text-default-theme is-visually-hidden')
            price = ab_price_per_night.text.strip() if ab_price_per_night else "Not available"

            # Extracting number of beds
            ab_beds = listing.find('div',
                                   class_='uitk-text uitk-text-spacing-half truncate-lines-2 uitk-type-300 uitk-text-default-theme')
            beds = ab_beds.text.strip() if ab_beds else "Not available"

            # Extracting ratings
            ab_ratings = listing.find('span', class_='uitk-text uitk-type-500 uitk-type-bold uitk-text-default-theme')
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


# Example usage:
vrbo_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
           "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=& "
max_pages = 5
#scrape_vrbo(vrbo_url)
