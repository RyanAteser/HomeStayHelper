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


def scrape_booking(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(url)
        data = []
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button:contains('Dismiss sign in information.')"))).click()

        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button:contains('Dismiss sign in information.')"))).click()

        # Wait until the hotel list is loaded
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        hotel_list = soup.find_all('div', class_='sr_property_block')
        #Button to show price.
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-stid='apply-date-selector']"))).click()
        logging.info(f"Scraping URL: {url}")

        for hotel in hotel_list:
            # Extracting image sources
            image = hotel.find('img', class_='f9671d49b1')
            image_source = image.get('src') if image else None

            # Extracting price per night
            price_element = hotel.find('div', class_='ac4a7896c7')
            price = price_element.text.strip() if price_element else "Not available"

            # Extracting number of beds
            beds_element = hotel.find('div', class_='abf093bdfe')
            beds = beds_element.text.strip() if beds_element else "Not available"

            # Extracting ratings
            ratings_element = hotel.find('div', class_='ac4a7896c7')
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
        raise Exception("Error occurred during scraping")
    finally:
        driver.quit()

    return data


# Example usage:
booking_url = "https://www.booking.com/searchresults.en-gb.html?ss=Kyoto&ssne=Kyoto&ssne_untouched=Kyoto&efdco=1&label=gen173nr-1FCAEoggI46AdIM1gEaHWIAQGYAQm4ARnIAQzYAQHoAQH4AQKIAgGoAgO4Av_ktfIFwAIB0gIkNWI0YzU1Y2EtMjBmYS00NzNkLThkMjEtMjQxYmI5Nzg3YTRh2AIF4AIB&sid=36885a1972ccca576d195bcd6f2a9d80&aid=304142&lang=en-gb&sb=1&src_elem=sb&src=searchresults&dest_id=-235402&dest_type=city&group_adults=1&no_rooms=1&group_children=0"
scrape_booking(booking_url)