from pathlib import Path

from quick_cita_cr.browser.driver import (
    _parse_chrome_major_version,
    build_chrome_options,
    detect_chrome_major_version,
)


def test_build_chrome_options_uses_persistent_profile_and_antidetection_flags(tmp_path) -> None:
    profile_dir = tmp_path / "profile"

    options = build_chrome_options(profile_dir, headless=False)
    arguments = options.arguments

    assert f"--user-data-dir={profile_dir.expanduser()}" in arguments
    assert "--disable-blink-features=AutomationControlled" in arguments
    assert "--lang=es-CR" in arguments
    assert "--window-size=1366,900" in arguments
    assert profile_dir.exists()


def test_build_chrome_options_adds_executable_path_when_configured(tmp_path) -> None:
    chrome_path = Path("/opt/google/chrome/chrome")

    options = build_chrome_options(tmp_path / "profile", executable_path=chrome_path, headless=True)

    assert options.binary_location == str(chrome_path)
    assert "--headless=new" in options.arguments


def test_detect_chrome_major_version_reads_configured_binary(tmp_path) -> None:
    fake_chrome = tmp_path / "chrome"
    fake_chrome.write_text("#!/bin/sh\necho 'Google Chrome 152.0.7977.82'\n", encoding="utf-8")
    fake_chrome.chmod(0o755)

    assert detect_chrome_major_version(fake_chrome) == 152


def test_parse_chrome_major_version() -> None:
    assert _parse_chrome_major_version("Google Chrome 152.0.7977.83") == 152
    assert _parse_chrome_major_version("Opening in existing browser session.") is None
