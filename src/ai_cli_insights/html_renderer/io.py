from __future__ import annotations

import json
from pathlib import Path

from ..models import ReportMeta


def run_self_check(html_text: str) -> list[str]:
    required = [
        "At a Glance",
        "Report Quality Score",
        "Snapshot Compare",
        "Key Trends",
        "Platform Recommendations",
        "What You Work On",
        "Where Things Go Wrong",
        "Project Drill-Down",
        "High-Value Session Leaderboards",
        "Prompt Library",
        "Task Type Recommendation Matrix",
        "Existing Features to Try",
        "New Ways to Use These Tools",
        "On the Horizon",
        "copyText(",
        "Copy All Feature Prompts",
        "Copy All Pattern Prompts",
    ]
    if "How You Use These Tools" not in html_text and "How You Use Claude Code" not in html_text and "How You Use Codex CLI" not in html_text:
        required.append("How You Use")
    return [item for item in required if item not in html_text]


def write_report(output_dir: Path, report_date: str, html_text: str, meta: ReportMeta) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"{meta.file_slug}-{report_date}.html"
    html_path.write_text(html_text, encoding="utf-8")
    return html_path


def load_previous_snapshot(output_dir: Path, meta: ReportMeta) -> dict | None:
    snapshot_dir = output_dir / ".snapshots"
    if not snapshot_dir.exists():
        return None
    candidates = sorted(snapshot_dir.glob(f"{meta.file_slug}-*.json"))
    if not candidates:
        return None
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def write_snapshot(output_dir: Path, meta: ReportMeta, generated_at: str, payload: dict) -> Path:
    snapshot_dir = output_dir / ".snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = generated_at.replace(":", "-")
    snapshot_path = snapshot_dir / f"{meta.file_slug}-{safe_ts}.json"
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot_path
