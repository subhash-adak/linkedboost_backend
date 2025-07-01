import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class LinkedInConnector:
    def __init__(self, email, password, headless=True):
        self.email = email
        self.password = password

        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 15)

    def login(self):
        print("Logging in to LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            self.wait.until(EC.url_contains("linkedin.com/feed"))
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def search_by_keyword(self, keyword, start_page=1):
        print(f"Searching for keyword: {keyword}")
        base_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ', '%20')}"
        search_url = f"{base_url}&page={start_page}" if start_page > 1 else base_url
        self.driver.get(search_url)
        time.sleep(8)
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
        return True

    def go_to_next_page(self):
        try:
            next_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'artdeco-pagination__button--next')]")
            if next_button.is_enabled():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(8)
                return True
            return False
        except NoSuchElementException:
            return False

    def send_connection_requests(self, requests_per_page=10):
        sent_count = 0
        time.sleep(5)

        connect_buttons = self.driver.find_elements(By.XPATH,
            "//button[contains(@class, 'artdeco-button--secondary') and contains(@aria-label, 'Invite')]")
        if not connect_buttons:
            connect_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(@class, 'artdeco-button--secondary') and .//span[text()='Connect']]")

        for i, button in enumerate(connect_buttons):
            if sent_count >= requests_per_page:
                break
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(3)

                send_button_selectors = [
                    "//button[contains(@aria-label, 'Send now')]",
                    "//button[contains(@aria-label, 'Send without a note')]",
                    "//button[contains(@class, 'artdeco-button--primary') and .//span[contains(text(), 'Send')]]"
                ]
                for selector in send_button_selectors:
                    try:
                        send_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        self.driver.execute_script("arguments[0].click();", send_button)
                        sent_count += 1
                        break
                    except:
                        continue

                time.sleep(random.uniform(5, 10))
            except Exception as e:
                print(f"Skipping profile: {e}")
                continue
        return sent_count

    def run_multi_page_campaign(self, keyword, start_page=1, end_page=1, requests_per_page=10):
        total_sent = 0
        if not self.search_by_keyword(keyword, start_page):
            return 0

        for page in range(start_page, end_page + 1):
            print(f"Sending requests on page {page}")
            total_sent += self.send_connection_requests(requests_per_page)
            if page < end_page:
                if not self.go_to_next_page():
                    break
        return total_sent

    def close(self):
        self.driver.quit()
        print("Browser closed.")
