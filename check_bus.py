import os
import smtplib
import time
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIG ---
TARGET_DATE = "16-02-2026"
ORIGIN = "SWY" # Sunway
DEST = "SIN"   # Singapore
ROUTE_TEXT = "SWY - SIN"    # Sunway Pyramid to Singapore
LOGIN_URL = "https://www.aeroline.com.my/sign_in.php"
SEARCH_URL = "https://www.aeroline.com.my/plan_trip.php"

def send_notification(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["EMAIL_SENDER"]
    msg["To"] = os.environ["EMAIL_RECEIVER"]

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(os.environ["EMAIL_SENDER"], os.environ["EMAIL_PASSWORD"])
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_availability():
    # Setup Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # 1. Go to domain to initialize context
        print("Initializing session...")
        driver.get(LOGIN_URL)
        
        # 2. INJECT COOKIE (Bypasses Login/CAPTCHA)
        # We need the 'PHPSESSID' (or similar) from your Secrets
        print(f"INJECT COOKIE Bypasses Login/CAPTCHA...")
        session_cookie = {
            "name": "PHPSESSID", 
            "value": os.environ["AEROLINE_SESSION_ID"],
            "domain": "https://www.aeroline.com.my"
        }
        driver.add_cookie(session_cookie)

        
        # 3. Go to Booking Page (Now authenticated)
        print(f"Checking {TARGET_DATE}...")
        driver.get(SEARCH_URL)

        
        print(f"DATA {driver.page_source} ")
        
        # Check if we were kicked out (Cookie Expired)
        if "sign_in.php" in driver.current_url or "New Aeroline User?" in driver.page_source:
            print("Session Expired!")
            send_notification(
                "Action Required: Aeroline Cookie Expired", 
                "The GitHub Action failed to login. Please grab a new PHPSESSID cookie and update your GitHub Secrets."
            )
        #    return

        # 4. Fill Search Form (This varies based on their exact input names)
        # Note: We try to interact with the raw form or URL if possible.
        # If the page loads with a default "Plan Trip" form:
        try:
            # Inject Date via JS if standard input is hard to reach/readonly
            driver.execute_script(f"document.getElementById('date').value = '{TARGET_DATE}'")
            
            # Select Route (Assuming Dropdown)
            # You might need to inspect the page to get exact value for SWY-SIN
            # For now, we print page text to see if we are on the right track
            route_dropdown = Select(driver.find_element(By.NAME, "route")) # Common name guess
            route_dropdown.select_by_visible_text(ROUTE_TEXT)
            pass 
        except:
            pass

        # 5. Simple Availability Check
        # Since we can't easily press 'Submit' blindly on a complex form, 
        # we often check if the date is even clickable or if we can POST directly.
        # *Simplification for Stability:* We check if the page loaded correctly.
        
        # If the booking form is visible, we assume we are "in".
        # To truly check availability, we usually need to click "Next".
        # (This part requires the exact button ID from the live site)
        
        # Placeholder for button click:
        driver.find_element(By.NAME, "imageField").click() 
        
       
        # For now, let's assume if we stay on plan_trip.php, we are good.
        if "Available" in driver.page_source or "RM 128.00" in driver.page_source:
             send_notification(
                f"Aeroline Tickets Available: {TARGET_DATE}",
                f"It looks like tickets might be released! Check now: {SEARCH_URL}"
            )
        else:
            print("Checked. No obvious tickets found yet.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_availability()
