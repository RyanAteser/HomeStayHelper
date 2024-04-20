# scraping_script.py
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import sqlite3
from io import BytesIO
import tempfile
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)


# Define custom exceptions
class ScrapingError(Exception):
    pass


def fetch_images_from_carousel(driver, listing_element):
    images = set()  # Using a set to avoid duplicate images if the carousel loops

    # Selectors based on your provided button elements
    next_button_selector = "button.uitk-gallery-carousel-button-next"
    prev_button_selector = "button.uitk-gallery-carousel-button-prev"

    try:
        # Initial collection of image

        initial_img = WebDriverWait(listing_element, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "img.uitk-image-media"))
        )
        images.add(initial_img.get_attribute('src'))

        next_button = listing_element.find_element(By.CSS_SELECTOR, next_button_selector)

        # Function to navigate and collect images
        def navigate_and_collect():
            try:
                next_button.click()
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "img.uitk-image-media"))
                )
                img = listing_element.find_element(By.CSS_SELECTOR, "img.uitk-image-media")
                return img.get_attribute('src')
            except NoSuchElementException:
                print("Navigation button not found.")
                return None

        # Loop through carousel by clicking 'next' until we hit the first image again
        while True:
            src = navigate_and_collect()
            if src in images:  # Break if we see the same image again, indicating we've looped around
                break
            if src:
                images.add(src)

    except TimeoutException:
        print("Timeout waiting for images in the carousel.")

    except Exception as e:
        print(f"An error occurred: {e}")

    return list(images)  # Convert set back to list for consistency


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


def insert_into_db(listing_id, images):
    conn = sqlite3.connect('data/listing_data.db')
    cursor = conn.cursor()
    try:
        for image_path in images:
            cursor.execute(
                "INSERT INTO images (listing_id, image_path) VALUES (?, ?)",
                (listing_id, image_path)
            )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def scrape_vrbo(url, max_pages=None):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))).click()

        # Simulate scrolling to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.uitk-spacing.uitk-spacing-margin-blockstart-three")))

        listings = driver.find_elements(By.CSS_SELECTOR, "div.uitk-spacing.uitk-spacing-margin-blockstart-three")
        scraped_data = []
        for listing_index, listing in enumerate(listings):
            images = fetch_images_from_carousel(driver, listing)
            listing_id = f"listing_{listing_index}"  # Generate unique listing_id

            # Extract the listing URL
            url_element = None
            try:
                url_element = listing.find_element(By.CSS_SELECTOR, "a[data-stid='open-hotel-information']")
            except NoSuchElementException:
                logging.warning("Listing URL element not found")

            listing_url = url_element.get_attribute("href") if url_element else None

            scraped_data.append({'listing_id': listing_id, 'listing_url': listing_url, 'image_sources': images})

        return scraped_data

    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        raise ScrapingError("Error occurred during scraping")
    finally:
        driver.quit()
