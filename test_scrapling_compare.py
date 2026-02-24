"""
Side-by-side comparison: Selenium vs Scrapling
Tests all 3 Unistellar scraper targets.
"""
import re, time

# ── shared regex (identical to backend/scrape.py) ──────────────────────────
_ASTEROID_PATTERN = re.compile(
    r'(?:'
    r'\(\d+\)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|'
    r'\d{5,}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|'
    r'\d{1,4}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|'
    r'\d{4}\s+[A-Z]{1,2}\d+|'
    r'\d{4}\s+[A-Z]{2}\d*'
    r')'
)
_COMET_PATTERN = re.compile(
    r'(?:'
    r'[CAPI]/\d{4}\s+[A-Z]\d*\s+\([^)]+\)|'
    r'\d+[A-Za-z]/[A-Za-z][A-Za-z0-9\-]+(?:\s+\d+)?'
    r')'
)
_PAREN_NUM_RE = re.compile(r'^\((\d+)\)\s+')

def _normalize(name):
    return _PAREN_NUM_RE.sub(r'\1 ', name)


def _deep_text(cell):
    """Get ALL text from a Scrapling element, including child elements.

    Scrapling's .text only returns the element's direct text node.
    Selenium's .text returns all descendant text concatenated.
    This helper makes Scrapling behave like Selenium by using ::text.
    """
    parts = cell.css("::text")
    if parts:
        return " ".join(p.text.strip() for p in parts if p.text.strip())
    return cell.text.strip()


# ═══════════════════════════════════════════════════════════════════════════
# TRANSIENT EVENTS PAGE
# ═══════════════════════════════════════════════════════════════════════════

def transient_scrapling():
    from scrapling.fetchers import StealthyFetcher

    url = "https://alerts.unistellaroptics.com/transient/events.html"
    t0 = time.perf_counter()
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True)

    headers = [_deep_text(h).replace('\n', ' ') for h in page.css("table th")]
    if headers and not headers[0]:
        headers[0] = "DeepLink"

    data = []
    for row in page.css("table tbody tr"):
        cells = row.css("td")
        if len(cells) < 2:
            continue
        row_data = []
        for i, cell in enumerate(cells):
            if i == 0:
                link_el = cell.css("a")
                row_data.append(link_el[0].attrib.get("href", "") if link_el else "")
            else:
                row_data.append(_deep_text(cell))
        data.append(row_data)

    elapsed = time.perf_counter() - t0
    return headers, data, elapsed


def transient_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import os

    url = "https://alerts.unistellaroptics.com/transient/events.html"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    system_driver_path = "/usr/bin/chromedriver"
    if os.path.exists(system_driver_path):
        service = Service(system_driver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    try:
        t0 = time.perf_counter()
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        time.sleep(2)

        header_els = driver.find_elements(By.TAG_NAME, "th")
        headers = [h.text.strip().replace('\n', ' ') for h in header_els]
        if headers and not headers[0]:
            headers[0] = "DeepLink"

        data = []
        for row in driver.find_elements(By.CSS_SELECTOR, "table tbody tr"):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 2:
                continue
            row_data = []
            for i, cell in enumerate(cells):
                if i == 0:
                    try:
                        link = cell.find_element(By.TAG_NAME, "a").get_attribute("href")
                        row_data.append(link)
                    except Exception:
                        row_data.append("")
                else:
                    row_data.append(cell.text.strip())
            data.append(row_data)

        elapsed = time.perf_counter() - t0
        return headers, data, elapsed
    finally:
        driver.quit()


# ═══════════════════════════════════════════════════════════════════════════
# COMET MISSIONS PAGE
# ═══════════════════════════════════════════════════════════════════════════

def comets_scrapling():
    from scrapling.fetchers import StealthyFetcher

    url = "https://science.unistellar.com/comets/missions/"
    t0 = time.perf_counter()
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True)

    elements = page.css("h1,h2,h3,h4,p,.et_pb_text_inner")
    text = " ".join(re.sub(r'\s+', ' ', _deep_text(el)) for el in elements if _deep_text(el))
    elapsed = time.perf_counter() - t0

    found = list(dict.fromkeys(_COMET_PATTERN.findall(text)))
    return found, text, elapsed


def comets_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import os

    url = "https://science.unistellar.com/comets/missions/"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    system_driver_path = "/usr/bin/chromedriver"
    if os.path.exists(system_driver_path):
        service = Service(system_driver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    try:
        t0 = time.perf_counter()
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        elements = driver.find_elements(By.CSS_SELECTOR, "h1,h2,h3,h4,p,.et_pb_text_inner")
        text = " ".join(re.sub(r'\s+', ' ', el.text) for el in elements if el.text.strip())
        elapsed = time.perf_counter() - t0

        found = list(dict.fromkeys(_COMET_PATTERN.findall(text)))
        return found, text, elapsed
    finally:
        driver.quit()


# ═══════════════════════════════════════════════════════════════════════════
# ASTEROID MISSIONS PAGE
# ═══════════════════════════════════════════════════════════════════════════

def asteroids_scrapling():
    from scrapling.fetchers import StealthyFetcher

    url = "https://science.unistellar.com/planetary-defense/missions/"
    t0 = time.perf_counter()
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True)

    elements = page.css("h1,h2,h3,h4,p,.et_pb_text_inner")
    text = " ".join(re.sub(r'\s+', ' ', _deep_text(el)) for el in elements if _deep_text(el))
    elapsed = time.perf_counter() - t0

    found = list(dict.fromkeys(_normalize(m) for m in _ASTEROID_PATTERN.findall(text)))
    return found, text, elapsed


def asteroids_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import os

    url = "https://science.unistellar.com/planetary-defense/missions/"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    system_driver_path = "/usr/bin/chromedriver"
    if os.path.exists(system_driver_path):
        service = Service(system_driver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    try:
        t0 = time.perf_counter()
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        elements = driver.find_elements(By.CSS_SELECTOR, "h1,h2,h3,h4,p,.et_pb_text_inner")
        text = " ".join(re.sub(r'\s+', ' ', el.text) for el in elements if el.text.strip())
        elapsed = time.perf_counter() - t0

        found = list(dict.fromkeys(_normalize(m) for m in _ASTEROID_PATTERN.findall(text)))
        return found, text, elapsed
    finally:
        driver.quit()


# ═══════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def compare_table(label, sp_h, sp_d, sp_t, se_h, se_d, se_t):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"  {'':20s} {'Scrapling':>12s}  {'Selenium':>12s}")
    print(f"  {'Time':20s} {sp_t:>11.2f}s  {se_t:>11.2f}s")
    print(f"  {'Rows':20s} {len(sp_d):>12d}  {len(se_d):>12d}")
    print(f"  {'Headers match':20s} {'YES' if sp_h == se_h else 'NO':>12s}")

    if sp_d and se_d:
        # Compare Name column (index 1) for first 5 rows
        print(f"\n  Name column (first 5 rows):")
        for i in range(min(5, len(sp_d), len(se_d))):
            sp_name = sp_d[i][1] if len(sp_d[i]) > 1 else "?"
            se_name = se_d[i][1] if len(se_d[i]) > 1 else "?"
            match = "  OK" if sp_name == se_name else "  DIFF"
            print(f"    [{i}] Scrapling: {sp_name:20s}  Selenium: {se_name:20s} {match}")

        # Full row-by-row match
        exact = sum(1 for a, b in zip(sp_d, se_d) if a == b)
        print(f"\n  Exact row matches: {exact}/{min(len(sp_d), len(se_d))}")


def compare_text(label, sp_found, sp_text, sp_t, se_found, se_text, se_t):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"  {'':20s} {'Scrapling':>12s}  {'Selenium':>12s}")
    print(f"  {'Time':20s} {sp_t:>11.2f}s  {se_t:>11.2f}s")
    print(f"  {'Text chars':20s} {len(sp_text):>12d}  {len(se_text):>12d}")
    print(f"  {'Matches found':20s} {len(sp_found):>12d}  {len(se_found):>12d}")

    if sp_found:
        print(f"  Scrapling found: {sp_found}")
    if se_found:
        print(f"  Selenium found:  {se_found}")

    if not sp_found and not se_found:
        print(f"  (neither found matches -- page may have been redesigned)")
    elif set(sp_found) == set(se_found):
        print(f"  IDENTICAL results")
    else:
        only_sp = set(sp_found) - set(se_found)
        only_se = set(se_found) - set(sp_found)
        if only_sp:
            print(f"  Only Scrapling: {only_sp}")
        if only_se:
            print(f"  Only Selenium:  {only_se}")

    # Cloudflare detection
    if "checking your browser" in se_text.lower() and "checking your browser" not in sp_text.lower():
        print(f"  ** Selenium BLOCKED by Cloudflare -- Scrapling bypassed it **")


if __name__ == "__main__":
    print("Running all 3 scraper comparisons...\n")

    # ── 1. Transient Events (table scraper) ─────────────────────────────
    print("[1/3] Transient Events page...")
    sp_h, sp_d, sp_t = transient_scrapling()
    se_h, se_d, se_t = transient_selenium()
    compare_table("TRANSIENT EVENTS (Cosmic Cataclysm)", sp_h, sp_d, sp_t, se_h, se_d, se_t)

    # ── 2. Comet Missions (text scraper) ────────────────────────────────
    print("\n[2/3] Comet Missions page...")
    sp_cf, sp_ct, sp_ctime = comets_scrapling()
    se_cf, se_ct, se_ctime = comets_selenium()
    compare_text("COMET MISSIONS", sp_cf, sp_ct, sp_ctime, se_cf, se_ct, se_ctime)

    # ── 3. Asteroid Missions (text scraper) ─────────────────────────────
    print("\n[3/3] Asteroid Missions page...")
    sp_af, sp_at, sp_atime = asteroids_scrapling()
    se_af, se_at, se_atime = asteroids_selenium()
    compare_text("ASTEROID MISSIONS", sp_af, sp_at, sp_atime, se_af, se_at, se_atime)

    # ── Final summary ───────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  FINAL SUMMARY")
    print(f"{'=' * 60}")
    print(f"  {'Page':25s} {'Scrapling':>10s} {'Selenium':>10s} {'Winner':>10s}")
    print(f"  {'-'*55}")

    tests = [
        ("Transient Events", sp_t, se_t, len(sp_d), len(se_d)),
        ("Comet Missions", sp_ctime, se_ctime, len(sp_cf), len(se_cf)),
        ("Asteroid Missions", sp_atime, se_atime, len(sp_af), len(se_af)),
    ]
    for name, st, set_, sc, sec in tests:
        winner = "Scrapling" if sc > sec else ("Selenium" if sec > sc else ("Tie" if sc == sec else "Tie"))
        if sc == sec:
            winner = "Scrapling" if st < set_ else "Selenium"
        print(f"  {name:25s} {st:>9.1f}s {set_:>9.1f}s {winner:>10s}")
        print(f"  {'':25s} {sc:>9d}r {sec:>9d}r")
