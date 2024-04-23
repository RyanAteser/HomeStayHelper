from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get('https://www.vrbo.com/search?keyword=Seattle')

try:
    # Use XPath to locate an element
    element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='uitk-text uitk-type-300 uitk-text-default-theme is-visually-hidden']"))
    )
    print(element)
finally:
    driver.quit()






