from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import random


def format_string(text, length):
    # Replace spaces with "-"
    text = text.replace(" ", "-")
    # Center the text with "-" padding
    return text.center(length, "-")


def safe_find_element(parent, selector):
    from selenium.common.exceptions import NoSuchElementException

    try:
        return parent.find_element(By.CSS_SELECTOR, selector)
    except NoSuchElementException:
        return None


def safe_find_elements_many(parent, selector):
    from selenium.common.exceptions import NoSuchElementException

    try:
        return parent.find_elements(By.CSS_SELECTOR, selector)
    except NoSuchElementException:
        return []


def safe_find_text(element):
    if element:
        return element.get_attribute("innerText").strip()
    return None


# Function to check if the page has been scrolled to the end
def is_end_of_page(driver):
    # Get the current scroll position
    current_scroll_position = driver.execute_script(
        "return window.scrollY + window.innerHeight;"
    )
    # Get the total scrollable height of the page
    total_scroll_height = driver.execute_script("return document.body.scrollHeight;")
    # Check if the current scroll position is at the bottom
    return current_scroll_position >= total_scroll_height


def get_driver():
    # List of user-agents
    user_agents = [
        # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/124.0',
        # "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
    ]

    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    choosed_user_agent = random.choice(user_agents)
    print("Using User-Agent: ", choosed_user_agent)
    chrome_options.add_argument(f"user-agent={choosed_user_agent}")

    # Tắt các dịch vụ Google không cần thiết
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Tắt logging để giảm noise
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")

    # Khởi tạo WebDriver với nhiều cách khác nhau
    driver = None
    # Cách 1: Thử sử dụng webdriver-manager (cần cài đặt: pip install webdriver-manager)
    try:
        from webdriver_manager.chrome import ChromeDriverManager

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except ImportError:
        print("webdriver-manager chưa được cài đặt")
        return None
    except Exception as e:
        print(f"Lỗi khi khởi tạo WebDriver với webdriver-manager: {e}")
        return None
