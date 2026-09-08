import re
import ssl
import subprocess
from pathlib import Path

import undetected_chromedriver as uc  # type: ignore[import-untyped]

# This bypasses the unverified context issue sometimes found with
# `undetected_chromedriver` downloads on Linux.
ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[assignment]


def build_chrome_options(
    profile_dir: Path, executable_path: Path | None = None, headless: bool = True
) -> uc.ChromeOptions:
    expanded_profile_dir = profile_dir.expanduser()
    expanded_profile_dir.mkdir(parents=True, exist_ok=True)
    options = uc.ChromeOptions()

    if executable_path:
        options.binary_location = str(executable_path.expanduser())

    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--user-data-dir={expanded_profile_dir}")
    options.add_argument("--lang=es-CR")
    options.add_argument("--window-size=1366,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-sandbox")
    options.add_argument("--no-service-autorun")
    options.add_argument("--password-store=basic")
    options.add_argument("--start-maximized")

    return options


def _parse_chrome_major_version(output: str) -> int | None:
    match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
    if match:
        return int(match.group(1))
    return None


def _detect_windows_chrome_version(executable_path: Path) -> int | None:
    windows_path = str(executable_path)
    if windows_path.startswith("/mnt/") and len(windows_path) > 6:
        windows_tail = windows_path[7:].replace("/", "\\")
        windows_path = f"{windows_path[5].upper()}:\\{windows_tail}"
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"(Get-Item '{windows_path}').VersionInfo.ProductVersion",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return _parse_chrome_major_version(result.stdout + result.stderr)


def detect_chrome_major_version(executable_path: Path | None = None) -> int | None:
    candidates = []
    if executable_path:
        candidates.append(str(executable_path.expanduser()))
    candidates.extend(["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"])

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        version = _parse_chrome_major_version(result.stdout + result.stderr)
        if version:
            return version

    if executable_path:
        return _detect_windows_chrome_version(executable_path.expanduser())
    return None


def get_browser(
    profile_dir: Path, executable_path: Path | None = None, headless: bool = True
) -> uc.Chrome:
    options = build_chrome_options(profile_dir, executable_path, headless)
    chrome_major_version = detect_chrome_major_version(executable_path)
    return uc.Chrome(
        options=options,
        headless=headless,
        enable_cdp_events=True,
        use_subprocess=True,
        version_main=chrome_major_version,
    )
