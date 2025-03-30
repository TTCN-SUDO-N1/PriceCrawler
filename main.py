import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from time import sleep
import clean
def scrape(url):
    print("Scraping URL:", url)
    
    webDriverPath ="./geckodriver"
    options = webdriver.FirefoxOptions()
    driver = webdriver.Firefox(service=Service(webDriverPath), options=options)
    
    try:
        driver.get(url)
        sleep(6)  
        
        # scroll down to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(2)  # Wait for additional content to load
        
        # scroll back up
        driver.execute_script("window.scrollTo(0, 0);")
        sleep(2)  
        
        html = driver.page_source
        urltxt = clean.cleanUrl(url)
        filename = urltxt+".html"  # Fixed filename for simplicity
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
            print(f"HTML saved to {filename}")
        
        return html
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()
        print("Driver closed.")
        
    return None

scrape("https://phongvu.vn/c/may-tinh-de-ban")