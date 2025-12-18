import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

def check_ticket_availability():
    # Configuration
    target_date = "22/02/2026"  # Format: DD/MM/YYYY
    route_text_part = "SWY - SIN" # Unique part of the route text (Sunway to Singapore)
    
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background without opening a window
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    print("Initializing browser...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("Navigating to Aeroline website...")
        driver.get("https://www.aeroline.com.my/")
        
        # Wait for the specific planning form to load
        wait = WebDriverWait(driver, 15)
        
        # 1. Handle Route Selection
        # The dropdown usually has a name like 'route' or we find it by the text inside options
        print(f"Selecting route: {route_text_part}...")
        
        # specific logic to find the dropdown containing our route
        # We look for a <select> element that has an <option> containing 'SWY - SIN'
        route_dropdown = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//select[.//option[contains(text(), '{route_text_part}')]]")
        ))
        
        select = Select(route_dropdown)
        # Select by visible text containing the route code
        for option in select.options:
            if route_text_part in option.text:
                select.select_by_visible_text(option.text)
                break
        
        # 2. Handle Date Input
        print(f"Entering date: {target_date}...")
        # Finding input that expects date, often having placeholder 'DD/MM/YYYY' or nearby text 'Date'
        date_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'DD/MM/YYYY') or contains(@title, 'Date')]")
        date_input.clear()
        date_input.send_keys(target_date)
        
        # 3. Submit Form
        # Finding the search/book button. Often an image button or button with text 'Book' or 'Search'
        search_btn = driver.find_element(By.XPATH, "//input[@type='image' or @type='submit'] | //button[contains(text(), 'Book')]")
        search_btn.click()
        
        # 4. Check Results
        print("Checking availability...")
        # Wait for the results page to load. We check for success indicators or 'No trips' messages
        # Note: This part depends heavily on the specific response of the site which we can't see live without running it.
        # We will capture the page text to analyze.
        time.sleep(5) # Simple wait for page transition
        
        page_source = driver.page_source.lower()
        
        if "no trips found" in page_source or "no schedule" in page_source:
            print(f"[-] No tickets available yet for {target_date}.")
        elif "select seats" in page_source or "available" in page_source:
            print(f"[!] Tickets might be AVAILABLE! Please check manually.")
        else:
            print("[?] Status unclear. The schedule page loaded, but availability could not be confirmed automatically.")
            print("    It is recommended to visit the site manually if the date is near.")

    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        driver.quit()
        print("Check complete.")

if __name__ == "__main__":
    check_ticket_availability()
