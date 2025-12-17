import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
TARGET_DATE = "22-02-2026"  # Format: DD-MM-YYYY
ROUTE_TEXT = "SWY - SIN"    # Sunway Pyramid to Singapore
CHECK_INTERVAL = 3600       # Check every 1 hour (in seconds)

def start_browser():
    """Initializes the browser."""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Keep headless OFF for the first run to handle login
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def login_step(driver):
    """Navigates to login and waits for manual user intervention."""
    print(">>> Opening Login Page...")
    driver.get("https://www.aeroline.com.my/sign_in.php")
    
    print("\n" + "!"*50)
    print("ACTION REQUIRED: Please manually log in to the website in the browser window.")
    print("Because of the CAPTCHA, this part cannot be automated.")
    print("Once you are successfully logged in and see the Dashboard/Home page, return here.")
    print("!"*50 + "\n")
    
    input(">>> Press ENTER here after you have successfully logged in...")

def check_ticket(driver):
    """Navigates to booking page and checks availability."""
    try:
        print(f">>> Checking availability for {TARGET_DATE}...")
        driver.get("https://www.aeroline.com.my/plan_trip.php")
        
        # 1. Select Route
        # We look for the dropdown usually named 'route' or similar. 
        # Note: Selectors might change; we try to find by fuzzy matching if ID fails.
        try:
            route_dropdown = Select(driver.find_element(By.NAME, "route")) # Common name guess
            route_dropdown.select_by_visible_text(ROUTE_TEXT)
        except:
            # Fallback: Find any select that contains our route text option
            all_selects = driver.find_elements(By.TAG_NAME, "select")
            found = False
            for select_element in all_selects:
                if ROUTE_TEXT in select_element.text:
                    Select(select_element).select_by_visible_text(ROUTE_TEXT)
                    found = True
                    break
            if not found:
                print("Error: Could not find Route dropdown.")
                return False

        # 2. Set Date
        # Aeroline often uses a set of dropdowns (Day, Month, Year) or a single text field.
        # This part attempts to fill a text field if present, or you might need to adjust for dropdowns.
        try:
            # Attempt to find date input. ID is often 'date' or 'depart_date'
            date_input = driver.find_element(By.XPATH, "//input[@name='travel_date' or @id='date']")
            date_input.clear()
            date_input.send_keys(TARGET_DATE)
        except:
            print("Notice: Could not auto-fill date text field. Please ensure date is correct in browser if manual selection is needed.")

        # 3. Submit
        try:
            # Look for a button with text 'Check', 'Search' or 'Next'
            submit_btn = driver.find_element(By.XPATH, "//input[@type='submit' or @value='Next' or @value='Check Availability']")
            submit_btn.click()
        except:
            print("Error: Could not find Submit button.")
            return False

        # 4. Analyze Results
        time.sleep(5) # Wait for results to load
        page_source = driver.page_source.lower()
        
        # Define success or failure keywords based on typical Aeroline responses
        if "no trips found" in page_source or "sold out" in page_source:
            print("Result: No tickets available yet.")
            return False
        elif "select seats" in page_source or "available" in page_source:
            print("SUCCESS: Tickets might be available! Check the browser.")
            return True
        else:
            # Ambiguous result, notify user
            print("Result: Page loaded, but availability status is unclear. Please check browser.")
            return True

    except Exception as e:
        print(f"An error occurred during check: {e}")
        return False

def main():
    driver = start_browser()
    try:
        login_step(driver)
        
        while True:
            found = check_ticket(driver)
            if found:
                print("!!!"*10)
                print(f"TICKET FOUND OR PAGE CHANGED FOR {TARGET_DATE}!")
                print("!!!"*10)
                # Optional: Add code here to send an email/Telegram notification
                break
            
            print(f"Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
            driver.refresh() # Keep session alive
            
    except KeyboardInterrupt:
        print("Stopping script...")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
