from __future__ import annotations

from collections import Counter, defaultdict

from .analytics import infer_domain, infer_project, normalize_text, parse_session_dt, source_label
from .models import AnalyzedData, NarrativeBundle, ReportExtras, ReportMeta


def infer_task_type(session: dict) -> str:
    domain = infer_domain(session)
    text = normalize_text(session)
    if domain == "调试与构建故障":
        return "调试与构建"
    if domain == "测试与验证":
        return "测试验证"
    if domain == "Flutter 多仓开发与组件化":
        return "跨仓实现"
    if domain == "技术调研与问答" or "review" in text or "评审" in text:
        return "分析评审"
    if domain == "工作流与记忆系统":
        return "工作流设计"
    if session.get("source") == "codex_cli" and session.get("active_minutes", 0) >= 120:
        return "长链路执行"
    return "工具开发"


def _daily_buckets(data: AnalyzedData) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for session in data.sessions:
        dt = parse_session_dt(session)
        if dt is None:
            continue
        buckets[dt.date().isoformat()].append(session)
    return dict(sorted(buckets.items()))


def _aggregate_series(data: AnalyzedData, source: str | None, metric: str) -> list[dict]:
    rows = []
    for day, sessions in _daily_buckets(data).items():
        filtered = [s for s in sessions if source is None or s.get("source") == source]
        if not filtered:
            continue
        if metric == "sessions":
            value = len(filtered)
        elif metric == "avg_duration":
            value = round(sum(s.get("duration_minutes", 0) for s in filtered) / len(filtered), 1)
        elif metric == "avg_messages":
            value = round(sum(s.get("user_messages", 0) for s in filtered) / len(filtered), 1)
        elif metric == "friction":
            value = sum(sum((s.get("friction_counts") or {}).values()) for s in filtered)
        elif metric == "active_minutes":
            value = round(sum(s.get("active_minutes", 0) for s in filtered) / len(filtered), 1)
        elif metric == "apply_patch":
            value = round(sum((s.get("tool_counts") or {}).get("apply_patch", 0) for s in filtered) / len(filtered), 1)
        else:
            value = 0
        rows.append({"label": day[5:], "full_label": day, "value": value})
    return rows[-30:]


def _build_trend_windows(series_specs: list[dict]) -> list[dict]:
    windows = []
    for key, days in (("7d", 7), ("14d", 14), ("30d", 30)):
        window_series = []
        for spec in series_specs:
            points = spec["points"][-days:]
            window_series.append(
                {
                    "name": spec["name"],
                    "color": spec["color"],
                    "points": points,
                }
            )
        windows.append(
            {
                "key": key,
                "label": key.upper(),
                "series": window_series,
            }
        )
    return windows


def build_trend_cards(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    if meta.tool == "all":
        return [
            {
                "title": "Sessions Trend",
                "kind": "dual",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#2563eb", "points": _aggregate_series(data, "claude_code", "sessions")},
                    {"name": "Codex", "color": "#16a34a", "points": _aggregate_series(data, "codex_cli", "sessions")},
                ]),
            },
            {
                "title": "Avg Duration Trend",
                "kind": "dual",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#2563eb", "points": _aggregate_series(data, "claude_code", "avg_duration")},
                    {"name": "Codex", "color": "#16a34a", "points": _aggregate_series(data, "codex_cli", "avg_duration")},
                ]),
            },
            {
                "title": "Avg Messages Trend",
                "kind": "dual",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#2563eb", "points": _aggregate_series(data, "claude_code", "avg_messages")},
                    {"name": "Codex", "color": "#16a34a", "points": _aggregate_series(data, "codex_cli", "avg_messages")},
                ]),
            },
            {
                "title": "Claude Friction Trend",
                "kind": "single",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#dc2626", "points": _aggregate_series(data, "claude_code", "friction")}
                ]),
            },
        ]
    metric = "friction" if meta.tool == "claude" else "active_minutes"
    fourth_title = "Friction Trend" if meta.tool == "claude" else "Execution Intensity Trend"
    source = meta.primary_source or ""
    label = source_label(source)
    return [
        {
            "title": "Sessions Trend",
            "kind": "single",
            "default_window": "30d",
            "windows": _build_trend_windows([{"name": label, "color": "#2563eb", "points": _aggregate_series(data, source, "sessions")}]),
        },
        {
            "title": "Avg Duration Trend",
            "kind": "single",
            "default_window": "30d",
            "windows": _build_trend_windows([{"name": label, "color": "#16a34a", "points": _aggregate_series(data, source, "avg_duration")}]),
        },
        {
            "title": "Avg Messages Trend",
            "kind": "single",
            "default_window": "30d",
            "windows": _build_trend_windows([{"name": label, "color": "#0891b2", "points": _aggregate_series(data, source, "avg_messages")}]),
        },
        {
            "title": fourth_title,
            "kind": "single",
            "default_window": "30d",
            "windows": _build_trend_windows([{"name": label, "color": "#dc2626" if meta.tool == "claude" else "#7c3aed", "points": _aggregate_series(data, source, metric)}]),
        },
    ]


def build_project_drilldown(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for session in data.sessions:
        grouped[infer_project(session)].append(session)
    cards = []
    for project, sessions in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:6]:
        source_counts = Counter(s.get("source") for s in sessions)
        domain_counts = Counter(infer_domain(s) for s in sessions)
        tool_counts = Counter()
        for session in sessions:
            tool_counts.update(session.get("tool_counts") or {})
        split = (
            f"Claude {source_counts.get('claude_code', 0)} / Codex {source_counts.get('codex_cli', 0)}"
            if meta.tool == "all"
            else f"{source_label(meta.primary_source or '')} {len(sessions)}"
        )
        cards.append(
            {
                "project": project,
                "sessions": len(sessions),
                "split": split,
                "top_domains": ", ".join(name for name, _ in domain_counts.most_common(2)) or "暂无",
                "top_tools": ", ".join(name for name, _ in tool_counts.most_common(3)) or "暂无",
                "recommendation": (
                    "适合继续按固定模板推进。"
                    if len(sessions) >= 3
                    else "样本较少，建议后续继续积累后再判断是否要单独沉淀模板。"
                ),
            }
        )
    return cards


def build_leaderboards(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    stable = []
    longest = []
    highest_friction = []
    for session in data.sessions:
        domain = infer_domain(session)
        project = infer_project(session)
        label = f"{source_label(session.get('source', ''))} | {project} | {domain}"
        duration = session.get("active_minutes") or session.get("duration_minutes", 0)
        longest.append((label, duration))
        if session.get("source") == "claude_code":
            friction = sum((session.get("friction_counts") or {}).values())
            highest_friction.append((label, friction))
            if session.get("outcome") in {"fully_achieved", "mostly_achieved"} and duration <= 90 and friction <= 1:
                stable.append((label, round(100 - duration - friction * 10, 1)))
        else:
            patch_count = (session.get("tool_counts") or {}).get("apply_patch", 0)
            if duration <= 120 and session.get("user_messages", 0) <= 25 and patch_count >= 3:
                stable.append((label, round(100 - duration / 2 + patch_count, 1)))
    stable.sort(key=lambda item: item[1], reverse=True)
    longest.sort(key=lambda item: item[1], reverse=True)
    highest_friction.sort(key=lambda item: item[1], reverse=True)
    boards = [
        {"title": "Most Reusable Sessions", "items": [{"label": label, "value": score} for label, score in stable[:5]]},
        {"title": "Longest Chain Sessions", "items": [{"label": label, "value": value} for label, value in longest[:5]]},
    ]
    if meta.tool != "codex":
        boards.append({"title": "Highest Friction Sessions", "items": [{"label": label, "value": value} for label, value in highest_friction[:5]]})
    return boards


def build_task_matrix(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    task_rows = [
        ("分析评审", "Claude", "先收敛目标、约束和证据，再决定是否进入执行"),
        ("调试与构建", "Claude -> Codex" if meta.tool == "all" else source_label(meta.primary_source or ""), "Claude 做 root cause，Codex 做修复与验证"),
        ("跨仓实现", "Codex" if meta.tool == "all" else source_label(meta.primary_source or ""), "先定边界，再分 repo 连续施工"),
        ("测试验证", "Codex" if meta.tool == "all" else source_label(meta.primary_source or ""), "按计划和门禁循环推进"),
        ("工作流设计", "Claude" if meta.tool == "all" else source_label(meta.primary_source or ""), "先定义规则，再固化成模板"),
        ("长链路执行", "Codex" if meta.tool == "all" else source_label(meta.primary_source or ""), "强制阶段 checkpoint 和回放小结"),
    ]
    counts = Counter(infer_task_type(session) for session in data.sessions)
    return [
        {"task": task, "recommended": recommended, "workflow": workflow, "observed_sessions": counts.get(task, 0)}
        for task, recommended, workflow in task_rows
    ]


def build_platform_recommendations(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    if meta.tool == "claude":
        sessions = claude.get("sessions", 0)
        avg_msg = claude.get("avg_user_messages", 0)
        avg_min = claude.get("avg_duration_min", 0)
        top_tools = ", ".join(f"{name}({cnt})" for name, cnt in (claude.get("top_tools") or [])[:3]) or "暂无"
        return [
            {"title": "分析层持续使用", "desc": f"本期 Claude {sessions} 个 sessions，平均 {avg_min} 分钟、{avg_msg} 条消息，适合继续承担分析与收敛。"},
            {"title": "结构化输出优先", "desc": f"当前 Top tools 为 {top_tools}，建议将输出固定为结论/证据/风险/建议/验证。"},
            {"title": "强化交接清单", "desc": "将 Claude 结论转为执行清单后交给执行层，可降低跨工具返工。"},
        ]
    if meta.tool == "codex":
        sessions = codex.get("sessions", 0)
        avg_msg = codex.get("avg_user_messages", 0)
        avg_min = codex.get("avg_duration_min", 0)
        top_tools = ", ".join(f"{name}({cnt})" for name, cnt in (codex.get("top_tools") or [])[:3]) or "暂无"
        return [
            {"title": "执行层持续使用", "desc": f"本期 Codex {sessions} 个 sessions，平均 {avg_min} 分钟、{avg_msg} 条消息，执行角色明确。"},
            {"title": "阶段协议优先", "desc": f"Top tools 为 {top_tools}，建议每批改动后固定输出阶段小结。"},
            {"title": "验证门禁前移", "desc": "每批改动后先做 analyze/关键检查，再进入下一批，可降低长链路返工。"},
        ]
    c_sessions = claude.get("sessions", 0)
    x_sessions = codex.get("sessions", 0)
    c_avg_msg = claude.get("avg_user_messages", 0)
    x_avg_msg = codex.get("avg_user_messages", 0)
    return [
        {"title": "保持双层分工", "desc": f"本期 sessions: Claude {c_sessions} / Codex {x_sessions}，角色分工已具备数据支撑。"},
        {"title": "按消息密度分配角色", "desc": f"每 session 消息数: Claude {c_avg_msg} / Codex {x_avg_msg}，建议继续分析-执行拆分。"},
        {"title": "优先优化交接质量", "desc": "将目标、边界、验证命令作为固定交接字段，可提升跨工具稳定性。"},
    ]


def build_prompt_library(narrative: NarrativeBundle, meta: ReportMeta) -> dict[str, list[dict]]:
    library = {
        "Features": [{"title": item["title"], "prompt": item["prompt"]} for item in narrative.feature_cards],
        "Patterns": [{"title": item["title"], "prompt": item["prompt"]} for item in narrative.pattern_cards],
    }
    if meta.tool == "all":
        library["Handoff"] = [
            {
                "title": "Claude -> Codex Handoff",
                "prompt": "先让 Claude 输出目标 repo、参考实现、改动边界、验证命令。确认后，把同一份清单完整交给 Codex 执行，并要求每个阶段输出已完成、已验证、剩余风险、下一步。",
            }
        ]
    return library


def build_quality_score(data: AnalyzedData, meta: ReportMeta, narrative: NarrativeBundle) -> dict:
    completeness = 55
    if data.sessions:
        completeness += 15
    if meta.tool == "all" and all(data.comparison.get(source, {}).get("sessions", 0) > 0 for source in ("claude_code", "codex_cli")):
        completeness += 15
    if meta.tool == "claude" and data.friction_counts:
        completeness += 10
    if meta.tool == "codex" and len(data.sessions) >= 10:
        completeness += 10
    clarity = 70 if meta.tool != "all" else 82
    if meta.tool == "all":
        clarity += 6
    explainability = 65
    if data.friction_counts:
        explainability += 15
    if meta.tool in {"codex", "all"}:
        explainability += 10
    actionability = 60 + min(len(narrative.feature_cards) * 5 + len(narrative.pattern_cards) * 5, 30)
    breakdown = {
        "Data Completeness": min(completeness, 100),
        "Platform Clarity": min(clarity, 100),
        "Friction Explainability": min(explainability, 100),
        "Actionability": min(actionability, 100),
    }
    overall = round(sum(breakdown.values()) / len(breakdown))
    return {"overall": overall, "grade": "A" if overall >= 85 else "B" if overall >= 70 else "C", "breakdown": breakdown}


def build_snapshot_compare(data: AnalyzedData, meta: ReportMeta, previous_snapshot: dict | None, quality_score: dict) -> dict:
    current = {
        "sessions": {source: stats.get("sessions", 0) for source, stats in data.comparison.items()},
        "avg_duration_min": {source: stats.get("avg_duration_min", 0) for source, stats in data.comparison.items()},
        "avg_user_messages": {source: stats.get("avg_user_messages", 0) for source, stats in data.comparison.items()},
        "quality_overall": quality_score["overall"],
    }
    if not previous_snapshot:
        return {
            "summary": "这是当前模式下的第一份可比快照，后续再次生成时会自动显示与上一次报告的差异。",
            "previous_generated_at": None,
            "changes": [],
        }
    changes = []
    for source, current_sessions in current["sessions"].items():
        prev_sessions = (previous_snapshot.get("sessions") or {}).get(source, 0)
        prev_duration = (previous_snapshot.get("avg_duration_min") or {}).get(source, 0)
        prev_messages = (previous_snapshot.get("avg_user_messages") or {}).get(source, 0)
        changes.append(
            {
                "label": source_label(source),
                "sessions_delta": round(current_sessions - prev_sessions, 1),
                "duration_delta": round(current["avg_duration_min"].get(source, 0) - prev_duration, 1),
                "messages_delta": round(current["avg_user_messages"].get(source, 0) - prev_messages, 1),
            }
        )
    quality_delta = round(quality_score["overall"] - previous_snapshot.get("quality_overall", 0), 1)
    return {
        "summary": f"对比上一次同模式报告（{previous_snapshot.get('generated_at', '未知时间')}），当前质量评分变化 {quality_delta:+}。",
        "previous_generated_at": previous_snapshot.get("generated_at"),
        "changes": changes,
    }


def snapshot_payload(data: AnalyzedData, quality_score: dict, generated_at: str) -> dict:
    return {
        "generated_at": generated_at,
        "sessions": {source: stats.get("sessions", 0) for source, stats in data.comparison.items()},
        "avg_duration_min": {source: stats.get("avg_duration_min", 0) for source, stats in data.comparison.items()},
        "avg_user_messages": {source: stats.get("avg_user_messages", 0) for source, stats in data.comparison.items()},
        "quality_overall": quality_score["overall"],
    }


def build_report_extras(
    data: AnalyzedData,
    meta: ReportMeta,
    narrative: NarrativeBundle,
    previous_snapshot: dict | None,
    llm_analysis: dict | None = None,
) -> ReportExtras:
    quality = build_quality_score(data, meta, narrative)
    return ReportExtras(
        snapshot_compare=build_snapshot_compare(data, meta, previous_snapshot, quality),
        trend_cards=build_trend_cards(data, meta),
        platform_recommendations=build_platform_recommendations(data, meta),
        project_drilldown=build_project_drilldown(data, meta),
        leaderboards=build_leaderboards(data, meta),
        prompt_library=build_prompt_library(narrative, meta),
        task_matrix=build_task_matrix(data, meta),
        quality_score=quality,
        llm_analysis=llm_analysis,
    )
