# musiccli/config.py
"""Configuration management for MusicCLI."""

from pathlib import Path
import sys

# tomllib is Python 3.11+, use tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

CONFIG_DIR = Path.home() / ".config" / "musiccli"
CONFIG_PATH = CONFIG_DIR / "config.toml"


def load_config() -> dict:
    """Load configuration from config file."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save configuration to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "wb") as f:
        tomli_w.dump(config, f)


def get_config_value(key: str, default=None):
    """Get a specific config value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value) -> None:
    """Set a specific config value."""
    config = load_config()
    config[key] = value
    save_config(config)
