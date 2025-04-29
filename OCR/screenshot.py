import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import os
import extractTxt
def scrape(url):
    print("Scraping URL:", url)
    
    webDriverPath ="/snap/bin/firefox.geckodriver"
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    driver = webdriver.Firefox(service=Service(webDriverPath), options=options)
    
    try:
        driver.get(url)
        sleep(2)
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        sleep(1)
        # get name of website from the url
        urlName = url.split("//")[-1].split("/")[0]
        driver.save_screenshot(urlName+".png")
        print(f"Screenshot saved as {urlName}.png")
        StoreName = urlName
        ImgUrl = urlName+".png"
        extractTxt.Extract(ImgUrl, StoreName)
        os.remove(ImgUrl)
        
        
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()
        print("Driver closed.")
        
    return None


# url=[input("Enter URL: ")]
url=["https://www.thegioididong.com/dtdd/iphone-14-plus"]

for link in url:
    if link == "":
        break
    else:
        scrape(link)
        