from __future__ import annotations

import json
from pathlib import Path

from ..models import ReportMeta


def run_self_check(html_text: str) -> list[str]:
    required = [
        "一眼概览",
        "报告质量评分",
        "快照对比",
        "关键趋势",
        "平台建议",
        "你主要在做什么",
        "问题主要出在哪",
        "项目下钻",
        "高价值会话榜单",
        "提示词库",
        "任务类型建议矩阵",
        "可直接尝试的功能",
        "这些工具的新用法",
        "后续规划",
        "copyText(",
        "复制全部功能提示词",
        "复制全部模式提示词",
    ]
    if "你如何使用这些工具" not in html_text and "你如何使用 Claude Code" not in html_text and "你如何使用 Codex CLI" not in html_text:
        required.append("你如何使用")
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
