"""Load and expose chat-harness configuration from config.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _resolve_path(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


class Config:
    def __init__(self, data: dict[str, Any], config_path: Path) -> None:
        self._data = data
        self.config_path = config_path

    @property
    def vault_path(self) -> Path:
        return _resolve_path(self._data.get("vault_path", "~/Documents/ObsidianVault"))

    @property
    def model(self) -> str:
        return self._data.get("model", "qwen2.5:14b-instruct-q4_K_M")

    @property
    def ollama_url(self) -> str:
        return self._data.get("ollama_url", "http://localhost:11434")

    @property
    def log_dir(self) -> Path:
        return _resolve_path(self._data.get("log_dir", "~/.chat-harness/logs"))

    @property
    def skills(self) -> dict[str, Any]:
        return self._data.get("skills", {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


def load_config(path: Path | None = None) -> Config:
    """Load config.yaml from *path* (or the repo-root default)."""
    target = Path(path) if path else _DEFAULT_CONFIG_PATH
    if not target.exists():
        return Config({}, target)
    with target.open() as fh:
        data = yaml.safe_load(fh) or {}
    return Config(data, target)
