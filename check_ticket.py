import time
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# --- Configuration ---
TARGET_URL = "https://www.aeroline.com.my/"
DEPARTURE_DATE = "22/02/2026"  # Format: DD/MM/YYYY
ROUTE_VALUE = "SWY - SIN"      # The text value to look for in the dropdown

def get_driver():
    """Sets up the Chrome Webdriver."""
    chrome_options = Options()
    # Remove the argument below if you want to see the browser pop up
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Automatically manages the driver installation
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def check_ticket_availability():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking availability...")
    driver = None
    
    try:
        driver = get_driver()
        driver.get(TARGET_URL)

        # 1. Wait for the 'Route' dropdown to load and select 'SWY - SIN'
        # We look for the select element that contains the route options
        wait = WebDriverWait(driver, 15)
        
        # Locating the route dropdown. 
        # Note: Selectors might need adjustment if the site updates.
        # We try to find the select element by its likely name or ID in the form.
        route_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "route")))
        select = Select(route_dropdown)
        
        # Select by visible text
        try:
            select.select_by_visible_text(ROUTE_VALUE)
        except Exception:
            # Fallback: iterate options if exact text match fails
            found = False
            for option in select.options:
                if "SWY" in option.text and "SIN" in option.text:
                    option.click()
                    found = True
                    break
            if not found:
                print("Error: Could not find the SWY-SIN route in the dropdown.")
                return

        # 2. Input the Date
        # Finding the date input field (often named 'ddate' or similar)
        date_input = driver.find_element(By.NAME, "ddate")
        date_input.clear()
        date_input.send_keys(DEPARTURE_DATE)

        # 3. Click the 'Search' or 'Next' button
        # Usually an image input or button type=submit
        try:
            search_btn = driver.find_element(By.XPATH, "//input[@type='image' or @type='submit']")
            search_btn.click()
        except:
            print("Error: Could not find the search button.")
            return

        # 4. Analyze the Results
        # We wait for the results table or an error message.
        # If trips are available, they usually appear in a table row.
        # If not, there is often a message like "No trips available" or empty table.
        
        # Wait a moment for page transition
        time.sleep(5) 
        
        page_source = driver.page_source.lower()

        if "no trip found" in page_source or "no seats available" in page_source:
            print("Status: No tickets available yet.")
        elif "select seat" in page_source or "price" in page_source:
            # If we see terms indicating booking flow is active
            print("\n" + "="*40)
            print(f"SUCCESS! Tickets might be available for {DEPARTURE_DATE}!")
            print(f"Check now: {TARGET_URL}")
            print("="*40 + "\n")
            # Here you could add a function to send an email or play a sound
        else:
            # Ambiguous result, print warning
            print("Status: Check completed, but result was unclear. (Page might have changed)")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()

# --- Scheduling ---
# Run once immediately to verify it works
check_ticket_availability()

# Schedule to run every hour
schedule.every(1).hours.do(check_ticket_availability)

print("Script is running. Press Ctrl+C to stop.")

while True:
    schedule.run_pending()
    time.sleep(1)
