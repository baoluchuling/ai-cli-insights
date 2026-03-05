"""Install Claude Code skill file for multi-insights."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _get_skill_template() -> str:
    if sys.version_info >= (3, 11):
        from importlib.resources import files
        return files("ai_cli_insights").joinpath("data/skill_template.md").read_text(encoding="utf-8")
    else:
        from importlib import resources
        return resources.read_text("ai_cli_insights.data", "skill_template.md", encoding="utf-8")


def install_skill() -> None:
    # Determine the command name
    command = shutil.which("ai-cli-insights")
    if command:
        command_str = "ai-cli-insights"
    else:
        command_str = f"{sys.executable} -m ai_cli_insights"

    template = _get_skill_template()
    content = template.replace("{command}", command_str)

    skill_dir = Path.home() / ".claude" / "skills" / "multi-insights"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"

    skill_path.write_text(content, encoding="utf-8")
    print(f"Skill installed to {skill_path}")
    print(f"Command: {command_str}")
