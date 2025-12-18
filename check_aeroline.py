import os
import smtplib
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
TARGET_DATE = "16/02/2026"
ROUTE_KEYWORD = "SWY - SIN" # Sunway to Singapore
EMAIL_SENDER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER') # Can be same as sender

def send_notification():
    msg = EmailMessage()
    msg.set_content(f"Tickets for {ROUTE_KEYWORD} on {TARGET_DATE} might be available! \n\nCheck now: https://www.aeroline.com.my/")
    msg['Subject'] = f"AEROLINE ALERT: {TARGET_DATE} Available"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        # Example for Gmail (Requires App Password if 2FA is on)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("Notification email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_availability():
    # Chrome options for GitHub Actions (Headless Linux)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print(f"Checking Aeroline for {TARGET_DATE}...")
        driver.get("https://www.aeroline.com.my/")
        
        wait = WebDriverWait(driver, 20)
        page_source = driver.page_source.lower()
        print(f"Page info: {page_source}...")          
        print(f"Checking route for {ROUTE_KEYWORD}...")
        # 1. Select Route
        route_dropdown = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//select[.//option[contains(text(), '{ROUTE_KEYWORD}')]]")
        ))
        select = Select(route_dropdown)
        for option in select.options:
            if ROUTE_KEYWORD in option.text:
                select.select_by_visible_text(option.text)
                break
        
        print(f"Checking Aeroline for {TARGET_DATE}...")  
        # 2. Enter Date
        date_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'DD/MM/YYYY') or contains(@title, 'Date')]")
        date_input.clear()
        date_input.send_keys(TARGET_DATE)

        # 3. Click Book/Search
        # Note: Selectors may change; looking for the submit button
        search_btn = driver.find_element(By.XPATH, "//input[@type='image' or @type='submit'] | //button[contains(text(), 'Book')]")
        search_btn.click()
        
        # 4. Analyze Results
        # Wait for page load logic (simplified)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        page_source = driver.page_source.lower()

        print(f"Page info: {page_source}...")  
        # Logic: If we see "select seats" or specific pricing, it's likely open.
        # If we see "no trips" or "no schedule", it's closed.
        if "no trips found" in page_source or "no schedule" in page_source:
            print("Result: No tickets yet.")
        else:
            # If the negative keywords aren't there, we assume something loaded.
            # You might need to refine this based on the actual 'Success' page HTML.
            print("Result: POTENTIAL AVAILABILITY.")
            send_notification()

    except Exception as e:
        print(f"Error during check: {e}")
        # Optional: Send email on error if you want to debug
        
    finally:
        driver.quit()

if __name__ == "__main__":
    check_availability()
