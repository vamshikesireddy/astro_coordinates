import re
import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_unistellar_table():
    url = "https://alerts.unistellaroptics.com/transient/events.html"
    
    # Setup Chrome options
    options = Options()
    options.add_argument("--headless")  # Run without opening a window
    options.add_argument("--no-sandbox") # Required for server environments
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Check for system-installed chromedriver (Docker / Streamlit Cloud)
    system_driver_path = "/usr/bin/chromedriver"
    if os.path.exists(system_driver_path):
        service = Service(system_driver_path)
    else:
        # Local fallback
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    try:
        print("Connecting to Unistellar Alerts...")
        driver.get(url)

        # Wait up to 15 seconds for the table body to contain at least one row
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        
        # Brief pause to ensure all React elements are rendered
        time.sleep(2)

        # Get headers
        header_elements = driver.find_elements(By.TAG_NAME, "th")
        headers = [h.text.strip().replace('\n', ' ') for h in header_elements]
        if not headers[0]: headers[0] = "DeepLink"

        # Get all rows
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        data = []

        print(f"Found {len(rows)} targets. Extracting data...")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 2: continue
            
            row_data = []
            for i, cell in enumerate(cells):
                if i == 0: # Handle the deep link icon
                    try:
                        link = cell.find_element(By.TAG_NAME, "a").get_attribute("href")
                        row_data.append(link)
                    except:
                        row_data.append("")
                else:
                    row_data.append(cell.text.strip())
            data.append(row_data)

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        print("\nSuccess! Sample of scraped data:")
        print(df.head(3))
        print(f"\nExtracted {len(df)} rows.")
        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        driver.quit()

_COMET_PATTERN = re.compile(
    r'(?:'
    r'[CAPI]/\d{4}\s+[A-Z]\d*\s+\([^)]+\)|'       # C/2025 N1 (ATLAS), A/..., P/2010 H2 (Vales)
    r'\d+[A-Za-z]/[A-Za-z][A-Za-z0-9\-]+(?:\s+\d+)?'  # 29P/Schwassmann-Wachmann 1, 3I/ATLAS, 235P/LINEAR
    r')'
)


def scrape_unistellar_priority_comets():
    """Scrapes the Unistellar comet missions page to extract active priority comet designations."""
    url = "https://science.unistellar.com/comets/missions/"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    system_driver_path = "/usr/bin/chromedriver"
    if os.path.exists(system_driver_path):
        service = Service(system_driver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # Collect text from headings and content sections (Divi theme structure)
        elements = driver.find_elements(By.CSS_SELECTOR, "h1,h2,h3,h4,p,.et_pb_text_inner")
        text = " ".join(re.sub(r'\s+', ' ', el.text) for el in elements if el.text.strip())

        # Extract and deduplicate comet designations
        found = list(dict.fromkeys(_COMET_PATTERN.findall(text)))
        return found
    except Exception as e:
        print(f"Failed to scrape Unistellar missions page: {e}")
        return []
    finally:
        driver.quit()


_ASTEROID_PATTERN = re.compile(
    r'(?:'
    r'\(\d+\)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|'  # (2033) Basilea, (3260) Vizbor — IAU parenthesized format
    r'\d{5,}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|'   # 99942 Apophis, 101955 Bennu
    r'\d{1,4}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|'  # 433 Eros, 16 Psyche, 2033 Basilea
    r'\d{4}\s+[A-Z]{1,2}\d+|'                       # 2024 YR4, 1994 PC1
    r'\d{4}\s+[A-Z]{2}\d*'                          # 2001 SN263, 2001 FD58
    r')'
)

_PAREN_NUM_RE = re.compile(r'^\((\d+)\)\s+')


def _normalize_asteroid_match(name):
    """Convert IAU parenthesized format '(2033) Basilea' → '2033 Basilea'."""
    return _PAREN_NUM_RE.sub(r'\1 ', name)


def scrape_unistellar_priority_asteroids():
    """Scrapes the Unistellar planetary defense missions page to extract active priority asteroid designations."""
    url = "https://science.unistellar.com/planetary-defense/missions/"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    system_driver_path = "/usr/bin/chromedriver"
    if os.path.exists(system_driver_path):
        service = Service(system_driver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # Collect text from headings and content sections (Divi theme structure)
        elements = driver.find_elements(By.CSS_SELECTOR, "h1,h2,h3,h4,p,.et_pb_text_inner")
        text = " ".join(re.sub(r'\s+', ' ', el.text) for el in elements if el.text.strip())

        # Extract, normalize parenthesized numbers, and deduplicate
        raw = _ASTEROID_PATTERN.findall(text)
        found = list(dict.fromkeys(_normalize_asteroid_match(m) for m in raw))
        return found
    except Exception as e:
        print(f"Failed to scrape Unistellar planetary defense page: {e}")
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_unistellar_table()