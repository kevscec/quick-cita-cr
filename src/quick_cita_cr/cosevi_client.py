from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .config import AppConfig, Secrets
from .models import BranchSnapshot
from .parser import parse_appointment_dates

LOGIN_URL = "https://servicios.educacionvial.go.cr/Formularios/IngresarCuenta"
PRACTICAL_TEST_URL = "https://servicios.educacionvial.go.cr/Formularios/MatriculaPruebaPractica"
PORTAL_URL = "https://servicios.educacionvial.go.cr/Formularios/Servicios"


class HumanInterventionRequired(RuntimeError):
    pass


class CoseviPlaywrightClient:
    def __init__(self, config: AppConfig, secrets: Secrets, headed: bool | None = None):
        self.config = config
        self.secrets = secrets
        self.headless = config.browser.headless if headed is None else not headed

    def __enter__(self) -> CoseviPlaywrightClient:
        self._playwright = sync_playwright().start()
        profile_dir = self.config.browser.profile_dir.expanduser()
        profile_dir.mkdir(parents=True, exist_ok=True)
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=self.headless,
            locale="es-CR",
            timezone_id="America/Costa_Rica",
        )
        self._context.set_default_timeout(self.config.browser.timeout_seconds * 1000)
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._context.close()
        self._playwright.stop()

    @property
    def page(self) -> Page:
        return self._page

    def ensure_logged_in(self) -> None:
        self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        if self._looks_logged_in():
            return
        self._stop_if_human_verification_visible()
        self._select_by_value_or_label("select.selector-tipos-identificacion", self.secrets.id_type)
        self.page.locator("#identificacion").fill(self.secrets.identification.get_secret_value())
        self.page.locator("#contrasena").fill(self.secrets.password.get_secret_value())
        self.page.locator("#botonAcceder").click()
        self._wait_for_loading_modal()
        self._dismiss_existing_session_prompt()
        self._stop_if_human_verification_visible()
        if not self._looks_logged_in():
            raise RuntimeError("Login did not reach an authenticated page; run with --headed to inspect.")

    def prepare_practical_test_flow(self) -> None:
        self.ensure_logged_in()
        self.page.goto(PRACTICAL_TEST_URL, wait_until="domcontentloaded")
        self._stop_if_human_verification_visible()
        self.page.locator("#numRecibo").fill(self.secrets.receipt_number.get_secret_value())
        self._select_by_value_or_label("select.selector-licencia", self.config.appointment.license_class)
        checkbox = self.page.locator("#check-AceptaTerminos")
        if not checkbox.is_checked():
            checkbox.check()
        self.page.locator("#botonContinuar").click()
        self._wait_for_loading_modal()

    def check_branch(self, branch: str) -> BranchSnapshot:
        if not self._branch_list_visible():
            self.prepare_practical_test_flow()
        self._select_branch(branch)
        self.page.locator("#botonContinuarSedes").click()
        self._wait_for_loading_modal()
        self._stop_if_human_verification_visible()
        text = self.page.locator("body").inner_text()
        slots = parse_appointment_dates(text, branch=branch)
        self._go_back_to_branches_if_possible()
        return BranchSnapshot(branch=branch, checked_at=datetime.now(UTC), slots=slots)

    def _looks_logged_in(self) -> bool:
        return self.page.locator("a.encabezado-boton-salir, text=Salir").count() > 0

    def _branch_list_visible(self) -> bool:
        try:
            return self.page.locator("#listaSedes").count() > 0
        except PlaywrightTimeoutError:
            return False

    def _select_branch(self, branch: str) -> None:
        items = self.page.locator("#listaSedes li")
        count = items.count()
        for index in range(count):
            item = items.nth(index)
            if branch.lower() in item.inner_text().lower():
                item.click()
                return
        raise RuntimeError(f"Branch not found in visible list: {branch}")

    def _select_by_value_or_label(self, selector: str, value: str) -> None:
        locator = self.page.locator(selector)
        try:
            locator.select_option(value=value)
        except Exception:
            locator.select_option(label=value)

    def _wait_for_loading_modal(self) -> None:
        with suppress(PlaywrightTimeoutError):
            self.page.locator(".modal-carga").wait_for(state="hidden", timeout=10_000)

    def _dismiss_existing_session_prompt(self) -> None:
        for selector in ["button.cancel", ".cancel", "text=Si", "text=Sí"]:
            locator = self.page.locator(selector)
            if locator.count() > 0:
                try:
                    locator.first.click(timeout=1_000)
                    self._wait_for_loading_modal()
                    return
                except Exception:
                    continue

    def _go_back_to_branches_if_possible(self) -> None:
        for selector in ["#botonAtrasCitas", "#botonAtras", "text=Atrás", "text=Regresar"]:
            locator = self.page.locator(selector)
            if locator.count() > 0:
                try:
                    locator.first.click(timeout=2_000)
                    self._wait_for_loading_modal()
                    return
                except Exception:
                    continue
        self.prepare_practical_test_flow()

    def _stop_if_human_verification_visible(self) -> None:
        body = self.page.locator("body").inner_text(timeout=5_000).lower()
        triggers = ["captcha", "no soy un robot", "verificación", "verificacion", "acceso denegado"]
        if any(trigger in body for trigger in triggers):
            raise HumanInterventionRequired(
                "The portal is asking for human verification or denied access. Run headed and resolve manually."
            )
