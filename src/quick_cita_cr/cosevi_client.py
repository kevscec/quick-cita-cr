from __future__ import annotations

from datetime import UTC, datetime

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from undetected_chromedriver import Chrome  # type: ignore[import-untyped]

from .browser import (
    CloudflareSolver,
    get_browser,
    human_click,
    human_delay,
    human_type,
    is_visible,
    wait_and_find,
    wait_and_find_clickable,
    wait_for_hidden,
)
from .config import AppConfig, Secrets
from .models import BranchSnapshot
from .parser import parse_appointment_dates

LOGIN_URL = "https://servicios.educacionvial.go.cr/Formularios/IngresarCuenta"
PRACTICAL_TEST_URL = "https://servicios.educacionvial.go.cr/Formularios/MatriculaPruebaPractica"
PORTAL_URL = "https://servicios.educacionvial.go.cr/Formularios/Servicios"


class HumanInterventionRequired(RuntimeError):
    pass


class CoseviBrowserClient:
    def __init__(self, config: AppConfig, secrets: Secrets, headed: bool | None = None):
        self.config = config
        self.secrets = secrets
        self.headless = config.browser.headless if headed is None else not headed
        self._driver: Chrome | None = None

    def __enter__(self) -> CoseviBrowserClient:
        profile_dir = self.config.browser.profile_dir.expanduser()

        driver = get_browser(
            profile_dir=profile_dir,
            executable_path=self.config.browser.executable_path,
            headless=self.headless,
        )
        self._driver = driver

        # Set page load timeout based on config
        driver.set_page_load_timeout(self.config.browser.timeout_seconds)

        self.solver = CloudflareSolver(driver)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None

    @property
    def driver(self) -> Chrome:
        if not self._driver:
            raise RuntimeError("Browser not initialized. Use as a context manager.")
        return self._driver

    def _solve_cloudflare(self) -> None:
        """Wait for Cloudflare resolution if present"""
        if self.solver.is_challenge_present():
            if not self.solver.solve(timeout=45):
                raise HumanInterventionRequired(
                    "Cloudflare challenge could not be bypassed automatically. Run with --headed."
                )
            human_delay(1000, 2000)

    def ensure_logged_in(self) -> None:
        self.driver.get(LOGIN_URL)
        self._solve_cloudflare()

        if self._looks_logged_in():
            return

        self._stop_if_human_verification_visible()

        # ID Type
        id_type_select = Select(wait_and_find(self.driver, "select.selector-tipos-identificacion"))
        id_type_select.select_by_value(self.secrets.id_type)
        human_delay(300, 800)

        # Identification
        id_input = wait_and_find(self.driver, "#identificacion")
        human_type(id_input, self.secrets.identification.get_secret_value())

        # Password
        pass_input = wait_and_find(self.driver, "#contrasena")
        human_type(pass_input, self.secrets.password.get_secret_value())

        # Submit
        submit_btn = wait_and_find_clickable(self.driver, "#botonAcceder")
        human_click(self.driver, submit_btn)

        self._wait_for_loading_modal()
        self._dismiss_existing_session_prompt()
        self._stop_if_human_verification_visible()

        if not self._looks_logged_in():
            raise RuntimeError(
                "Login did not reach an authenticated page; run with --headed to inspect."
            )

    def prepare_practical_test_flow(self) -> None:
        self.ensure_logged_in()
        self.driver.get(PRACTICAL_TEST_URL)
        self._solve_cloudflare()

        self._stop_if_human_verification_visible()

        # Receipt Number
        receipt_input = wait_and_find(self.driver, "#numRecibo")
        human_type(receipt_input, self.secrets.receipt_number.get_secret_value())

        # License Class
        license_select = Select(wait_and_find(self.driver, "select.selector-licencia"))
        try:
            license_select.select_by_value(self.config.appointment.license_class)
        except NoSuchElementException:
            license_select.select_by_visible_text(self.config.appointment.license_class)
        human_delay(400, 900)

        # Accept terms
        checkbox = wait_and_find(self.driver, "#check-AceptaTerminos")
        if not checkbox.is_selected():
            human_click(self.driver, checkbox)

        # Continue
        continue_btn = wait_and_find_clickable(self.driver, "#botonContinuar")
        human_click(self.driver, continue_btn)

        self._wait_for_loading_modal()

    def check_branch(self, branch: str) -> BranchSnapshot:
        if not self._branch_list_visible():
            self.prepare_practical_test_flow()

        self._select_branch(branch)

        continue_btn = wait_and_find_clickable(self.driver, "#botonContinuarSedes")
        human_click(self.driver, continue_btn)

        self._wait_for_loading_modal()
        self._stop_if_human_verification_visible()

        # Extract text from page body
        body_element = wait_and_find(self.driver, "body")
        text = body_element.text

        slots = parse_appointment_dates(text, branch=branch)
        self._go_back_to_branches_if_possible()

        return BranchSnapshot(branch=branch, checked_at=datetime.now(UTC), slots=slots)

    def _looks_logged_in(self) -> bool:
        return is_visible(self.driver, "a.encabezado-boton-salir:not(.oculto)", timeout=3)

    def _branch_list_visible(self) -> bool:
        return is_visible(self.driver, "#listaSedes", timeout=3)

    def _select_branch(self, branch: str) -> None:
        try:
            items = self.driver.find_elements(By.CSS_SELECTOR, "#listaSedes li")
            for item in items:
                if branch.lower() in item.text.lower():
                    human_click(self.driver, item)
                    return
        except NoSuchElementException:
            pass
        raise RuntimeError(f"Branch not found in visible list: {branch}")

    def _wait_for_loading_modal(self) -> None:
        wait_for_hidden(self.driver, ".modal-carga", timeout=10)
        human_delay(200, 500)

    def _dismiss_existing_session_prompt(self) -> None:
        selectors = ["button.cancel", ".cancel", "//*[text()='Si']", "//*[text()='Sí']"]

        for selector in selectors:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            try:
                elements = self.driver.find_elements(by, selector)
                if elements and elements[0].is_displayed():
                    human_click(self.driver, elements[0])
                    self._wait_for_loading_modal()
                    return
            except Exception:
                continue

    def _go_back_to_branches_if_possible(self) -> None:
        selectors = [
            "#botonAtrasCitas",
            "#botonAtras",
            "//*[text()='Atrás']",
            "//*[text()='Regresar']",
        ]

        for selector in selectors:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            try:
                elements = self.driver.find_elements(by, selector)
                if elements and elements[0].is_displayed():
                    human_click(self.driver, elements[0])
                    self._wait_for_loading_modal()
                    return
            except Exception:
                continue

        self.prepare_practical_test_flow()

    def _stop_if_human_verification_visible(self) -> None:
        try:
            body = wait_and_find(self.driver, "body", timeout=5).text.lower()
            triggers = ["captcha", "no soy un robot", "access denied", "acceso denegado"]
            if any(trigger in body for trigger in triggers):
                raise HumanInterventionRequired(
                    "The portal is asking for human verification or denied access. Run headed and resolve manually."
                )
        except TimeoutException:
            pass


CoseviPlaywrightClient = CoseviBrowserClient
