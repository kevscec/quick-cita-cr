import yaml

from quick_cita_cr.cli import _write_demo_config


def test_write_demo_config_forces_visible_browser_and_local_chrome_when_available(tmp_path) -> None:
    source_config = tmp_path / "config.yaml"
    chrome = tmp_path / "chrome-for-testing" / "chrome-linux64" / "chrome"
    chrome.parent.mkdir(parents=True)
    chrome.write_text("", encoding="utf-8")
    chrome.chmod(0o755)

    source_config.write_text(
        yaml.safe_dump(
            {
                "browser": {
                    "headless": True,
                    "executable_path": None,
                    "profile_dir": "~/.local/share/quick-cita-cr/browser-profile",
                }
            }
        ),
        encoding="utf-8",
    )

    demo_config = _write_demo_config(source_config, tmp_path / "demo.yaml", chrome)
    data = yaml.safe_load(demo_config.read_text(encoding="utf-8"))

    assert data["browser"]["headless"] is False
    assert data["browser"]["executable_path"] == str(chrome)
    assert data["browser"]["profile_dir"] == "~/.local/share/quick-cita-cr/browser-profile"


def test_write_demo_config_preserves_configured_executable_path(tmp_path) -> None:
    source_config = tmp_path / "config.yaml"
    source_config.write_text(
        yaml.safe_dump({"browser": {"headless": True, "executable_path": "/custom/chrome"}}),
        encoding="utf-8",
    )

    demo_config = _write_demo_config(
        source_config, tmp_path / "demo.yaml", tmp_path / "local-chrome"
    )
    data = yaml.safe_load(demo_config.read_text(encoding="utf-8"))

    assert data["browser"]["headless"] is False
    assert data["browser"]["executable_path"] == "/custom/chrome"
