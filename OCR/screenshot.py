import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import os
import ExtractTxt
import time
from dotenv import load_dotenv
import os
import cv2 as cv
load_dotenv()

DriverPath = os.getenv("SELENIUM_DRIVER_PATH")
chromeOrFirefox = os.getenv("CHROME_OR_FIREFOX")


def scrape(url):
    print("Scraping URL:", url)
    

    webDriverPath = DriverPath
    print("WebDriver Path:", webDriverPath)
    print("Browser choice:", chromeOrFirefox)
    if chromeOrFirefox == "firefox":
        from selenium.webdriver.firefox.service import Service
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        # Set window size for Firefox
        # options.add_argument("--width=1366")
        # options.add_argument("--height=768")
        driver = webdriver.Firefox(service=Service(webDriverPath), options=options)
        print("Using Firefox WebDriver")
    elif chromeOrFirefox == "chrome":
        from selenium.webdriver.chrome.service import Service
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        # Set window size for Chrome
        # options.add_argument("--window-size=1366,768")
        driver = webdriver.Chrome(service=Service(webDriverPath), options=options)
        print("Using Chrome WebDriver")
    else:
        print("Invalid browser choice. Please set CHROME_OR_FIREFOX to 'chrome' or 'firefox'.")
        print("defaulting to firefox")
        from selenium.webdriver.firefox.service import Service
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        # Set window size for Firefox
        # options.add_argument("--width=1366")
        # options.add_argument("--height=768")
        driver = webdriver.Firefox(service=Service(webDriverPath), options=options)
        print("Using Firefox WebDriver")
    try:
        driver.get(url)
        sleep(3)
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            sleep(1)
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        sleep(1)
        domain = url.split("//")[-1].split("/")[0]
        timestamp = str(int(time.time()))
        driver.save_screenshot(domain+"_"+timestamp+".png")
        print(f"Screenshot saved as {domain+"_"+timestamp}.png")
        image = cv.imread(domain+"_"+timestamp+".png")
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        cv.imwrite(domain+"_"+timestamp+".png", gray)
        print(f"Screenshot saved as {domain+"_"+timestamp}.png")
        responseJson= ExtractTxt.Extract(domain+"_"+timestamp+".png")
        os.remove(domain+"_"+timestamp+".png")
        
        
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()
        print("Driver closed.")
        
    # convert the promotional_price and current_price to float (20.2300.123 VND,d $,...)
    def clean_price_string(price_str):
        if not isinstance(price_str, str):
            return 0.0
        
        try:
            # Remove currency symbols and formatting characters
            cleaned = price_str.replace('VND', '').replace('VNĐ', '').replace('₫', '')
            cleaned = cleaned.replace('vnd', '').replace('vnđ', '').replace('đ', '')
            cleaned = cleaned.replace('$', '').replace(' ', '')
            
            # Replace comma with empty string if used as thousand separator
            # Keep only digits - this removes any unexpected characters
            digits_only = ''.join(c for c in cleaned if c.isdigit())
            
            if not digits_only:
                return 0.0
                
            return float(digits_only)
        except Exception as e:
            print(f"Error converting price: {price_str}, Error: {e}")
            return 0.0
    
    print("Response JSON:", responseJson)
    if 'promotional_price' in responseJson:
        responseJson['promotional_price'] = clean_price_string(responseJson['promotional_price'])
    if 'current_price' in responseJson:
        responseJson['current_price'] = clean_price_string(responseJson['current_price'])
    return responseJson

