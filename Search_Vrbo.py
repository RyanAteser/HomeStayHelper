import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import Create_DATA_TABLE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ScrapingError(Exception):
    pass


class ScrapingError(Exception):
    pass


def fetch_images_from_carousel(driver):
    images = set()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".uitk-image-media"))
        )
        initial_src = driver.find_element(By.CSS_SELECTOR, ".uitk-image-media").get_attribute('src')
        images.add(initial_src)

        while True:
            next_button = driver.find_element(By.CSS_SELECTOR, ".uitk-gallery-carousel-button-next")
            if not next_button:
                break
            next_button.click()
            WebDriverWait(driver, 5).until(
                lambda driver: driver.find_element(By.CSS_SELECTOR, ".uitk-image-media").get_attribute(
                    'src') != initial_src
            )
            new_src = driver.find_element(By.CSS_SELECTOR, ".uitk-image-media").get_attribute('src')
            if new_src in images:
                break
            images.add(new_src)
            initial_src = new_src
    except (TimeoutException, NoSuchElementException) as e:
        logging.warning("Issues encountered while fetching images from carousel: {}".format(e))
    return list(images)


def safe_find_element(driver, css_selector, timeout=10, attribute=None):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return element.get_attribute(attribute) if attribute else element.text
    except TimeoutException:
        logging.warning(f"Timeout waiting for element with selector: {css_selector}")
        return "N/A"


def insert_or_update_listing_data(table_name, listing_id, images, price, beds, ratings):
    with sqlite3.connect('data/listing_data.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not c.fetchone():
            Create_DATA_TABLE.create_db(table_name)
        first_image = images[0] if images else "No Image Available"
        data = (first_image, price, beds, ratings, listing_id)
        c.execute(f"REPLACE INTO {table_name} (image_url, price, beds, ratings, listing_id) VALUES (?, ?, ?, ?, ?)",
                  data)
        conn.commit()


def fetch_listing_details(driver):
    """Fetches price, beds, and ratings of a listing."""
    try:
        price = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH,
                                              "//div[contains(@class, 'uitk-text uitk-type-300 uitk-text-default-theme is-visually-hidden')]"))
        ).text
        beds = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH,
                                              "//div[contains(@class, 'uitk-text uitk-text-spacing-half truncate-lines-2 uitk-type-300 uitk-text-default-theme')]"))
        ).text
        ratings = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH,
                                              "//span[contains(@class, 'uitk-text uitk-type-300 uitk-type-bold uitk-text-default-theme')]"))
        ).text
    except TimeoutException as e:
        logging.warning(f"Timeout occurred while fetching details for a listing: {e}")
        price, beds, ratings = "N/A", "N/A", "N/A"
    return price, beds, ratings


def read_states_from_file(file_path):
    with open(file_path, 'r') as file:
        states = [line.strip() for line in file if line.strip()]
    return states


def scrape_vrbo(state_name, table_name):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = f"https://www.vrbo.com/search?keyword={state_name}"

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))
        ).click()
        listings = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".uitk-spacing.uitk-spacing-margin-blockstart-three"))
        )

        for listing_index, listing in enumerate(listings):

            images = fetch_images_from_carousel(driver)
            url = safe_find_element(driver, "a[data-stid='open-hotel-information']", attribute='href')
            print("Extracted URL:", url)

            print(images)
            from urllib.parse import urlparse, parse_qs

            base_url = "https://www.vrbo.com"
            full_url = base_url + url
            parsed_url = urlparse(full_url)
            query_params = parse_qs(parsed_url.query)

            listing_id = query_params.get('expediaPropertyId', [''])[0]
            print(listing_id)
            try:
                price = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH,
                                                      "//div[contains(@class, 'uitk-text uitk-type-300 uitk-text-default-theme is-visually-hidden')]"))
                ).text
                print(price)
                beds = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH,
                                                      "//div[contains(@class, 'uitk-text uitk-text-spacing-half truncate-lines-2 uitk-type-300 uitk-text-default-theme')]"))
                ).text
                print(beds)
                ratings = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH,
                                                      "//span[contains(@class, 'uitk-text uitk-type-300 uitk-type-bold uitk-text-default-theme')]"))
                ).text
                print(ratings)
                insert_or_update_listing_data(table_name, listing_id, images, price, beds, ratings)
            except TimeoutException as e:
                logging.warning(f"Timeout occurred while fetching details for a listing: {e}")
    except Exception as e:
        logging.error(f"Error processing a listing: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    file_path = r"C:\Users\rcate\Downloads\WebScraper-main (2)\WebScraper-main\Scripts\List_states.txt"
    states = read_states_from_file(file_path)

    for state_name in states:
        logging.info(f"Starting to scrape data for {state_name}")
        scrape_vrbo(state_name, f"{state_name}")
        logging.info(f"Finished scraping data for {state_name}")
