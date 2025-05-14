import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep, time
import os
import extractTxt
from urllib.parse import urlparse
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='crawler.log'
)

logger = logging.getLogger('crawler')

def scrape(url, is_original=False, product_name=None, product_sku=None, enemy_name=None, enemy_domain=None):
    """
    Scrape a URL and extract product information
    
    Args:
        url: URL to scrape
        is_original: Whether this is an original product (vs. competitor)
        product_name: Optional name for original products
        product_sku: Optional SKU for original products
        enemy_name: Optional name for competitor website
        enemy_domain: Optional domain for competitor website
        
    Returns:
        dict: Status and result information
    """
    logger.info(f"Starting to scrape URL: {url}")
    
    result = {
        "success": False,
        "url": url,
        "error": None,
        "message": None
    }
    
    if not url or not url.startswith(('http://', 'https://')):
        error_msg = f"Invalid URL: {url}"
        logger.error(error_msg)
        result["error"] = error_msg
        return result
    
    webDriverPath = "/snap/bin/firefox.geckodriver"
    options = FirefoxOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    
    # Add page load timeout
    options.set_preference("page.load.timeout", 30000)  # 30 seconds
    
    driver = None
    screenshot_path = None
    
    try:
        # Get domain information
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        urlName = domain.split(".")[-2] if len(domain.split(".")) > 1 else domain
        timestamp = int(time())  # Get current timestamp
        screenshot_path = f"{urlName}.png"  
        logger.info(f"Initializing webdriver for {url}")
        driver = webdriver.Firefox(service=Service(webDriverPath), options=options)
        driver.set_page_load_timeout(30)  # 30 seconds timeout
        
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Dismiss popups or overlays
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            sleep(1)
            body.send_keys(Keys.ESCAPE)
            logger.info("Attempted to dismiss popups")
        except Exception as e:
            logger.warning(f"Could not dismiss popups: {str(e)}")
        
        # Allow page to stabilize
        sleep(2)
        
        # Take screenshot
        logger.info(f"Taking screenshot as {screenshot_path}")
        driver.save_screenshot(screenshot_path)
        
        # Extract data
        if is_original:
            logger.info(f"Processing as original product: {product_name}")
            extractTxt.Extract(
                imgURL=screenshot_path, 
                link=url, 
                enemyOrOriginal='original',
                enemyName=None,
                enemyDomain=None
            )
        else:
            # Use provided enemy_name/domain if available, otherwise use values from URL
            final_enemy_name = enemy_name if enemy_name else urlName
            final_enemy_domain = enemy_domain if enemy_domain else domain
            logger.info(f"Processing as competitor product: {final_enemy_name}")
            
            extractTxt.Extract(
                imgURL=screenshot_path, 
                link=url, 
                enemyOrOriginal='enemy',
                enemyName=final_enemy_name,
                enemyDomain=final_enemy_domain
            )
        
        # Operation successful
        result["success"] = True
        result["message"] = f"Successfully crawled {url}"
        logger.info(f"Successfully crawled {url}")
        
    except TimeoutException as e:
        error_msg = f"Timeout while loading {url}: {str(e)}"
        logger.error(error_msg)
        result["error"] = error_msg
        
    except WebDriverException as e:
        error_msg = f"WebDriver error for {url}: {str(e)}"
        logger.error(error_msg)
        result["error"] = error_msg
        
    except Exception as e:
        error_msg = f"Error crawling {url}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        result["error"] = error_msg
        
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {str(e)}")
        
        # Remove screenshot file
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
                logger.info(f"Removed screenshot: {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not remove screenshot {screenshot_path}: {str(e)}")
    
    return result
