import logging
import re
import sqlite3
import time
from random import random

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def scroll_page(driver):
    """Scrolls the webpage to trigger lazy loading."""
    logging.info("Starting to scroll the page.")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    logging.info("Finished scrolling the page.")


def load_complete_page(driver):
    """Simulate user interaction to trigger all lazy-loaded items."""
    try:
        body = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        for _ in range(20):
            body.send_keys(Keys.PAGE_DOWN)
            WebDriverWait(driver, 1).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    except TimeoutException:
        logging.error("Page did not load new content in time.")
    except KeyboardInterrupt:
        logging.info("Process was manually interrupted by user.")
        raise


def fetch_images_from_carousel(driver, listing):
    """Fetches image sources from a listing using JavaScript."""
    images = []
    driver.execute_script("arguments[0].scrollIntoView();", listing)

    try:
        # Find the initial set of images in the carousel
        img_elements = listing.find_elements(By.CSS_SELECTOR, "img")
        for img in img_elements:
            src = img.get_attribute('src')
            if src:
                images.append(src)
                logging.info(f"Found image: {src}")

        # Find the next button in the carousel and click it to get more images
        next_button = listing.find_element(By.CSS_SELECTOR, "button[aria-label^='Next photo']")
        while next_button and next_button.get_attribute('aria-disabled') != 'true':
            # Click using JavaScript to avoid interception issues
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(random.uniform(1, 3))  # Random delay to mimic human interaction
            img_elements = listing.find_elements(By.CSS_SELECTOR, "img")
            for img in img_elements:
                src = img.get_attribute('src')
                if src and src not in images:
                    images.append(src)
                    logging.info(f"Found image: {src}")

            try:
                next_button = listing.find_element(By.CSS_SELECTOR, "button[aria-label^='Next photo']")
            except Exception:
                break

    except Exception as e:
        logging.error(f"Error fetching images: {e}")

    if not images:
        logging.info("No suitable images found for this listing.")
    return images


def insert_or_update_listing_data(conn, table_name, listing_id, images, price, title, beds, ratings, link):
    """Insert or update listing data in the database."""
    images = ",".join(images) if images else "No Image Available"
    data = (listing_id, images, price, title, beds, ratings, link)
    sql_insert_or_update = f"""
    REPLACE INTO {table_name} (listing_id, image_url, price, title, beds, ratings, link) VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    try:
        c = conn.cursor()
        c.execute(sql_insert_or_update, data)
        conn.commit()
        logging.info("Data successfully saved.")
    except sqlite3.Error as e:
        logging.error(f"An error occurred during data insertion: {e}")


def sanitize_state_name(state_name):
    """Sanitize and format state name to create a valid and consistent SQL table name."""
    sanitized = re.sub(r'[^a-zA-Z]', '', state_name)  # Remove all non-alphabetic characters
    return sanitized.lower()


def ensure_table_exists(conn, state_name):
    """Ensure that a table for the specified state exists in the database."""
    table_name = sanitize_state_name(state_name)
    sql_create_table = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT UNIQUE,
        image_url TEXT,
        price TEXT,
        title TEXT,
        beds TEXT,
        ratings TEXT,
        link TEXT
    );
    """
    try:
        c = conn.cursor()
        c.execute(sql_create_table)
        conn.commit()
        logging.info(f"Table '{table_name}' is ready for use or already exists.")
    except sqlite3.Error as e:
        logging.error(f"An error occurred: {e}")
    return table_name


def fetch_listing_details(driver, state_name):
    """Fetch listing details from the VRBO website."""
    db_path = 'data/listing_data.db'
    conn = sqlite3.connect(db_path)
    table_name = ensure_table_exists(conn, state_name)

    url = f"https://www.vrbo.com/search?keyword={state_name}"
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))
        ).click()
    except Exception as e:
        logging.error(f"Timeout or other error: {e}")
        driver.refresh()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))
        ).click()

    scroll_page(driver)
    load_complete_page(driver)
    logging.info("Loading Complete")

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-stid='lodging-card-responsive']"))
    )
    listings = driver.find_elements(By.CSS_SELECTOR, "div[data-stid='lodging-card-responsive']")

    for listing in listings:
        try:
            link = listing.find_element(By.CSS_SELECTOR, "a[data-stid='open-hotel-information']")
            href = link.get_attribute('href')
            listing_id = re.search(r'expediaPropertyId=(\d+)', href).group(1) if href else "No ID Found"

            price = listing.find_element(By.CSS_SELECTOR, "span[data-stid='price-summary-message-line']").text
            title = listing.find_element(By.CSS_SELECTOR,
                                         "h3.uitk-heading.uitk-heading-5.overflow-wrap.uitk-layout-grid-item.uitk-layout-grid-item-has-row-start").text
            beds = listing.find_element(By.CSS_SELECTOR,
                                        "div.uitk-text.uitk-text-spacing-half.truncate-lines-2.uitk-type-300.uitk-text-default-theme").text
            ratings = listing.find_element(By.CSS_SELECTOR, "span.is-visually-hidden").text

            images = fetch_images_from_carousel(driver, listing)
            insert_or_update_listing_data(conn, table_name, listing_id, images, price, title, beds, ratings, href)
        except Exception as e:
            logging.error(f"Error processing listing: {e}")

    conn.close()


def read_states_from_file(file_path):
    """Read state names from a file."""
    with open(file_path, 'r') as file:
        states = [line.strip() for line in file if line.strip()]
    return states


if __name__ == "__main__":
    file_path = r"C:\Users\rcate\Downloads\WebScraper-main (2)\WebScraper-main\Scripts\List_states.txt"
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    states = read_states_from_file(file_path)
    for state_name in states:
        logging.info(f"Starting to scrape data for {state_name}")
        fetch_listing_details(driver, state_name)
        time.sleep(5)

    driver.quit()
    logging.info("Web scraping session ended.")

