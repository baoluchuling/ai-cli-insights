from __future__ import annotations

import html
from textwrap import dedent

from ..analytics import delta_text, infer_codex_archetypes, source_label
from ..models import AnalyzedData, NarrativeBundle, PeriodComparison, ReportExtras, ReportMeta
from .shared import bar_rows, block_title_html, fmt_list, fmt_tool_list, format_metric, heading_html, sparkline_svg, title_with_help


def _delta_descriptor(delta: float) -> tuple[str, str]:
    if abs(delta) < 0.05:
        return "持平", "delta-flat"
    if delta > 0:
        return f"上升 {format_metric(abs(delta))}", "delta-up"
    return f"下降 {format_metric(abs(delta))}", "delta-down"


def _series_summary_pill(item: dict, previous_window_item: dict | None) -> str:
    latest_value = item["points"][-1]["value"]
    prev_step_text = "无"
    prev_step_class = "delta-flat"
    if len(item["points"]) >= 2:
        prev_step_delta = round(latest_value - item["points"][-2]["value"], 1)
        prev_step_text, prev_step_class = _delta_descriptor(prev_step_delta)
    prev_window_text = "无"
    prev_window_class = "delta-flat"
    if previous_window_item and previous_window_item.get("points"):
        prev_window_delta = round(latest_value - previous_window_item["points"][-1]["value"], 1)
        prev_window_text, prev_window_class = _delta_descriptor(prev_window_delta)
    return (
        f'<div class="trend-summary-pill trend-pill-metric" style="--pill-accent:{item["color"]}">'
        f'<span class="trend-pill-label">{html.escape(item["name"])}</span>'
        f'<span class="trend-pill-value">{format_metric(latest_value)}</span>'
        '<span class="trend-pill-subvalue">当前值</span>'
        '</div>'
        f'<div class="trend-summary-pill {prev_step_class}">'
        '<span class="trend-pill-label">相邻点</span>'
        f'<span class="trend-pill-value">{html.escape(prev_step_text)}</span>'
        '<span class="trend-pill-subvalue">相对上一点</span>'
        '</div>'
        f'<div class="trend-summary-pill {prev_window_class}">'
        '<span class="trend-pill-label">前窗口</span>'
        f'<span class="trend-pill-value">{html.escape(prev_window_text)}</span>'
        '<span class="trend-pill-subvalue">相对前一窗口</span>'
        '</div>'
    )


def _gap_summary_pill(series: list[dict]) -> str:
    if len(series) != 2 or not all(item["points"] for item in series):
        return ""
    left = series[0]
    right = series[1]
    delta = round(right["points"][-1]["value"] - left["points"][-1]["value"], 1)
    delta_text_value, delta_class = _delta_descriptor(delta)
    if abs(delta) < 0.05:
        label = f"{html.escape(right['name'])} 与 {html.escape(left['name'])}"
        value = "持平"
    else:
        leader = right["name"] if delta > 0 else left["name"]
        trailer = left["name"] if delta > 0 else right["name"]
        label = f"{html.escape(leader)} 高于 {html.escape(trailer)}"
        value = delta_text_value
    return (
        f'<div class="trend-summary-pill {delta_class}">'
        '<span class="trend-pill-label">差值</span>'
        f'<span class="trend-pill-value">{value}</span>'
        f'<span class="trend-pill-subvalue">{label}</span>'
        '</div>'
    )


def build_comparison_table(data: AnalyzedData, meta: ReportMeta) -> str:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    primary = data.comparison.get(meta.primary_source or "", {})
    if meta.compare_sources:
        rows = [
            ("会话数量", str(claude.get("sessions", 0)), str(codex.get("sessions", 0))),
            ("平均时长", f"{claude.get('avg_duration_min', 0)} 分钟", f"{codex.get('avg_duration_min', 0)} 分钟"),
            ("平均每 Session 用户消息数", str(claude.get("avg_user_messages", 0)), str(codex.get("avg_user_messages", 0))),
            ("工具 Top5", fmt_tool_list(claude.get("top_tools", [])), fmt_tool_list(codex.get("top_tools", []))),
            ("涉及项目", fmt_list(claude.get("top_projects", [])), fmt_list(codex.get("top_projects", []))),
        ]
        return "\n".join(
            f"<tr><td>{html.escape(label)}</td><td>{html.escape(left)}</td><td>{html.escape(right)}</td></tr>"
            for label, left, right in rows
        )
    rows = [
        ("会话数量", str(primary.get("sessions", 0))),
        ("平均时长", f"{primary.get('avg_duration_min', 0)} 分钟"),
        ("平均每 Session 用户消息数", str(primary.get("avg_user_messages", 0))),
        ("工具 Top5", fmt_tool_list(primary.get("top_tools", []))),
        ("涉及项目", fmt_list(primary.get("top_projects", []))),
    ]
    return "\n".join(
        f"<tr><td>{html.escape(label)}</td><td>{html.escape(value)}</td></tr>"
        for label, value in rows
    )


def build_period_section(period_comparison: PeriodComparison | None, meta: ReportMeta) -> str:
    if not period_comparison:
        return ""
    if meta.compare_sources:
        rows = []
        for source in ("claude_code", "codex_cli"):
            cur = period_comparison.current.get(source, {})
            prev = period_comparison.previous.get(source, {})
            rows.append(
                "<tr>"
                f"<td>{source_label(source)}</td>"
                f"<td>{delta_text(cur.get('sessions', 0), prev.get('sessions', 0))}</td>"
                f"<td>{delta_text(cur.get('avg_duration_min', 0), prev.get('avg_duration_min', 0), ' 分钟')}</td>"
                f"<td>{delta_text(cur.get('avg_user_messages', 0), prev.get('avg_user_messages', 0))}</td>"
                "</tr>"
            )
        return (
            f"{heading_html('h2', '周期对比', 'period', 'section-period')}"
            f"<p class=\"section-intro\">当前周期 {html.escape(period_comparison.current_label)}，对比上一周期 {html.escape(period_comparison.previous_label)}。括号内为相对上一周期的变化值。</p>"
            "<table class=\"comparison-table\"><thead><tr><th>工具</th><th>会话数</th><th>平均时长</th><th>平均消息数</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    source = meta.primary_source or ""
    cur = period_comparison.current.get(source, {})
    prev = period_comparison.previous.get(source, {})
    return (
        f"{heading_html('h2', '周期对比', 'period', 'section-period')}"
        f"<p class=\"section-intro\">当前周期 {html.escape(period_comparison.current_label)}，对比上一周期 {html.escape(period_comparison.previous_label)}。括号内为相对上一周期的变化值。</p>"
        "<table class=\"comparison-table\"><thead><tr><th>维度</th><th>变化</th></tr></thead><tbody>"
        f"<tr><td>会话数</td><td>{delta_text(cur.get('sessions', 0), prev.get('sessions', 0))}</td></tr>"
        f"<tr><td>平均时长</td><td>{delta_text(cur.get('avg_duration_min', 0), prev.get('avg_duration_min', 0), ' 分钟')}</td></tr>"
        f"<tr><td>平均每 Session 用户消息数</td><td>{delta_text(cur.get('avg_user_messages', 0), prev.get('avg_user_messages', 0))}</td></tr>"
        "</tbody></table>"
    )


def _mode_copy(variant: str) -> dict[str, str]:
    if variant == "claude":
        return {
            "lane": "分析侧",
            "win": "分析信号",
            "friction": "评审风险",
            "recommendation": "决策规则",
            "library": "分析提示词",
            "feature": "提示词模板",
            "pattern": "工作流模式",
        }
    if variant == "codex":
        return {
            "lane": "执行侧",
            "win": "执行信号",
            "friction": "交付风险",
            "recommendation": "执行规则",
            "library": "执行提示词",
            "feature": "操作模板",
            "pattern": "执行模式",
        }
    return {
        "lane": "工作流",
        "win": "平台信号",
        "friction": "协作风险",
        "recommendation": "工作流规则",
        "library": "通用提示词",
        "feature": "提示词模板",
        "pattern": "工作流模式",
    }


def render_project_cards(project_cards: list[dict], variant: str = "all") -> str:
    copy = _mode_copy(variant)
    return "\n".join(
        dedent(
            f"""
            <div class="project-area">
              <div class="area-header">
                <div class="area-heading">
                  <span class="area-mode-pill">{html.escape(copy['lane'])}</span>
                  <span class="area-name">{html.escape(card['name'])}</span>
                </div>
                <span class="area-count">{card['count']} 次会话 | {html.escape(card['split'])}</span>
              </div>
              <div class="area-desc">{html.escape(card['desc'])}</div>
            </div>
            """
        ).strip()
        for card in project_cards
    )


def render_wins(wins: list[dict], variant: str = "all") -> str:
    copy = _mode_copy(variant)
    return "\n".join(
        dedent(
            f"""
            <div class="big-win">
              <div class="card-kicker">{html.escape(copy['win'])}</div>
              <div class="big-win-title">{html.escape(item['title'])}</div>
              <div class="big-win-desc">{html.escape(item['desc'])}</div>
            </div>
            """
        ).strip()
        for item in wins
    )


def render_friction_cards(cards: list[dict], variant: str = "all") -> str:
    copy = _mode_copy(variant)
    return "\n".join(
        dedent(
            f"""
            <div class="friction-category">
              <div class="card-kicker">{html.escape(copy['friction'])}</div>
              <div class="friction-title">{html.escape(card['title'])}</div>
              <div class="friction-desc">{html.escape(card['desc'])}</div>
              <ul class="friction-examples">
                {''.join(f'<li>{html.escape(example)}</li>' for example in card['examples'])}
              </ul>
            </div>
            """
        ).strip()
        for card in cards
    )


def render_prompt_cards(cards: list[dict], kind: str, variant: str = "all") -> str:
    copy = _mode_copy(variant)
    class_name = "feature-card" if kind == "feature" else "pattern-card"
    title_class = "feature-title" if kind == "feature" else "pattern-title"
    summary_class = "feature-oneliner" if kind == "feature" else "pattern-summary"
    detail_class = "feature-why" if kind == "feature" else "pattern-detail"
    starter_class = "feature-starter" if kind == "feature" else "pattern-starter"
    starter_label = "开始建议：" if kind == "feature" else "下一步建议："
    kicker = copy["feature"] if kind == "feature" else copy["pattern"]
    return "\n".join(
        dedent(
            f"""
            <div class="{class_name}">
              <div class="card-kicker">{html.escape(kicker)}</div>
              <div class="{title_class}">{html.escape(card['title'])}</div>
              <div class="{summary_class}">{html.escape(card['summary'])}</div>
              <div class="{detail_class}">{html.escape(card['detail'])}</div>
              <div class="{starter_class}"><strong>{starter_label}</strong> {html.escape(card['starter'])}</div>
              <div class="copyable-prompt-section">
                <div class="prompt-label">可直接粘贴到 Claude 或 Codex：</div>
                <div class="copyable-prompt-row">
                  <code class="copyable-prompt">{html.escape(card['prompt'])}</code>
                  <button class="copy-btn" onclick="copyText(this)">复制</button>
                </div>
              </div>
            </div>
            """
        ).strip()
        for card in cards
    )


def render_horizon_cards(cards: list[dict]) -> str:
    return "\n".join(
        dedent(
            f"""
            <div class="horizon-card">
              <div class="horizon-title">{html.escape(card['title'])}</div>
              <div class="horizon-possible">{html.escape(card['desc'])}</div>
            </div>
            """
        ).strip()
        for card in cards
    )


def render_glance(glance_sections: list[str]) -> str:
    return "\n".join(f'<div class="glance-section">{item}</div>' for item in glance_sections)


def render_archetypes(data: AnalyzedData) -> str:
    codex_archetypes = infer_codex_archetypes(data)
    return "\n".join(
        dedent(
            f"""
            <div class="project-area">
              <div class="area-header">
                <div class="area-heading">
                  <span class="area-mode-pill">执行画像</span>
                  <span class="area-name">{html.escape(item['title'])}</span>
                </div>
                <span class="area-count">Inference</span>
              </div>
              <div class="area-desc"><strong>{html.escape(item['summary'])}</strong> {html.escape(item['detail'])}</div>
            </div>
            """
        ).strip()
        for item in codex_archetypes
    )


def render_friction_details(data: AnalyzedData) -> str:
    if not data.friction_counts:
        return ""
    outcome_html = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>"
        for name, count in data.outcomes.most_common()
    ) or '<tr><td colspan="2">暂无</td></tr>'
    top_friction_html = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>"
        for name, count in data.friction_counts.most_common(8)
    ) or '<tr><td colspan="2">暂无</td></tr>'
    friction_session_html = "\n".join(
        dedent(
            f"""
            <div class="project-area">
              <div class="area-header">
                <span class="area-name">{html.escape(item['project'])} | {html.escape(item['domain'])}</span>
                <span class="area-count">摩擦分 {item['score']}</span>
              </div>
              <div class="area-desc">{html.escape(item['friction_detail'] or item['summary'] or item['first_prompt'])}</div>
            </div>
            """
        ).strip()
        for item in data.friction_sessions[:3]
    )
    return (
        f"<details class='project-area'><summary class='area-name'>{title_with_help('打开 Claude 摩擦与结果统计', 'claude_friction_details')}</summary><div style='margin-top:16px'><div class='charts-row'><div class='chart-card'>{block_title_html('Claude 摩擦 Top', 'chart_claude_friction', 'chart-title')}<table class='comparison-table'><thead><tr><th>类型</th><th>次数</th></tr></thead><tbody>{top_friction_html}</tbody></table></div><div class='chart-card'>{block_title_html('Claude 结果分布', 'chart_claude_outcome', 'chart-title')}<table class='comparison-table'><thead><tr><th>结果</th><th>会话数</th></tr></thead><tbody>{outcome_html}</tbody></table></div></div><div class='project-areas'>{friction_session_html}</div></div></details>"
    )


def render_stats_row(data: AnalyzedData, meta: ReportMeta) -> str:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    primary = data.comparison.get(meta.primary_source or "", {})
    if meta.compare_sources:
        return (
            f"<div class='stat'><div class='stat-value'>{claude.get('sessions', 0)}</div><div class='stat-label'>Claude 会话数</div></div>"
            f"<div class='stat'><div class='stat-value'>{codex.get('sessions', 0)}</div><div class='stat-label'>Codex 会话数</div></div>"
            f"<div class='stat'><div class='stat-value'>{claude.get('avg_user_messages', 0)}</div><div class='stat-label'>Claude 每会话消息</div></div>"
            f"<div class='stat'><div class='stat-value'>{codex.get('avg_user_messages', 0)}</div><div class='stat-label'>Codex 每会话消息</div></div>"
            f"<div class='stat'><div class='stat-value'>{claude.get('avg_duration_min', 0)}</div><div class='stat-label'>Claude 平均分钟</div></div>"
            f"<div class='stat'><div class='stat-value'>{codex.get('avg_duration_min', 0)}</div><div class='stat-label'>Codex 平均分钟</div></div>"
        )
    return (
        f"<div class='stat'><div class='stat-value'>{primary.get('sessions', 0)}</div><div class='stat-label'>会话数</div></div>"
        f"<div class='stat'><div class='stat-value'>{primary.get('avg_user_messages', 0)}</div><div class='stat-label'>每会话消息</div></div>"
        f"<div class='stat'><div class='stat-value'>{primary.get('avg_duration_min', 0)}</div><div class='stat-label'>平均分钟</div></div>"
        f"<div class='stat'><div class='stat-value'>{primary.get('total_duration_hours', 0)}</div><div class='stat-label'>总时长(小时)</div></div>"
    )


def render_usage_block(narrative: NarrativeBundle) -> str:
    return (
        '<div class="narrative">'
        f"<p>{html.escape(narrative.usage_narrative['p1'])}</p>"
        f"<p>{html.escape(narrative.usage_narrative['p2'])}</p>"
        f"<p>{html.escape(narrative.usage_narrative['p3'])}</p>"
        f"<div class=\"key-insight\"><strong>关键模式：</strong> {html.escape(narrative.usage_narrative['key'])}</div>"
        "</div>"
    )


def render_chart_rows(data: AnalyzedData, meta: ReportMeta) -> tuple[str, str]:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    primary = data.comparison.get(meta.primary_source or "", {})
    source_name = source_label(meta.primary_source or "")
    top_tools_title = "Claude Top Tools" if meta.compare_sources else f"{source_name} Top Tools"
    top_projects_title = "Codex Top Tools" if meta.compare_sources else f"{source_name} Top Projects"
    top_domains_title = "Claude Top Domains" if meta.compare_sources else f"{source_name} Top Domains"
    first = (
        '<div class="charts-row">'
        '<div class="chart-card">'
        f"{block_title_html(top_tools_title, 'chart_top_tools', 'chart-title')}"
        f"{bar_rows((claude if meta.compare_sources else primary).get('top_tools', []), '#2563eb' if meta.compare_sources else '#f59e0b')}"
        "</div>"
        '<div class="chart-card">'
        f"{block_title_html(top_projects_title, 'chart_top_projects', 'chart-title')}"
        f"{bar_rows((codex if meta.compare_sources else primary).get('top_projects', []), '#f59e0b' if meta.compare_sources else '#16a34a')}"
        "</div>"
        "</div>"
    )
    second = (
        '<div class="charts-row">'
        '<div class="chart-card">'
        f"{block_title_html(top_domains_title, 'chart_top_domains', 'chart-title')}"
        f"{bar_rows((claude if meta.compare_sources else primary).get('top_domains', []), '#0891b2')}"
        "</div>"
        '<div class="chart-card">'
        f"{block_title_html('Codex Top Domains' if meta.compare_sources else 'Codex 推断执行画像', 'chart_execution_archetypes', 'chart-title')}"
        f"{bar_rows(codex.get('top_domains', []), '#16a34a') if meta.compare_sources else '<div class=\"empty\">见下方 inference 卡片</div>'}"
        "</div>"
        "</div>"
    )
    return first, second


def render_claude_focus_row(data: AnalyzedData) -> str:
    top_friction_html = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>"
        for name, count in data.friction_counts.most_common(6)
    ) or '<tr><td colspan="2">暂无</td></tr>'
    outcome_html = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>"
        for name, count in data.outcomes.most_common()
    ) or '<tr><td colspan="2">暂无</td></tr>'
    return (
        '<div class="charts-row">'
        '<div class="chart-card">'
        f"{block_title_html('Claude Top Friction', 'chart_claude_friction', 'chart-title')}"
        '<table class="comparison-table"><thead><tr><th>类型</th><th>次数</th></tr></thead><tbody>'
        f"{top_friction_html}"
        "</tbody></table>"
        "</div>"
        '<div class="chart-card">'
        f"{block_title_html('Claude Outcome', 'chart_claude_outcome', 'chart-title')}"
        '<table class="comparison-table"><thead><tr><th>结果</th><th>会话数</th></tr></thead><tbody>'
        f"{outcome_html}"
        "</tbody></table>"
        "</div>"
        "</div>"
    )


def render_codex_execution_row(data: AnalyzedData, meta: ReportMeta) -> str:
    primary = data.comparison.get(meta.primary_source or "", {})
    return (
        '<div class="charts-row">'
        '<div class="chart-card">'
        f"{block_title_html(f'{source_label(meta.primary_source or '')} Top Projects', 'chart_top_projects', 'chart-title')}"
        f"{bar_rows(primary.get('top_projects', []), '#16a34a')}"
        "</div>"
        '<div class="chart-card">'
        f"{block_title_html(f'{source_label(meta.primary_source or '')} Top Domains', 'chart_top_domains', 'chart-title')}"
        f"{bar_rows(primary.get('top_domains', []), '#0891b2')}"
        "</div>"
        "</div>"
    )


def render_snapshot_compare(snapshot_compare: dict) -> str:
    items = snapshot_compare.get("changes", [])
    cards = "".join(
        (
            '<div class="snapshot-card">'
            f"<strong>{html.escape(item['label'])}</strong>"
            f"<span>会话数变化: {item['sessions_delta']:+}</span>"
            f"<span>平均时长变化: {item['duration_delta']:+} 分钟</span>"
            f"<span>平均消息变化: {item['messages_delta']:+}</span>"
            "</div>"
        )
        for item in items
    ) or '<div class="snapshot-card"><strong>快照对比</strong><span>暂无上一份快照可比。</span></div>'
    return (
        f"{heading_html('h2', '快照对比', 'snapshot', 'section-snapshot')}"
        f'<p class="section-intro">{html.escape(snapshot_compare.get("summary", ""))}</p>'
        f'<div class="snapshot-grid">{cards}</div>'
    )


def render_trend_cards(trend_cards: list[dict]) -> str:
    cards = []
    for card in trend_cards:
        windows = card.get("windows", [])
        if not windows:
            continue
        default_window = card.get("default_window", windows[-1]["key"])
        active_window = default_window if any(window["key"] == default_window for window in windows) else windows[-1]["key"]
        legend = "".join(
            f'<span class="trend-legend-item"><span class="legend-dot" style="background:{item["color"]}"></span>{html.escape(item["name"])}</span>'
            for item in windows[0]["series"]
        )
        toggle = ""
        if len(windows) > 1:
            buttons = "".join(
                (
                    f'<button class="trend-window-btn{" is-active" if window["key"] == active_window else ""}" '
                    f'onclick="switchTrendWindow(this, \'{html.escape(window["key"])}\')">{html.escape(window["label"])}</button>'
                )
                for window in windows
            )
            toggle = f'<div class="trend-window-switcher">{buttons}</div>'
        panels = []
        for window_index, window in enumerate(windows):
            all_points = [point for item in window["series"] for point in item["points"]]
            start_label = min((point.get("full_label", point.get("label", "")) for point in all_points), default="")
            end_label = max((point.get("full_label", point.get("label", "")) for point in all_points), default="")
            previous_window = windows[window_index - 1] if window_index > 0 else None
            latest_values = " | ".join(
                f'{html.escape(item["name"])} {format_metric(item["points"][-1]["value"])}'
                for item in window["series"]
                if item["points"]
            ) or "暂无数据"
            peak_values = " | ".join(
                f'{html.escape(item["name"])} 峰值 {format_metric(max(point["value"] for point in item["points"]))}'
                for item in window["series"]
                if item["points"]
            ) or "暂无数据"
            latest_gap = ""
            if len(window["series"]) == 2 and all(item["points"] for item in window["series"]):
                left = window["series"][0]
                right = window["series"][1]
                left_value = left["points"][-1]["value"]
                right_value = right["points"][-1]["value"]
                delta = round(right_value - left_value, 1)
                if abs(delta) < 0.05:
                    latest_gap = f"当前差值: {html.escape(right['name'])} 与 {html.escape(left['name'])} 持平"
                else:
                    leader = right["name"] if delta > 0 else left["name"]
                    trailer = left["name"] if delta > 0 else right["name"]
                    latest_gap = (
                        f"当前差值: {html.escape(leader)} 比 {html.escape(trailer)} 高 {format_metric(abs(delta))}"
                    )
            summary_row = "".join(
                _series_summary_pill(
                    item,
                    previous_window["series"][series_index] if previous_window and series_index < len(previous_window["series"]) else None,
                )
                for series_index, item in enumerate(window["series"])
                if item["points"]
            )
            summary_row += _gap_summary_pill(window["series"])
            panels.append(
                f'<div class="trend-window-panel" data-window="{html.escape(window["key"])}"{" hidden" if window["key"] != active_window else ""}>'
                f'<div class="trend-summary-row">{summary_row}</div>'
                f'{sparkline_svg(window["series"])}'
                f'<div class="trend-window-meta">窗口 {html.escape(window["label"])} | {html.escape(start_label)} 到 {html.escape(end_label)} | 当前 {latest_values} | 峰值 {peak_values}'
                + (f" | {latest_gap}" if latest_gap else "")
                + " | 左侧纵轴给出最小/中位/峰值参考，图上已标出峰值与当前值，悬停折线节点可查看每日数值</div>"
                '</div>'
            )
        cards.append(
            '<div class="trend-card">'
            '<div class="trend-card-head">'
            f'{block_title_html(card["title"], "trend_card", "trend-card-title")}'
            f"{toggle}"
            '</div>'
            f'{"".join(panels)}'
            f'<div class="trend-legend">{legend}</div>'
            '</div>'
        )
    return f"{heading_html('h2', '关键趋势', 'trends', 'section-trends')}<div class=\"trend-grid\">" + "".join(cards) + "</div>"


def render_operational_signals(cards: list[dict]) -> str:
    body = "".join(
        (
            '<div class="snapshot-card">'
            f'<strong>{html.escape(card.get("title", ""))}</strong>'
            f'<span>{html.escape(card.get("summary", ""))}</span>'
            '<ul class="mini-list">'
            + "".join(f"<li>{html.escape(item)}</li>" for item in (card.get("bullets") or []))
            + "</ul>"
            "</div>"
        )
        for card in cards
    ) or '<div class="snapshot-card"><strong>运营信号</strong><span>暂无数据</span></div>'
    return (
        f"{heading_html('h2', '运营信号', 'operational', 'section-operational')}"
        '<p class="section-intro">这三项用于看流程运营面：成本压力、目标漂移信号、资产化机会。</p>'
        f'<div class="snapshot-grid">{body}</div>'
    )


def render_recommendations(cards: list[dict], variant: str = "all") -> str:
    copy = _mode_copy(variant)
    return (
        f"{heading_html('h2', '平台建议', 'recommendations', 'section-recommendations')}"
        '<div class="decision-grid">'
        + "".join(
            f'<div class="decision-card"><div class="card-kicker">{html.escape(copy["recommendation"])}</div><strong>{html.escape(card["title"])}</strong><span>{html.escape(card["desc"])}</span></div>'
            for card in cards
        )
        + "</div>"
    )


def render_llm_analysis(llm_analysis: dict | None) -> str:
    if not llm_analysis:
        return ""
    if llm_analysis.get("status") != "success":
        errors = llm_analysis.get("errors", [])
        error_rows = "".join(
            (
                "<tr>"
                f"<td>{html.escape(item.get('provider', ''))}</td>"
                f"<td>{html.escape(item.get('error', ''))}</td>"
                "</tr>"
            )
            for item in errors
        ) or "<tr><td colspan='2'>No details</td></tr>"
        return (
            f"{heading_html('h2', 'LLM 深度分析', 'llm', 'section-llm')}"
            "<p class='section-intro'>已尝试调用外部 LLM 生成深度分析，但本次调用失败。</p>"
            "<table class='comparison-table'><thead><tr><th>提供方</th><th>错误</th></tr></thead>"
            f"<tbody>{error_rows}</tbody></table>"
        )

    raw_insights = [str(item).strip() for item in llm_analysis.get("insights", []) if str(item).strip()]
    raw_risks = [str(item).strip() for item in llm_analysis.get("risks", []) if str(item).strip()]
    risk_markers = (
        "风险", "不足", "缺失", "偏", "不稳", "不够", "薄弱", "返工", "漂移", "阻碍", "单一", "依赖",
        "cannot", "lack", "insufficient", "risk", "bottleneck", "single",
    )
    positive_insights: list[str] = []
    risk_insights: list[str] = []
    for text in raw_insights:
        lowered = text.lower()
        if any(marker in text for marker in risk_markers) or any(marker in lowered for marker in risk_markers):
            risk_insights.append(text)
        else:
            positive_insights.append(text)
    if not positive_insights and raw_insights:
        positive_insights = raw_insights[:1]
        risk_insights = raw_insights[1:] + raw_risks
    else:
        risk_insights = risk_insights + raw_risks

    pos_html = "".join(f"<li>{html.escape(item)}</li>" for item in positive_insights)
    risk_html = "".join(f"<li>{html.escape(item)}</li>" for item in risk_insights)
    actions = "".join(f"<li>{html.escape(item)}</li>" for item in llm_analysis.get("actions", []))
    provider = html.escape(llm_analysis.get("provider", ""))
    model = html.escape(llm_analysis.get("model", "")) if llm_analysis.get("model") else "default"
    generated_at = html.escape(llm_analysis.get("generated_at", ""))
    return (
        f"{heading_html('h2', 'LLM 深度分析', 'llm', 'section-llm')}"
        f"<p class='section-intro'><strong>{html.escape(llm_analysis.get('headline', ''))}</strong></p>"
        f"<p class='section-intro'>{html.escape(llm_analysis.get('summary', ''))}</p>"
        f"<div class='snapshot-grid'>"
        f"<div class='snapshot-card'><strong>提供方</strong><span>{provider}</span><span>模型: {model}</span><span>{generated_at}</span></div>"
        "</div>"
        "<div class='charts-row'>"
        f"<div class='chart-card'>{block_title_html('正向信号', 'llm_insights', 'chart-title')}<ul class='mini-list'>{pos_html or '<li>暂无</li>'}</ul></div>"
        f"<div class='chart-card'>{block_title_html('风险信号', 'llm_risks', 'chart-title')}<ul class='mini-list'>{risk_html or '<li>暂无</li>'}</ul></div>"
        "</div>"
        "<div class='charts-row'>"
        f"<div class='chart-card'>{block_title_html('建议动作', 'llm_actions', 'chart-title')}<ul class='mini-list'>{actions or '<li>暂无</li>'}</ul></div>"
        "</div>"
    )


def render_quality_score(quality_score: dict) -> str:
    breakdown = quality_score.get("breakdown", {})
    cards = "".join(
        f'<div class="quality-card"><strong>{html.escape(name)}</strong><span>{score}/100</span></div>'
        for name, score in breakdown.items()
    )
    return (
        f"{heading_html('h2', '报告质量评分', 'quality', 'section-quality')}"
        f'<p class="section-intro">当前报告质量评分 {quality_score.get("overall", 0)} / 100，等级 {html.escape(quality_score.get("grade", "N/A"))}。</p>'
        f'<div class="score-badge">Overall {quality_score.get("overall", 0)} / {html.escape(quality_score.get("grade", "N/A"))}</div>'
        f'<div class="quality-grid">{cards}</div>'
    )


def render_project_drilldown(cards: list[dict], variant: str = "all") -> str:
    copy = _mode_copy(variant)
    return (
        f"{heading_html('h2', '项目下钻', 'projects', 'section-projects')}"
        '<div class="drilldown-grid">'
        + "".join(
            (
                '<div class="drilldown-card">'
                f'<div class="card-kicker">{html.escape(copy["lane"])}</div>'
                f'<strong>{html.escape(card["project"])}</strong>'
                f'<span>{card["sessions"]} 次会话 | {html.escape(card["split"])}</span>'
                f'<span>Top Domains: {html.escape(card["top_domains"])}</span>'
                f'<span>Top Tools: {html.escape(card["top_tools"])}</span>'
                f'<span>{html.escape(card["recommendation"])}</span>'
                '</div>'
            )
            for card in cards
        )
        + "</div>"
    )


def render_leaderboards(boards: list[dict]) -> str:
    cards = []
    for board in boards:
        items = "".join(
            f'<li>{html.escape(item["label"])} <strong>{item["value"]}</strong></li>'
            for item in board["items"]
        ) or "<li>暂无</li>"
        cards.append(f'<div class="leaderboard-card"><strong>{html.escape(board["title"])}</strong><ul class="mini-list">{items}</ul></div>')
    return f"{heading_html('h2', '高价值会话榜单', 'leaderboards', 'section-leaderboards')}<div class=\"leaderboard-grid\">" + "".join(cards) + "</div>"


def render_prompt_library(prompt_library: dict[str, list[dict]], variant: str = "all") -> str:
    copy = _mode_copy(variant)
    groups = []
    for group_name, prompts in prompt_library.items():
        items = "".join(
            (
                '<div class="prompt-card">'
                f'<div class="card-kicker">{html.escape(copy["library"])}</div>'
                f'<strong>{html.escape(item["title"])}</strong>'
                f'<div class="copyable-prompt-section"><div class="copyable-prompt-row"><code class="copyable-prompt">{html.escape(item["prompt"])}</code><button class="copy-btn" onclick="copyText(this)">复制</button></div></div>'
                '</div>'
            )
            for item in prompts
        )
        groups.append(f'<div><p class="section-intro">{html.escape(group_name)}</p><div class="prompt-library-grid">{items}</div></div>')
    return f"{heading_html('h2', '提示词库', 'library', 'section-library')}" + "".join(groups)


def render_task_matrix(rows: list[dict]) -> str:
    body = "".join(
        f'<tr><td>{html.escape(row["task"])}</td><td>{html.escape(row["recommended"])}</td><td>{row["observed_sessions"]}</td><td>{html.escape(row["workflow"])}</td></tr>'
        for row in rows
    )
    return (
        f"{heading_html('h2', '任务类型建议矩阵', 'matrix', 'section-matrix')}"
        '<table class="comparison-table matrix-table"><thead><tr><th>任务类型</th><th>样本信号（非限制）</th><th>观察到的会话数</th><th>建议流程（可调整）</th></tr></thead>'
        f'<tbody>{body}</tbody></table>'
    )
