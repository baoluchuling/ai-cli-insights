"""
Multi-CLI Insights Collector
Unified data collector for Claude Code and Codex CLI session data.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ── Path configuration ──────────────────────────────────────

CLAUDE_SESSION_META = Path.home() / ".claude" / "usage-data" / "session-meta"
CLAUDE_FACETS = Path.home() / ".claude" / "usage-data" / "facets"
CODEX_SESSIONS = Path.home() / ".codex" / "sessions"
CODEX_HISTORY = Path.home() / ".codex" / "history.jsonl"
CODEX_SQLITE = Path.home() / ".codex" / "state_5.sqlite"


# ── Claude Code data collection ─────────────────────────────

def collect_claude_sessions(days: int) -> list[dict]:
    sessions = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    if not CLAUDE_SESSION_META.exists():
        return sessions

    for meta_file in CLAUDE_SESSION_META.glob("*.json"):
        try:
            meta = json.loads(meta_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        start_time = meta.get("start_time", "")
        if not start_time:
            continue

        try:
            ts = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except ValueError:
            continue

        if ts < cutoff:
            continue

        session_id = meta.get("session_id", meta_file.stem)

        facet = {}
        facet_file = CLAUDE_FACETS / f"{session_id}.json"
        if facet_file.exists():
            try:
                facet = json.loads(facet_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        sessions.append({
            "source": "claude_code",
            "session_id": session_id,
            "start_time": start_time,
            "duration_minutes": meta.get("duration_minutes", 0),
            "project_path": meta.get("project_path", ""),
            "user_messages": meta.get("user_message_count", 0),
            "assistant_messages": meta.get("assistant_message_count", 0),
            "tool_counts": meta.get("tool_counts", {}),
            "languages": meta.get("languages", {}),
            "git_commits": meta.get("git_commits", 0),
            "input_tokens": meta.get("input_tokens", 0),
            "output_tokens": meta.get("output_tokens", 0),
            "lines_added": meta.get("lines_added", 0),
            "lines_removed": meta.get("lines_removed", 0),
            "files_modified": meta.get("files_modified", 0),
            "user_interruptions": meta.get("user_interruptions", 0),
            "tool_errors": meta.get("tool_errors", 0),
            "first_prompt": meta.get("first_prompt", "")[:200],
            "uses_task_agent": meta.get("uses_task_agent", False),
            "goal": facet.get("underlying_goal", ""),
            "goal_categories": facet.get("goal_categories", {}),
            "outcome": facet.get("outcome", ""),
            "satisfaction": facet.get("claude_helpfulness", ""),
            "friction_counts": facet.get("friction_counts", {}),
            "friction_detail": facet.get("friction_detail", ""),
            "primary_success": facet.get("primary_success", ""),
            "summary": facet.get("brief_summary", ""),
        })

    return sorted(sessions, key=lambda s: s["start_time"])


# ── Codex CLI data collection ────────────────────────────────

def _parse_codex_jsonl_timestamps(session_id: str) -> list[datetime]:
    timestamps = []
    if not CODEX_SESSIONS.exists():
        return timestamps
    for jsonl_file in CODEX_SESSIONS.rglob("*.jsonl"):
        if session_id not in jsonl_file.name:
            continue
        try:
            for line in open(jsonl_file):
                try:
                    event = json.loads(line)
                    ts = event.get("timestamp", "")
                    if ts:
                        timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except (json.JSONDecodeError, ValueError):
                    continue
        except OSError:
            pass
    return timestamps


def _calc_codex_durations(timestamps: list[datetime], active_cap_minutes: int = 5) -> tuple[int, int]:
    if len(timestamps) < 2:
        return 0, 0
    span = int((timestamps[-1] - timestamps[0]).total_seconds() / 60)
    active_seconds = 0
    cap = timedelta(minutes=active_cap_minutes)
    for i in range(1, len(timestamps)):
        gap = timestamps[i] - timestamps[i - 1]
        active_seconds += min(gap, cap).total_seconds()
    active = int(active_seconds / 60)
    return span, active


def _collect_codex_from_sqlite(days: int) -> list[dict]:
    sessions = []
    if not CODEX_SQLITE.exists():
        return sessions

    try:
        conn = sqlite3.connect(str(CODEX_SQLITE))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, created_at, updated_at, source, model_provider, cwd,
                   title, tokens_used, cli_version, first_user_message,
                   has_user_event, sandbox_policy, approval_mode,
                   git_branch, git_origin_url
            FROM threads
            ORDER BY created_at DESC
        """)

        for row in cursor.fetchall():
            row = dict(row)
            created_ms = row["created_at"]

            try:
                created_dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
                if created_dt.year < 2024 or created_dt.year > 2030:
                    created_dt = None
            except (OSError, ValueError, OverflowError):
                created_dt = None

            if created_dt is None:
                created_dt = _get_codex_session_time_from_jsonl(row["id"])

            if created_dt is None:
                continue

            start_time = created_dt.isoformat()

            jsonl_timestamps = _parse_codex_jsonl_timestamps(row["id"])
            span_minutes, active_minutes = _calc_codex_durations(jsonl_timestamps)

            if jsonl_timestamps:
                start_time = jsonl_timestamps[0].isoformat()
                created_dt = jsonl_timestamps[0]

            cursor2 = conn.cursor()
            cursor2.execute("SELECT count(*) FROM logs WHERE thread_id = ?", (row["id"],))
            log_count = cursor2.fetchone()[0]

            user_msg_count = _count_codex_user_messages(row["id"])
            tool_counts, total_events = _collect_codex_jsonl_tools(row["id"])

            sessions.append({
                "source": "codex_cli",
                "session_id": row["id"],
                "start_time": start_time,
                "duration_minutes": span_minutes,
                "active_minutes": active_minutes,
                "project_path": row["cwd"],
                "model": row["model_provider"],
                "cli_version": row.get("cli_version", ""),
                "title": row["title"][:200],
                "first_prompt": (row.get("first_user_message") or row["title"] or "")[:200],
                "tokens_used": row["tokens_used"],
                "user_messages": user_msg_count,
                "has_user_event": bool(row["has_user_event"]),
                "tool_counts": tool_counts,
                "total_events": total_events,
                "log_entries": log_count,
                "git_branch": row.get("git_branch", ""),
                "approval_mode": row.get("approval_mode", ""),
            })

        conn.close()
    except sqlite3.Error:
        pass

    return sorted(sessions, key=lambda s: s["start_time"])


def _get_codex_session_time_from_jsonl(session_id: str) -> datetime | None:
    if not CODEX_SESSIONS.exists():
        return None
    for jsonl_file in CODEX_SESSIONS.rglob("*.jsonl"):
        if session_id in jsonl_file.name:
            name = jsonl_file.stem
            try:
                date_part = name.replace("rollout-", "").split("-" + session_id[:8])[0]
                date_part = date_part[:10] + "T" + date_part[11:].replace("-", ":")
                return datetime.fromisoformat(date_part + "+00:00")
            except (ValueError, IndexError):
                try:
                    first_line = jsonl_file.open().readline()
                    event = json.loads(first_line)
                    ts = event.get("timestamp", "")
                    if ts:
                        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except (json.JSONDecodeError, OSError):
                    pass
    return None


def _count_codex_user_messages(session_id: str) -> int:
    count = 0
    if not CODEX_HISTORY.exists():
        return count
    try:
        with open(CODEX_HISTORY) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("session_id") == session_id:
                        count += 1
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return count


def _collect_codex_jsonl_tools(session_id: str) -> tuple[dict, int]:
    tool_counter: Counter = Counter()
    total_events = 0

    if not CODEX_SESSIONS.exists():
        return {}, 0

    for jsonl_file in CODEX_SESSIONS.rglob("*.jsonl"):
        if session_id not in jsonl_file.name:
            continue
        try:
            lines = jsonl_file.read_text().strip().split("\n")
        except OSError:
            continue
        for line in lines:
            try:
                event = json.loads(line)
                total_events += 1
                etype = event.get("type", "")
                payload = event.get("payload", {})
                payload_type = payload.get("type", "")
                if etype in ("tool_call", "function_call"):
                    name = payload.get("name", payload.get("function", "unknown"))
                    tool_counter[name] += 1
                elif etype == "response_item" and payload_type in (
                    "function_call", "custom_tool_call", "web_search_call"
                ):
                    name = payload.get("name", payload_type)
                    tool_counter[name] += 1
                elif etype == "exec":
                    tool_counter["shell_exec"] += 1
            except json.JSONDecodeError:
                continue

    return dict(tool_counter), total_events


def _parse_time(ts_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _collect_codex_from_jsonl(days: int) -> list[dict]:
    sessions = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    if not CODEX_SESSIONS.exists():
        return sessions

    for jsonl_file in CODEX_SESSIONS.rglob("*.jsonl"):
        try:
            lines = jsonl_file.read_text().strip().split("\n")
        except OSError:
            continue
        if not lines:
            continue
        events = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if not events:
            continue

        meta_events = [e for e in events if e.get("type") == "session_meta"]
        meta = meta_events[0].get("payload", {}) if meta_events else {}

        ts_str = meta.get("timestamp", events[0].get("timestamp", ""))
        if not ts_str:
            continue
        ts = _parse_time(ts_str)
        if not ts or ts < cutoff:
            continue

        user_msgs = [e for e in events if e.get("type") == "message" and
                     e.get("payload", {}).get("role") == "user"]
        assistant_msgs = [e for e in events if e.get("type") == "message" and
                          e.get("payload", {}).get("role") == "assistant"]

        tool_counter: Counter = Counter()
        for e in events:
            etype = e.get("type", "")
            if etype in ("tool_call", "function_call"):
                name = e.get("payload", {}).get("name",
                       e.get("payload", {}).get("function", "unknown"))
                tool_counter[name] += 1
            elif etype == "exec":
                tool_counter["shell_exec"] += 1

        timestamps = []
        for e in events:
            t = _parse_time(e.get("timestamp", ""))
            if t:
                timestamps.append(t)

        duration_minutes = 0
        if len(timestamps) >= 2:
            duration_minutes = int((max(timestamps) - min(timestamps)).total_seconds() / 60)

        first_prompt = ""
        if user_msgs:
            content = user_msgs[0].get("payload", {}).get("content", "")
            if isinstance(content, list):
                text_parts = [p.get("text", "") for p in content if isinstance(p, dict)]
                first_prompt = " ".join(text_parts)[:200]
            elif isinstance(content, str):
                first_prompt = content[:200]

        sessions.append({
            "source": "codex_cli",
            "session_id": meta.get("id", jsonl_file.stem),
            "start_time": ts_str,
            "duration_minutes": duration_minutes,
            "project_path": meta.get("cwd", ""),
            "model": meta.get("model_provider", "openai"),
            "cli_version": meta.get("cli_version", ""),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "tool_counts": dict(tool_counter),
            "total_events": len(events),
            "first_prompt": first_prompt,
        })

    return sorted(sessions, key=lambda s: s["start_time"])


def collect_codex_sessions(days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    sessions = _collect_codex_from_sqlite(days)

    if sessions:
        sessions = [s for s in sessions
                    if _parse_time(s["start_time"]) and _parse_time(s["start_time"]) >= cutoff]
        sqlite_ids = {s["session_id"] for s in sessions}
        jsonl_sessions = _collect_codex_from_jsonl(days)
        for js in jsonl_sessions:
            if js["session_id"] not in sqlite_ids:
                sessions.append(js)
        return sorted(sessions, key=lambda s: s.get("start_time", ""))

    return _collect_codex_from_jsonl(days)


# ── Aggregate statistics ─────────────────────────────────────

def aggregate_stats(sessions: list[dict]) -> dict:
    if not sessions:
        return {"total_sessions": 0}

    by_source: dict[str, list] = defaultdict(list)
    for s in sessions:
        by_source[s["source"]].append(s)

    stats: dict = {
        "period": {
            "from": sessions[0]["start_time"][:10],
            "to": sessions[-1]["start_time"][:10],
        },
        "total_sessions": len(sessions),
    }

    for source, source_sessions in by_source.items():
        tool_totals: Counter = Counter()
        total_user_msgs = 0
        total_duration = 0
        total_active = 0
        total_tokens = 0
        total_events = 0
        projects: set = set()
        outcomes: Counter = Counter()
        frictions: Counter = Counter()

        for s in source_sessions:
            for tool, count in s.get("tool_counts", {}).items():
                tool_totals[tool] += count
            total_user_msgs += s.get("user_messages", 0)
            total_duration += s.get("duration_minutes", 0)
            total_active += s.get("active_minutes", 0)
            total_events += s.get("total_events", 0)
            total_tokens += s.get("tokens_used", 0) or (s.get("input_tokens", 0) + s.get("output_tokens", 0))
            if s.get("project_path"):
                projects.add(s["project_path"])
            if s.get("outcome"):
                outcomes[s["outcome"]] += 1
            for friction, count in s.get("friction_counts", {}).items():
                frictions[friction] += count

        total_tool_calls = sum(tool_totals.values())

        source_stats: dict = {
            "sessions": len(source_sessions),
            "total_user_messages": total_user_msgs,
            "total_events": total_events,
            "total_tool_calls": total_tool_calls,
            "span_hours": round(total_duration / 60, 1),
            "active_hours": round(total_active / 60, 1),
            "avg_duration_minutes": round(total_duration / len(source_sessions), 1) if source_sessions else 0,
            "total_tokens": total_tokens,
            "avg_tokens_per_session": round(total_tokens / len(source_sessions)) if source_sessions else 0,
            "top_tools": dict(tool_totals.most_common(10)),
            "projects": sorted(projects),
        }

        if outcomes:
            source_stats["outcomes"] = dict(outcomes)
        if frictions:
            source_stats["friction_counts"] = dict(frictions)

        stats[source] = source_stats

    return stats


# ── Public API ────────────────────────────────────────────────

def collect(days: int, tool: str) -> dict:
    """Collect session data and return structured dict (replaces subprocess call)."""
    sessions: list[dict] = []
    if tool in ("all", "claude"):
        sessions.extend(collect_claude_sessions(days))
    if tool in ("all", "codex"):
        sessions.extend(collect_codex_sessions(days))
    sessions.sort(key=lambda s: s.get("start_time", ""))
    stats = aggregate_stats(sessions)
    return {"stats": stats, "sessions": sessions}
