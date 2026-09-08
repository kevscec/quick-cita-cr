import contextlib
import random
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome  # type: ignore[import-untyped]


def human_delay(min_ms: int = 500, max_ms: int = 2000) -> None:
    """Pause for a random time between min_ms and max_ms to simulate human behavior."""
    time.sleep(random.uniform(min_ms / 1000.0, max_ms / 1000.0))


def human_type(
    element: WebElement, text: str, min_delay_ms: int = 30, max_delay_ms: int = 150
) -> None:
    """Type text into an element with random delays between keystrokes."""
    element.clear()
    for char in text:
        element.send_keys(char)
        human_delay(min_delay_ms, max_delay_ms)
    human_delay(300, 800)


def human_click(driver: Chrome, element: WebElement) -> None:
    """Move the mouse to an element and click it with a slight delay."""
    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.pause(random.uniform(0.1, 0.4))
    actions.click()
    actions.perform()
    human_delay(500, 1500)


def wait_and_find(
    driver: Chrome, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10
) -> WebElement:
    """Wait for an element to be present and return it."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))


def wait_and_find_clickable(
    driver: Chrome, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10
) -> WebElement:
    """Wait for an element to be clickable and return it."""
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))


def is_visible(driver: Chrome, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 1) -> bool:
    """Check if an element is visible within a short timeout."""
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, selector)))
        return True
    except TimeoutException:
        return False


def wait_for_hidden(
    driver: Chrome, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10
) -> None:
    """Wait for an element to become invisible/hidden."""
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((by, selector)))
