from types import SimpleNamespace

from quick_cita_cr.browser.solver import CloudflareSolver


class FakeDriver:
    def __init__(self, page_source: str = "") -> None:
        self.page_source = page_source


class FakeBypasser:
    def __init__(self) -> None:
        self.driver = None
        self.wait = None
        self.config = SimpleNamespace(
            timeout=30,
            simulate_human=True,
            enable_fingerprint_spoofing=True,
            retry_delay=1,
            debug=False,
        )
        self.behavior_sim = None
        self.fingerprinting = None
        self.called = False

    def _detect_and_bypass_cloudflare(self, max_wait: int) -> bool:
        self.called = True
        assert 1 <= max_wait <= 7
        return True


def test_solver_uses_existing_driver_with_cloudflare_bypass_core() -> None:
    driver = FakeDriver("Just a moment")
    bypasser = FakeBypasser()

    solver = CloudflareSolver(driver, bypasser=bypasser)

    assert solver.solve(timeout=7) is True
    assert bypasser.driver is driver
    assert bypasser.called is True


def test_solver_skips_bypass_when_no_challenge_is_present() -> None:
    bypasser = FakeBypasser()
    solver = CloudflareSolver(FakeDriver("Portal normal"), bypasser=bypasser)

    assert solver.solve(timeout=7) is True
    assert bypasser.called is False
