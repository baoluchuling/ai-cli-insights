from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

from .models import ReportMeta

_APP_NAME = "ai-cli-insights"

# ── XDG / platform paths ───────────────────────────────────


def config_dir() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / _APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / _APP_NAME


def data_dir() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / _APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / _APP_NAME


def output_dir() -> Path:
    return data_dir() / "reports"


# ── Lazy config loading ───────────────────────────────────

import os

_config: dict | None = None


def _load_default_config() -> dict:
    if sys.version_info >= (3, 11):
        from importlib.resources import files
        data_text = files("ai_cli_insights").joinpath("data/default_config.json").read_text(encoding="utf-8")
    else:
        from importlib import resources
        data_text = resources.read_text("ai_cli_insights.data", "default_config.json", encoding="utf-8")
    return json.loads(data_text)


def _get_config() -> dict:
    global _config
    if _config is not None:
        return _config

    default = _load_default_config()
    user_config_path = config_dir() / "config.json"
    if user_config_path.exists():
        try:
            user = json.loads(user_config_path.read_text(encoding="utf-8"))
            # User config overrides default; merge top-level keys
            for key in user:
                default[key] = user[key]
        except (json.JSONDecodeError, OSError):
            pass
    _config = default
    return _config


def get_domain_patterns() -> dict[str, list[str]]:
    return {k: v for k, v in _get_config().get("domain_patterns", {}).items()}


def get_domain_priority() -> list[str]:
    return _get_config().get("domain_priority", [])


def get_project_patterns() -> list[tuple[str, list[str]]]:
    return [(item["name"], item["patterns"]) for item in _get_config().get("project_patterns", [])]


def make_report_meta(tool: str, analyst_label: str = "GPT (Codex CLI)") -> ReportMeta:
    cfg = _get_config()["template_modes"][tool]
    primary_source = None
    file_slug = cfg["file_slug"]
    if tool == "claude":
        primary_source = "claude_code"
    elif tool == "codex":
        primary_source = "codex_cli"
    elif tool == "all":
        file_slug = "multi-insights-claude" if analyst_label == "Claude" else "multi-insights-codex"
    return ReportMeta(
        tool=tool,
        title=cfg["title"],
        subtitle_prefix=cfg["subtitle_prefix"],
        file_slug=file_slug,
        compare_sources=cfg["compare_sources"],
        primary_source=primary_source,
        analyst_label=analyst_label,
    )
