from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from .collector import collect
from .config import get_domain_patterns, get_domain_priority, get_project_patterns
from .models import AnalyzedData, PeriodComparison


def run_collect(days: int, tool: str) -> dict:
    return collect(days, tool)


def parse_session_dt(session: dict) -> datetime | None:
    ts = session.get("start_time") or ""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def subset_raw_by_window(raw: dict, start_dt: datetime, end_dt: datetime) -> dict:
    kept = []
    for session in raw.get("sessions", []):
        dt = parse_session_dt(session)
        if dt is None:
            continue
        if start_dt <= dt < end_dt:
            kept.append(session)
    return {
        "stats": {
            "period": {
                "from": start_dt.date().isoformat(),
                "to": (end_dt - timedelta(days=1)).date().isoformat(),
            }
        },
        "sessions": kept,
    }


def subset_raw_by_source(raw: dict, source: str) -> dict:
    return {
        "stats": raw.get("stats", {}),
        "sessions": [session for session in raw.get("sessions", []) if session.get("source") == source],
    }


def normalize_text(session: dict) -> str:
    parts = [
        session.get("first_prompt") or "",
        session.get("title") or "",
        session.get("goal") or "",
        session.get("summary") or "",
        session.get("project_path") or "",
    ]
    return " ".join(parts).lower()


def infer_domain(session: dict) -> str:
    text = normalize_text(session)
    domain_patterns = get_domain_patterns()
    domain_priority = get_domain_priority()
    scores = []
    for domain, patterns in domain_patterns.items():
        score = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        if score:
            scores.append((score, domain))
    if scores:
        scores.sort(key=lambda item: (-item[0], domain_priority.index(item[1]) if item[1] in domain_priority else 999))
        return scores[0][1]
    project_path = session.get("project_path") or ""
    if "worklog-app" in project_path or "agent-visualizer" in project_path:
        return "工具开发与可视化"
    if "/projects/" in project_path or "/components/" in project_path:
        return "Flutter 多仓开发与组件化"
    return "工作流与记忆系统"


def infer_project(session: dict) -> str:
    text = normalize_text(session)
    project_path = session.get("project_path") or ""
    project_patterns = get_project_patterns()
    for name, _patterns in project_patterns:
        if name in project_path:
            return name
    for name, patterns in project_patterns:
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            return name
    match = re.search(r"/projects/([^/]+)", project_path)
    if match:
        return match.group(1)
    match = re.search(r"/components/[^/]+/([^/]+)", project_path)
    if match:
        return match.group(1)
    home = str(Path.home())
    if project_path in {home, home + "/ai"}:
        return "workspace-root"
    return project_path or "unknown"


def top_n(counter: Counter, n: int) -> list[tuple[str, int]]:
    return counter.most_common(n)


def analyze(raw: dict) -> AnalyzedData:
    sessions = raw.get("sessions", [])
    per_source: dict[str, list] = defaultdict(list)
    for session in sessions:
        if session.get("source") in {"claude_code", "codex_cli"}:
            per_source[session["source"]].append(session)

    domains = {
        source: Counter(infer_domain(session) for session in source_sessions)
        for source, source_sessions in per_source.items()
    }
    projects = {
        source: Counter(infer_project(session) for session in source_sessions)
        for source, source_sessions in per_source.items()
    }

    comparison: dict = {}
    for source, source_sessions in per_source.items():
        tool_counter: Counter = Counter()
        for session in source_sessions:
            tool_counter.update(session.get("tool_counts") or {})
        total_duration = sum(session.get("duration_minutes", 0) for session in source_sessions)
        total_user_messages = sum(session.get("user_messages", 0) for session in source_sessions)
        comparison[source] = {
            "sessions": len(source_sessions),
            "avg_duration_min": round(total_duration / len(source_sessions), 1) if source_sessions else 0.0,
            "avg_user_messages": round(total_user_messages / len(source_sessions), 1) if source_sessions else 0.0,
            "total_duration_hours": round(total_duration / 60, 1),
            "top_tools": top_n(tool_counter, 5),
            "top_domains": top_n(domains[source], 6),
            "top_projects": top_n(projects[source], 6),
        }

    friction_counts: Counter = Counter()
    outcomes: Counter = Counter()
    friction_sessions: list[dict] = []
    for session in per_source.get("claude_code", []):
        fc = Counter(session.get("friction_counts") or {})
        friction_counts.update(fc)
        if session.get("outcome"):
            outcomes[session["outcome"]] += 1
        score = sum(fc.values())
        if score:
            friction_sessions.append(
                {
                    "score": score,
                    "start_time": session.get("start_time", ""),
                    "project": infer_project(session),
                    "domain": infer_domain(session),
                    "outcome": session.get("outcome", ""),
                    "first_prompt": (session.get("first_prompt") or "")[:120],
                    "friction_counts": dict(fc),
                    "friction_detail": session.get("friction_detail", ""),
                    "summary": session.get("summary", ""),
                }
            )
    friction_sessions.sort(key=lambda item: (-item["score"], item["start_time"]))

    efficient: list[tuple] = []
    for session in sessions:
        source = session.get("source")
        if source == "claude_code":
            if session.get("outcome") in {"fully_achieved", "mostly_achieved"} and session.get("duration_minutes", 0) <= 90:
                efficient.append((source, infer_domain(session), infer_project(session)))
        elif source == "codex_cli":
            active_minutes = session.get("active_minutes", 0)
            if active_minutes and active_minutes <= 120 and session.get("user_messages", 0) <= 25:
                efficient.append((source, infer_domain(session), infer_project(session)))

    success_patterns = {
        "count": len(efficient),
        "domains": Counter(item[1] for item in efficient),
        "projects": Counter(item[2] for item in efficient),
    }

    return AnalyzedData(
        raw=raw,
        sessions=sessions,
        comparison=comparison,
        domains=domains,
        projects=projects,
        friction_counts=friction_counts,
        outcomes=outcomes,
        friction_sessions=friction_sessions,
        success_patterns=success_patterns,
    )


def total_user_messages(raw: dict) -> int:
    stats = raw.get("stats", {})
    return (stats.get("claude_code", {}) or {}).get("total_user_messages", 0) + (
        (stats.get("codex_cli", {}) or {}).get("total_user_messages", 0)
    )


def source_label(source: str) -> str:
    if source == "claude_code":
        return "Claude Code"
    if source == "codex_cli":
        return "Codex CLI"
    return source


def infer_codex_archetypes(data: AnalyzedData) -> list[dict]:
    codex_sessions = [s for s in data.sessions if s.get("source") == "codex_cli"]
    if not codex_sessions:
        return []
    archetypes = []
    long_running = [s for s in codex_sessions if s.get("active_minutes", 0) >= 120]
    if long_running:
        archetypes.append(
            {
                "title": "长链路执行器",
                "summary": "这是一个明显偏持续施工的使用模式，而不是快速问答模式。",
                "detail": (
                    f"共有 {len(long_running)} 个 Codex session 的 active_minutes 超过 120 分钟。"
                    "这通常意味着你不是拿它做一次性回答，而是让它在明确目标下持续推进命令、补丁和验证。"
                ),
            }
        )
    patch_heavy = [s for s in codex_sessions if (s.get("tool_counts") or {}).get("apply_patch", 0) >= 20]
    if patch_heavy:
        archetypes.append(
            {
                "title": "多文件实施流",
                "summary": "Codex 更常被你拿来做真正的代码落地，而不是只读不改。",
                "detail": (
                    f"共有 {len(patch_heavy)} 个 Codex session 的 apply_patch 次数达到 20 次以上。"
                    "这说明它更多承担多文件改动、修复串联和结果沉淀，而不是仅做命令探查。"
                ),
            }
        )
    verification_heavy = [
        s
        for s in codex_sessions
        if (s.get("tool_counts") or {}).get("write_stdin", 0) >= 10
        or (s.get("tool_counts") or {}).get("exec_command", 0) >= 150
    ]
    if verification_heavy:
        archetypes.append(
            {
                "title": "验证驱动推进",
                "summary": "你经常让 Codex 一边执行，一边盯住运行中的进程和命令输出。",
                "detail": (
                    f"共有 {len(verification_heavy)} 个 Codex session 呈现出明显的命令轮询/过程跟踪特征。"
                    "这通常对应测试、分析、构建或长命令观察，而不是一次性执行完就结束。"
                ),
            }
        )
    return archetypes


def build_period_comparison(days: int, tool: str) -> PeriodComparison | None:
    raw_2x = run_collect(days * 2, tool)
    sessions = [s for s in raw_2x.get("sessions", []) if parse_session_dt(s) is not None]
    if not sessions:
        return None
    latest_dt = max(parse_session_dt(s) for s in sessions if parse_session_dt(s) is not None)
    current_end = latest_dt + timedelta(seconds=1)
    current_start = current_end - timedelta(days=days)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=days)

    current_raw = subset_raw_by_window(raw_2x, current_start, current_end)
    previous_raw = subset_raw_by_window(raw_2x, previous_start, previous_end)
    current_data = analyze(current_raw)
    previous_data = analyze(previous_raw)

    return PeriodComparison(
        current_label=f"{current_start.date().isoformat()} ~ {(current_end - timedelta(days=1)).date().isoformat()}",
        previous_label=f"{previous_start.date().isoformat()} ~ {(previous_end - timedelta(days=1)).date().isoformat()}",
        current=current_data.comparison,
        previous=previous_data.comparison,
    )


def delta_text(current: float, previous: float, unit: str = "") -> str:
    if previous == 0:
        return f"{current}{unit}（无上一周期基线）"
    delta = current - previous
    sign = "+" if delta >= 0 else ""
    return f"{current}{unit}（{sign}{round(delta, 1)}）"
