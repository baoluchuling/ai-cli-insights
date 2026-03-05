from __future__ import annotations

import re
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
                "title": "会话数趋势",
                "kind": "dual",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#2563eb", "points": _aggregate_series(data, "claude_code", "sessions")},
                    {"name": "Codex", "color": "#16a34a", "points": _aggregate_series(data, "codex_cli", "sessions")},
                ]),
            },
            {
                "title": "平均时长趋势",
                "kind": "dual",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#2563eb", "points": _aggregate_series(data, "claude_code", "avg_duration")},
                    {"name": "Codex", "color": "#16a34a", "points": _aggregate_series(data, "codex_cli", "avg_duration")},
                ]),
            },
            {
                "title": "平均消息数趋势",
                "kind": "dual",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#2563eb", "points": _aggregate_series(data, "claude_code", "avg_messages")},
                    {"name": "Codex", "color": "#16a34a", "points": _aggregate_series(data, "codex_cli", "avg_messages")},
                ]),
            },
            {
                "title": "Claude 摩擦趋势",
                "kind": "single",
                "default_window": "30d",
                "windows": _build_trend_windows([
                    {"name": "Claude", "color": "#dc2626", "points": _aggregate_series(data, "claude_code", "friction")}
                ]),
            },
        ]
    metric = "friction" if meta.tool == "claude" else "active_minutes"
    fourth_title = "摩擦趋势" if meta.tool == "claude" else "执行强度趋势"
    source = meta.primary_source or ""
    label = source_label(source)
    return [
        {
            "title": "会话数趋势",
            "kind": "single",
            "default_window": "30d",
            "windows": _build_trend_windows([{"name": label, "color": "#2563eb", "points": _aggregate_series(data, source, "sessions")}]),
        },
        {
            "title": "平均时长趋势",
            "kind": "single",
            "default_window": "30d",
            "windows": _build_trend_windows([{"name": label, "color": "#16a34a", "points": _aggregate_series(data, source, "avg_duration")}]),
        },
        {
            "title": "平均消息数趋势",
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
        {"title": "最可复用会话", "items": [{"label": label, "value": score} for label, score in stable[:5]]},
        {"title": "最长链路会话", "items": [{"label": label, "value": value} for label, value in longest[:5]]},
    ]
    if meta.tool != "codex":
        boards.append({"title": "最高摩擦会话", "items": [{"label": label, "value": value} for label, value in highest_friction[:5]]})
    return boards


def build_task_matrix(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    task_rows = [
        ("分析评审", "先收敛目标、约束和证据，再决定是否进入执行"),
        ("调试与构建", "先定位根因，再小步修复并即时验证"),
        ("跨仓实现", "先定边界，再分 repo 连续施工"),
        ("测试验证", "按计划和门禁循环推进"),
        ("工作流设计", "先定义规则，再固化成模板"),
        ("长链路执行", "强制阶段 checkpoint 和回放小结"),
    ]
    counts = Counter()
    by_task_source: dict[str, Counter] = {}
    for session in data.sessions:
        task = infer_task_type(session)
        source = session.get("source", "")
        counts[task] += 1
        by_task_source.setdefault(task, Counter())[source] += 1

    def recommend_platform(task: str) -> str:
        source_counter = by_task_source.get(task, Counter())
        total = sum(source_counter.values())
        claude_count = source_counter.get("claude_code", 0)
        codex_count = source_counter.get("codex_cli", 0)
        if total == 0:
            return "待观察（样本不足）"
        if meta.tool == "all":
            gap = abs(claude_count - codex_count) / total
            if claude_count > 0 and codex_count > 0 and gap <= 0.25:
                return "双工具均有样本，按完成率/返工率动态路由"
            if claude_count == 0:
                return "仅 Codex 有样本，建议补 Claude 小样本 A/B"
            if codex_count == 0:
                return "仅 Claude 有样本，建议补 Codex 小样本 A/B"
            if claude_count > codex_count:
                ratio = round(claude_count / total * 100)
                return f"当前偏 Claude（{ratio}%），但不建议写死，保留 A/B"
            ratio = round(codex_count / total * 100)
            return f"当前偏 Codex（{ratio}%），但不建议写死，保留 A/B"
        if meta.primary_source:
            return f"当前仅 {source_label(meta.primary_source)} 样本，建议补跨工具对照"
        dominant = max(source_counter.items(), key=lambda item: item[1])[0]
        return f"当前样本偏 {source_label(dominant)}，建议按结果动态调整"

    return [
        {
            "task": task,
            "recommended": recommend_platform(task),
            "workflow": workflow,
            "observed_sessions": counts.get(task, 0),
        }
        for task, workflow in task_rows
    ]


def _selected_sessions(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    if meta.tool == "all":
        return list(data.sessions)
    source = meta.primary_source or ""
    return [session for session in data.sessions if session.get("source") == source]


def _token_count(session: dict) -> int:
    direct = session.get("tokens_used", 0) or 0
    if direct:
        return int(direct)
    return int((session.get("input_tokens", 0) or 0) + (session.get("output_tokens", 0) or 0))


def _approx_unit_cost_per_1k(source: str) -> float:
    # Coarse default for relative budgeting only.
    if source == "claude_code":
        return 0.015
    if source == "codex_cli":
        return 0.010
    return 0.012


def _build_cost_signal(data: AnalyzedData, meta: ReportMeta) -> dict:
    sessions = _selected_sessions(data, meta)
    by_source: dict[str, dict[str, float]] = defaultdict(lambda: {"sessions": 0, "tokens": 0})
    total_tokens = 0
    total_estimated_cost = 0.0
    for session in sessions:
        source = session.get("source") or "unknown"
        tokens = _token_count(session)
        by_source[source]["sessions"] += 1
        by_source[source]["tokens"] += tokens
        total_tokens += tokens
        total_estimated_cost += (tokens / 1000.0) * _approx_unit_cost_per_1k(source)
    bullets = []
    for source, item in sorted(by_source.items(), key=lambda pair: pair[1]["tokens"], reverse=True):
        s_count = int(item["sessions"])
        t_count = int(item["tokens"])
        avg_tokens = round(t_count / s_count) if s_count else 0
        est_cost = round((t_count / 1000.0) * _approx_unit_cost_per_1k(source), 2)
        bullets.append(
            f"{source_label(source)}: {t_count:,} tokens（均值 {avg_tokens:,}/session），估算成本 ${est_cost}"
        )
    if not bullets:
        bullets.append("暂无 token 数据，无法计算成本。")
    summary = (
        f"本窗口累计 {total_tokens:,} tokens，估算总成本 ${round(total_estimated_cost, 2)}。"
        if total_tokens
        else "本窗口未检测到可计量 token。"
    )
    return {
        "title": "Token 成本信号",
        "summary": summary,
        "bullets": bullets,
    }


def _drift_reasons(session: dict) -> list[str]:
    reasons = []
    user_messages = session.get("user_messages", 0) or 0
    active_minutes = session.get("active_minutes", 0) or session.get("duration_minutes", 0) or 0
    tool_kinds = len((session.get("tool_counts") or {}).keys())
    apply_patch = (session.get("tool_counts") or {}).get("apply_patch", 0)
    friction = sum((session.get("friction_counts") or {}).values())
    if user_messages >= 18:
        reasons.append(f"消息密度高({user_messages})")
    if active_minutes >= 120:
        reasons.append(f"链路较长({active_minutes}m)")
    if tool_kinds >= 6:
        reasons.append(f"工具切换多({tool_kinds}类)")
    if session.get("source") == "codex_cli" and user_messages >= 12 and apply_patch <= 1:
        reasons.append("讨论较多但落地改动偏少")
    if session.get("source") == "claude_code" and session.get("outcome") in {"partially_achieved", "not_achieved"} and friction >= 2:
        reasons.append("未达成且摩擦偏高")
    return reasons


def _build_drift_signal(data: AnalyzedData, meta: ReportMeta) -> dict:
    sessions = _selected_sessions(data, meta)
    candidates = []
    for session in sessions:
        reasons = _drift_reasons(session)
        if len(reasons) >= 2:
            label = f"{source_label(session.get('source', ''))} | {infer_project(session)}"
            candidates.append((label, reasons, len(reasons)))
    candidates.sort(key=lambda item: item[2], reverse=True)
    bullets = [
        f"{label}: {', '.join(reasons[:3])}"
        for label, reasons, _score in candidates[:4]
    ] or ["未检测到明显目标漂移信号。"]
    if sessions:
        ratio = round(len(candidates) / len(sessions) * 100, 1)
        summary = f"疑似目标漂移会话 {len(candidates)}/{len(sessions)}（{ratio}%）。该指标是启发式信号，不是人工标注真值。"
    else:
        summary = "暂无会话样本，无法评估目标漂移。"
    return {
        "title": "目标漂移信号",
        "summary": summary,
        "bullets": bullets,
    }


def _prompt_signature(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    cleaned = re.sub(r"/[\w\-./]+", "<path>", cleaned)
    cleaned = re.sub(r"\d+", "<n>", cleaned)
    return cleaned[:48]


def _build_asset_signal(data: AnalyzedData, meta: ReportMeta) -> dict:
    sessions = _selected_sessions(data, meta)
    total = len(sessions)
    project_counts = Counter(infer_project(session) for session in sessions)
    domain_counts = Counter(infer_domain(session) for session in sessions)
    prompt_counts = Counter(_prompt_signature(session.get("first_prompt", "")) for session in sessions)
    reusable_projects = [(name, count) for name, count in project_counts.most_common(4) if count >= 2 and name != "unknown"]
    reusable_domains = [(name, count) for name, count in domain_counts.most_common(4) if count >= 2 and name != "unknown"]
    repeated_prompts = [(name, count) for name, count in prompt_counts.most_common(4) if name and count >= 2]
    top2_cover = sum(count for _name, count in project_counts.most_common(2))
    cover_ratio = round(top2_cover / total * 100, 1) if total else 0.0
    bullets = []
    if reusable_projects:
        bullets.append("项目SOP候选: " + "；".join(f"{name}({count})" for name, count in reusable_projects[:3]))
    if reusable_domains:
        bullets.append("任务模板候选: " + "；".join(f"{name}({count})" for name, count in reusable_domains[:3]))
    if repeated_prompts:
        bullets.append("重复提示词簇: " + "；".join(f"{name[:24]}...({count})" for name, count in repeated_prompts[:2]))
    if not bullets:
        bullets.append("可复用资产信号偏弱，建议先稳定记录项目与提示词。")
    summary = (
        f"Top2 项目覆盖 {top2_cover}/{total} 次会话（{cover_ratio}%），已有资产化空间。"
        if total
        else "暂无会话样本，无法识别可复用资产。"
    )
    return {
        "title": "可复用资产信号",
        "summary": summary,
        "bullets": bullets,
    }


def build_operational_signals(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    return [
        _build_cost_signal(data, meta),
        _build_drift_signal(data, meta),
        _build_asset_signal(data, meta),
    ]


def _signal_recommendations(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    sessions = _selected_sessions(data, meta)
    total = len(sessions)
    total_tokens = sum(_token_count(session) for session in sessions)
    drift_hits = 0
    for session in sessions:
        if len(_drift_reasons(session)) >= 2:
            drift_hits += 1
    drift_ratio = (drift_hits / total) if total else 0.0
    project_counts = Counter(infer_project(session) for session in sessions)
    top2_cover = sum(count for _name, count in project_counts.most_common(2))
    cover_ratio = (top2_cover / total) if total else 0.0

    cards: list[dict] = []
    if total_tokens >= 5_000_000:
        cards.append(
            {
                "title": "加上 Token 预算门禁",
                "desc": f"本窗口 token 已到 {total_tokens:,}。建议按项目设预算上限和超额提醒，避免高消耗会话持续外溢。",
            }
        )
    elif total_tokens > 0:
        cards.append(
            {
                "title": "保持成本趋势跟踪",
                "desc": f"当前累计 token {total_tokens:,}。建议固定看周环比，提早发现成本抬头。",
            }
        )

    if drift_ratio >= 0.2:
        cards.append(
            {
                "title": "先治目标漂移",
                "desc": f"疑似漂移占比 {drift_ratio * 100:.1f}%。建议强制每阶段复述目标/边界/结束条件，再继续执行。",
            }
        )
    elif drift_hits > 0:
        cards.append(
            {
                "title": "建立漂移观察清单",
                "desc": f"本期有 {drift_hits} 个漂移信号会话。建议纳入周复盘并追踪是否反复出现。",
            }
        )
    else:
        cards.append(
            {
                "title": "目标对齐保持得不错",
                "desc": "本期未见明显漂移信号。继续保持阶段化推进和边界显式声明。",
            }
        )

    if total >= 4 and cover_ratio >= 0.6:
        cards.append(
            {
                "title": "优先沉淀 Top2 资产",
                "desc": f"Top2 项目覆盖 {cover_ratio * 100:.1f}%。先给这两个项目各产出 1 份 SOP + Prompt 包，复用收益最高。",
            }
        )
    elif total > 0:
        cards.append(
            {
                "title": "先积累再资产化",
                "desc": "当前项目分布较散。建议先补样本并统一记录 prompt 结构，再做模板沉淀。",
            }
        )
    return cards


def build_platform_recommendations(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    if meta.tool == "claude":
        sessions = claude.get("sessions", 0)
        avg_msg = claude.get("avg_user_messages", 0)
        avg_min = claude.get("avg_duration_min", 0)
        top_tools = ", ".join(f"{name}({cnt})" for name, cnt in (claude.get("top_tools") or [])[:3]) or "暂无"
        cards = [
            {"title": "保持高价值用法", "desc": f"本期 Claude {sessions} 次会话，平均 {avg_min} 分钟、{avg_msg} 条消息；Top tools: {top_tools}。优先延续已验证有效的任务类型。"},
            {"title": "结构化输出优先", "desc": "建议固定输出结论/证据/风险/建议/验证，提升复盘与协作可读性。"},
            {"title": "工具选择按结果决定", "desc": "不要预设“Claude 只能做某类任务”，建议按完成率、返工率、验证通过率做动态路由。"},
        ]
        cards.extend(_signal_recommendations(data, meta))
        return cards
    if meta.tool == "codex":
        sessions = codex.get("sessions", 0)
        avg_msg = codex.get("avg_user_messages", 0)
        avg_min = codex.get("avg_duration_min", 0)
        top_tools = ", ".join(f"{name}({cnt})" for name, cnt in (codex.get("top_tools") or [])[:3]) or "暂无"
        cards = [
            {"title": "保持高价值用法", "desc": f"本期 Codex {sessions} 次会话，平均 {avg_min} 分钟、{avg_msg} 条消息；Top tools: {top_tools}。优先延续已验证有效的任务类型。"},
            {"title": "阶段协议优先", "desc": "建议每批改动后固定输出阶段小结，提升可回放性。"},
            {"title": "工具选择按结果决定", "desc": "不要预设“Codex 只能做某类任务”，建议按完成率、返工率、验证通过率做动态路由。"},
        ]
        cards.extend(_signal_recommendations(data, meta))
        return cards
    c_sessions = claude.get("sessions", 0)
    x_sessions = codex.get("sessions", 0)
    c_avg_msg = claude.get("avg_user_messages", 0)
    x_avg_msg = codex.get("avg_user_messages", 0)
    if c_sessions == 0 or x_sessions == 0:
        route_tip = "当前样本偏单工具，建议下周期对另一工具做小样本 A/B 试跑，再决定是否扩大使用。"
    else:
        route_tip = "当前双工具均有样本，建议按任务完成率/返工率动态选择，不要固定工具分工。"
    cards = [
        {"title": "先看真实分布", "desc": f"本期会话分布：Claude {c_sessions} / Codex {x_sessions}；每会话消息：Claude {c_avg_msg} / Codex {x_avg_msg}。"},
        {"title": "动态路由而非写死分工", "desc": route_tip},
        {"title": "优先优化交接质量", "desc": "将目标、边界、验证命令作为固定交接字段，可提升跨工具协作稳定性。"},
    ]
    cards.extend(_signal_recommendations(data, meta))
    return cards


def build_prompt_library(narrative: NarrativeBundle, meta: ReportMeta) -> dict[str, list[dict]]:
    library = {
        "功能动作": [{"title": item["title"], "prompt": item["prompt"]} for item in narrative.feature_cards],
        "模式动作": [{"title": item["title"], "prompt": item["prompt"]} for item in narrative.pattern_cards],
    }
    if meta.tool == "all":
        library["交接模板"] = [
            {
                "title": "跨工具交接模板（通用）",
                "prompt": "先由当前工具输出交接清单：目标 repo、改动边界、证据/参考、验证命令、结束条件。确认后交给下一工具执行，并要求每阶段输出：已完成、已验证、剩余风险、下一步。",
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
        operational_signals=build_operational_signals(data, meta),
        platform_recommendations=build_platform_recommendations(data, meta),
        project_drilldown=build_project_drilldown(data, meta),
        leaderboards=build_leaderboards(data, meta),
        prompt_library=build_prompt_library(narrative, meta),
        task_matrix=build_task_matrix(data, meta),
        quality_score=quality,
        llm_analysis=llm_analysis,
    )
