import time
from typing import Any

from cloudflare_bypass import CloudflareBypasser  # type: ignore[import-untyped]
from cloudflare_bypass.utils import (  # type: ignore[import-untyped]
    CloudflareFingerprinting,
    HumanBehaviorSimulator,
)
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome  # type: ignore[import-untyped]

from .human import is_visible


class CloudflareSolver:
    def __init__(self, driver: Chrome, bypasser: Any | None = None):
        self.driver = driver
        self.bypasser = bypasser or CloudflareBypasser(headless=False)
        self._attach_existing_driver()

    def _attach_existing_driver(self) -> None:
        self.bypasser.driver = self.driver
        self.bypasser.wait = WebDriverWait(self.driver, self.bypasser.config.timeout)
        self.bypasser.behavior_sim = HumanBehaviorSimulator(self.driver)
        self.bypasser.fingerprinting = CloudflareFingerprinting(self.driver)

    def is_challenge_present(self) -> bool:
        """Detect if Cloudflare challenge/waiting room is present."""
        page_source = self.driver.page_source.lower()
        has_cloudflare_text = (
            "just a moment" in page_source
            or "checking if the site connection is secure" in page_source
            or "cf-challenge" in page_source
        )
        if has_cloudflare_text:
            return True

        try:
            return is_visible(self.driver, "#cf-challenge-running", timeout=1) or is_visible(
                self.driver, "div.cf-turnstile", timeout=1
            )
        except Exception:
            return False

    def solve(self, timeout: int = 30) -> bool:
        """Attempt to resolve Cloudflare on the current page using the active browser."""
        if not self.is_challenge_present():
            return True

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                remaining = max(1, int(deadline - time.time()))
                if self.bypasser._detect_and_bypass_cloudflare(remaining):
                    return True
            except Exception:
                time.sleep(1)

            time.sleep(1)
            if not self.is_challenge_present():
                return True

        return not self.is_challenge_present()
