import os
import time
import schedule
import smtplib
import ssl
from email.message import EmailMessage
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
DEPARTURE_DATE = "18/02/2026"
ROUTE_VALUE = "SWY - SIN"

# --- Email Configuration ---
# We read these from the environment variables for security
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

def send_email_alert():
    """Sends an email notification when tickets are found."""
    subject = f"URGENT: Aeroline Tickets Available for {DEPARTURE_DATE}!"
    body = f"""
    Ticket availability detected!
    
    Route: {ROUTE_VALUE}
    Date: {DEPARTURE_DATE}
    
    Go book now: {TARGET_URL}
    """

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        # Standard Gmail SMTP settings
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(">>> Email notification sent successfully!")
    except Exception as e:
        print(f">>> Failed to send email: {e}")

def get_driver():
    """Sets up the Chrome Webdriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def check_ticket_availability():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking availability...")
    driver = None
    
    try:
        driver = get_driver()
        driver.get(TARGET_URL)

        wait = WebDriverWait(driver, 15)
        
        # 1. Select Route
        route_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "route")))
        select = Select(route_dropdown)
        
        try:
            select.select_by_visible_text(ROUTE_VALUE)
        except Exception:
            found = False
            for option in select.options:
                if "SWY" in option.text and "SIN" in option.text:
                    option.click()
                    found = True
                    break
            if not found:
                print("Error: Could not find route.")
                return

        # 2. Input Date
        date_input = driver.find_element(By.NAME, "ddate")
        date_input.clear()
        date_input.send_keys(DEPARTURE_DATE)

        # 3. Click Search
        search_btn = driver.find_element(By.XPATH, "//input[@type='image' or @type='submit']")
        search_btn.click()

        # 4. Analyze Results
        time.sleep(5)
        page_source = driver.page_source.lower()

        if "no trip found" in page_source or "no seats available" in page_source:
            print("Status: No tickets available yet.")
        elif "select seat" in page_source or "price" in page_source:
            print("\n" + "="*40)
            print(f"SUCCESS! Tickets found for {DEPARTURE_DATE}!")
            print("="*40 + "\n")
            
            # TRIGGER THE EMAIL
            send_email_alert()
            
            # Optional: Stop the script after finding tickets so you don't get spammed
            return "FOUND" 
        else:
            print("Status: Result unclear (Check manually).")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()

# --- Scheduling ---
def job():
    result = check_ticket_availability()
    if result == "FOUND":
        print("Tickets found. Stopping scheduler.")
        return schedule.CancelJob

# Schedule to run every hour
schedule.every(1).hours.do(job)

print("Script running... Checking immediately first.")
job() # Run once on startup

while True:
    schedule.run_pending()
    time.sleep(1)
