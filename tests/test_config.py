"""Tests for chat_harness.config."""

from pathlib import Path

import pytest
import yaml

from chat_harness.config import Config, load_config


def test_load_config_defaults(tmp_path):
    cfg = load_config(tmp_path / "nonexistent.yaml")
    assert cfg.model == "qwen2.5:14b-instruct-q4_K_M"
    assert cfg.ollama_url == "http://localhost:11434"
    assert cfg.vault_path == Path.home() / "Documents" / "ObsidianVault"


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "vault_path": "/tmp/vault",
        "model": "llama3:8b",
        "ollama_url": "http://127.0.0.1:11434",
        "log_dir": "/tmp/logs",
        "skills": {"qwen_skip": ["search"], "qwen_degraded": []},
    }))
    cfg = load_config(config_file)
    assert cfg.model == "llama3:8b"
    assert cfg.vault_path == Path("/tmp/vault")
    assert cfg.ollama_url == "http://127.0.0.1:11434"
    assert cfg.log_dir == Path("/tmp/logs")
    assert cfg.skills["qwen_skip"] == ["search"]


def test_config_get_fallback(tmp_path):
    cfg = Config({}, tmp_path / "config.yaml")
    assert cfg.get("missing_key", "fallback") == "fallback"
