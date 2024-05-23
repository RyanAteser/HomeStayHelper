import logging
import os
import random
import re
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)


# Function to clean and format the price string
def clean_price(price_str):
    prices = re.findall(r'\$\d+', price_str)
    unique_prices = set(prices)
    if len(unique_prices) > 1:
        return ' to '.join(sorted(unique_prices)) + ' per night'
    elif unique_prices:
        return list(unique_prices)[0] + ' per night'
    else:
        return "Price not available"


# Function to scroll the page to load more content
def scroll_page(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 5))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# Function to load the entire page content
def load_complete_page(driver):
    body = driver.find_element(By.TAG_NAME, 'body')
    for _ in range(20):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.5)


# Function to fetch all images by interacting with the carousel
def fetch_images_from_carousel(driver, listing_element):
    logging.info("Fetching images for a new listing.")
    images = []
    driver.execute_script("arguments[0].scrollIntoView();", listing_element)

    try:
        # Find the initial set of images in the carousel
        img_elements = listing_element.find_elements(By.CSS_SELECTOR, "picture > img")
        for img in img_elements:
            src = img.get_attribute('src')
            if src and 'muscache.com' in src:
                images.append(src)
                logging.info(f"Found image: {src}")

        # Find the next button in the carousel and click it to get more images
        next_button = listing_element.find_element(By.CSS_SELECTOR, "button[aria-label^='Next photo']")
        while next_button and next_button.get_attribute('aria-disabled') != 'true':
            # Click using JavaScript to avoid interception issues
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(random.uniform(1, 3))  # Random delay to mimic human interaction
            img_elements = listing_element.find_elements(By.CSS_SELECTOR, "picture > img")
            for img in img_elements:
                src = img.get_attribute('src')
                if src and 'muscache.com' in src and src not in images:
                    images.append(src)
                    logging.info(f"Found image: {src}")

            try:
                next_button = listing_element.find_element(By.CSS_SELECTOR, "button[aria-label^='Next photo']")
            except Exception:
                break

    except Exception as e:
        logging.error(f"Error fetching images: {e}")

    if not images:
        logging.info("No suitable images found for this listing.")
    return images


# Function to sanitize state names for table names
def sanitize_state_name(state_name):
    sanitized = re.sub(r'[^a-zA-Z]', '', state_name)
    return sanitized.lower()


# Function to ensure the table for a state exists in the database
def ensure_table_exists(conn, state_name):
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


# Function to insert or update listing data in the database
def insert_or_update_listing_data(conn, table_name, listing_id, images, price, title, beds, ratings, link):
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


# Function to fetch listing details from the webpage
def fetch_listing_details(driver, state_name):
    db_path = 'data/Listings_data.db'
    conn = sqlite3.connect(db_path)
    table_name = ensure_table_exists(conn, state_name)

    scroll_page(driver)
    load_complete_page(driver)
    logging.info("Loading All Listings")
    listings = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='card-container']"))
    )
    logging.info(f"Found {len(listings)} listings")
    for listing in listings:
        try:
            link = listing.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
            listing_id = re.search(r'/rooms/(\d+)', link).group(1) if link else "No ID Found"
            price_element = listing.find_element(By.CSS_SELECTOR, "div[data-testid='price-availability-row']")
            price = price_element.text if price_element else "Price not found"
            true_price = clean_price(price)
            print(true_price)
            images = fetch_images_from_carousel(driver, listing)
            beds_element = listing.find_element(By.CSS_SELECTOR,
                                                "span.a8jt5op.atm_3f_idpfg4.atm_7h_hxbz6r.atm_7i_ysn8ba.atm_e2_t94yts.atm_ks_zryt35.atm_l8_idpfg4.atm_mk_stnw88.atm_vv_1q9ccgz.atm_vy_t94yts.dir.dir-ltr")
            beds = beds_element.text if beds_element else "No Data Available"
            print(beds)
            ratings_element = listing.find_element(By.CSS_SELECTOR, "span.ru0q88m.atm_cp_1ts48j8.dir.dir-ltr")
            ratings = ratings_element.text if ratings_element else "No Data Available"
            print(ratings)
            description_element = listing.find_element(By.CSS_SELECTOR, "span[data-testid='listing-card-name']")
            description = description_element.text if description_element else "No Data Available"
            print(description)

            insert_or_update_listing_data(conn, table_name, listing_id, images, true_price, description, beds, ratings,
                                          link)
        except Exception as e:
            logging.error(f"Error processing listing: {str(e)}")

    conn.close()


# Function to read state names from a file
def read_states_from_file(file_path):
    with open(file_path, 'r') as file:
        states = [line.strip() for line in file if line.strip()]
    return states


# Main script execution
if __name__ == "__main__":
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        states = read_states_from_file(
            r"C:\Users\rcate\Downloads\WebScraper-main (2)\WebScraper-main\Scripts\List_states.txt"
        )
        for state_name in states:
            url = f"https://www.airbnb.com/s/{state_name}/homes"
            driver.get(url)
            logging.info(f"Starting to scrape data for {state_name}")
            fetch_listing_details(driver, state_name)
            time.sleep(5)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()
        logging.info("Web scraping session ended.")


