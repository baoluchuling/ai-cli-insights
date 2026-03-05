from __future__ import annotations

import html
from textwrap import dedent

from ..analytics import source_label, total_user_messages
from ..models import AnalyzedData, NarrativeBundle, PeriodComparison, PlatformSection, ReportExtras, ReportMeta
from .sections import (
    build_comparison_table,
    build_period_section,
    render_archetypes,
    render_chart_rows,
    render_claude_focus_row,
    render_codex_execution_row,
    render_friction_cards,
    render_friction_details,
    render_glance,
    render_horizon_cards,
    render_leaderboards,
    render_llm_analysis,
    render_project_drilldown,
    render_prompt_library,
    render_quality_score,
    render_recommendations,
    render_project_cards,
    render_prompt_cards,
    render_snapshot_compare,
    render_stats_row,
    render_task_matrix,
    render_trend_cards,
    render_usage_block,
    render_wins,
)
from .shared import page_scripts, page_styles
from .shared import heading_html, title_with_help


def scope_section_ids(html_text: str, anchor_prefix: str) -> str:
    if not anchor_prefix:
        return html_text
    return html_text.replace('id="section-', f'id="{anchor_prefix}section-')


def render_single_platform_block(section: PlatformSection, anchor_prefix: str = "") -> str:
    usage_heading = f"How You Use {source_label(section.meta.primary_source or '')}"
    comparison_html = build_comparison_table(section.data, section.meta)
    period_html = build_period_section(section.period_comparison, section.meta)
    project_html = render_project_cards(section.project_cards, section.meta.tool)
    wins_html = render_wins(section.narrative.wins, section.meta.tool)
    friction_html = render_friction_cards(section.narrative.friction_cards, section.meta.tool)
    feature_html = render_prompt_cards(section.narrative.feature_cards, "feature", section.meta.tool)
    pattern_html = render_prompt_cards(section.narrative.pattern_cards, "pattern", section.meta.tool)
    horizon_html = render_horizon_cards(section.narrative.horizon_cards)
    stats_row_html = render_stats_row(section.data, section.meta)
    usage_block_html = render_usage_block(section.narrative)
    snapshot_html = scope_section_ids(render_snapshot_compare(section.extras.snapshot_compare), anchor_prefix)
    trend_html = scope_section_ids(render_trend_cards(section.extras.trend_cards), anchor_prefix)
    recommendation_html = scope_section_ids(render_recommendations(section.extras.platform_recommendations, section.meta.tool), anchor_prefix)
    quality_html = scope_section_ids(render_quality_score(section.extras.quality_score), anchor_prefix)
    drilldown_html = scope_section_ids(render_project_drilldown(section.extras.project_drilldown, section.meta.tool), anchor_prefix)
    leaderboard_html = scope_section_ids(render_leaderboards(section.extras.leaderboards), anchor_prefix)
    matrix_html = scope_section_ids(render_task_matrix(section.extras.task_matrix), anchor_prefix)
    library_html = scope_section_ids(render_prompt_library(section.extras.prompt_library, section.meta.tool), anchor_prefix)
    llm_analysis_html = scope_section_ids(render_llm_analysis(section.extras.llm_analysis), anchor_prefix)
    feature_section_class = f"{anchor_prefix}features-section" if anchor_prefix else "features-section"
    pattern_section_class = f"{anchor_prefix}patterns-section" if anchor_prefix else "patterns-section"
    anchor = lambda suffix: f"{anchor_prefix}{suffix}" if anchor_prefix else suffix
    if section.meta.tool == "claude":
        focus_block = render_claude_focus_row(section.data)
        chart_block = render_chart_rows(section.data, section.meta)[0]
        extra_detail = render_friction_details(section.data)
    else:
        focus_block = render_codex_execution_row(section.data, section.meta)
        chart_block = render_chart_rows(section.data, section.meta)[0]
        extra_detail = f"<div class=\"project-areas\">{render_archetypes(section.data)}</div>"

    mode_class = f"platform-mode platform-mode-{section.meta.tool}"
    content = (
        f"<div class=\"stats-row\">{stats_row_html}</div>"
        f"{quality_html}"
        f"{snapshot_html}"
        f"{trend_html}"
        f"{recommendation_html}"
        f"{llm_analysis_html}"
        f"{heading_html('h3', 'What You Work On', 'work', anchor('work'))}"
        f"<p class=\"section-intro\">{html.escape(section.narrative.work_intro)}</p>"
        f"<div class=\"project-areas\">{project_html}</div>"
        f"{drilldown_html}"
        f"{heading_html('h3', usage_heading, 'usage', anchor('usage'))}"
        f"{usage_block_html}"
        f"{heading_html('h3', 'Usage Snapshot', 'usage_snapshot', anchor('compare'))}"
        "<table class=\"comparison-table\">"
        f"<thead><tr><th>维度</th><th>{source_label(section.meta.primary_source or '')}</th></tr></thead>"
        f"<tbody>{comparison_html}</tbody></table>"
        f"{period_html}"
        f"{focus_block}"
        f"{chart_block}"
        f"{extra_detail}"
        f"{heading_html('h3', 'Impressive Things', 'wins', anchor('wins'))}"
        f"<p class=\"section-intro\">{html.escape(section.narrative.wins_intro)}</p>"
        f"<div class=\"big-wins\">{wins_html}</div>"
        f"{heading_html('h3', 'Where Things Go Wrong', 'friction', anchor('friction'))}"
        f"<p class=\"section-intro\">{html.escape(section.narrative.friction_intro)}</p>"
        f"<div class=\"friction-categories\">{friction_html}</div>"
        f"{leaderboard_html}"
        f"{matrix_html}"
        f"{library_html}"
        f"{heading_html('h3', 'Existing Features to Try', 'features', anchor('features'))}"
        f"<p class=\"section-intro\">{html.escape(section.narrative.feature_intro)}</p>"
        f"<div class=\"features-section {feature_section_class}\"><button class=\"copy-all-btn\" onclick=\"copyAllPrompts('{feature_section_class}')\">Copy All Feature Prompts</button>{feature_html}</div>"
        f"{heading_html('h3', 'New Ways to Use These Tools', 'patterns', anchor('patterns'))}"
        + (f'<p class="section-intro">{html.escape(section.narrative.pattern_intro)}</p>' if section.narrative.pattern_intro else "")
        + f"<div class=\"patterns-section {pattern_section_class}\"><button class=\"copy-all-btn\" onclick=\"copyAllPrompts('{pattern_section_class}')\">Copy All Pattern Prompts</button>{pattern_html}</div>"
        f"{heading_html('h3', 'On the Horizon', 'horizon', anchor('horizon'))}"
        f"<p class=\"section-intro\">{html.escape(section.narrative.horizon_intro)}</p>"
        f"<div class=\"horizon-section\">{horizon_html}</div>"
    )
    return f'<section class="{mode_class}">{content}</section>'


def render_html(
    data: AnalyzedData,
    meta: ReportMeta,
    period_comparison: PeriodComparison | None,
    narrative: NarrativeBundle,
    project_cards: list[dict],
    extras: ReportExtras,
    platform_sections: dict[str, PlatformSection] | None = None,
) -> str:
    period = data.raw.get("stats", {}).get("period", {})
    total_sessions = sum(source.get("sessions", 0) for source in data.comparison.values())
    total_msgs = total_user_messages(data.raw)
    usage_heading = "How You Use These Tools" if meta.tool == "all" else f"How You Use {source_label(meta.primary_source or '')}"
    comparison_html = build_comparison_table(data, meta)
    period_html = build_period_section(period_comparison, meta)
    project_html = render_project_cards(project_cards, meta.tool)
    wins_html = render_wins(narrative.wins, meta.tool)
    friction_html = render_friction_cards(narrative.friction_cards, meta.tool)
    feature_html = render_prompt_cards(narrative.feature_cards, "feature", meta.tool)
    pattern_html = render_prompt_cards(narrative.pattern_cards, "pattern", meta.tool)
    horizon_html = render_horizon_cards(narrative.horizon_cards)
    glance_html = render_glance(narrative.glance_sections)
    archetype_html = render_archetypes(data)
    friction_detail_html = render_friction_details(data)
    stats_row_html = render_stats_row(data, meta)
    usage_block_html = render_usage_block(narrative)
    first_chart_row, second_chart_row = render_chart_rows(data, meta)
    snapshot_html = render_snapshot_compare(extras.snapshot_compare)
    trend_html = render_trend_cards(extras.trend_cards)
    recommendation_html = render_recommendations(extras.platform_recommendations, meta.tool)
    quality_html = render_quality_score(extras.quality_score)
    drilldown_html = render_project_drilldown(extras.project_drilldown, meta.tool)
    leaderboard_html = render_leaderboards(extras.leaderboards)
    matrix_html = render_task_matrix(extras.task_matrix)
    library_html = render_prompt_library(extras.prompt_library, meta.tool)
    llm_analysis_html = render_llm_analysis(extras.llm_analysis)
    claude_platform_html = ""
    codex_platform_html = ""
    if meta.tool == "all" and platform_sections:
        scenario_card_html = (
            '<div class="scenario-card">'
            f'<div class="scenario-title">{title_with_help("什么时候该看哪份报告", "scenario_card")}</div>'
            '<div class="scenario-grid">'
            '<div class="scenario-item"><strong>看 Cross-Tool</strong><span>当你想一次看完整跨平台工作流、工具分工、全局趋势，以及两个平台的深度报告时，用这份总报告。</span></div>'
            '<div class="scenario-item"><strong>看 Claude-Only</strong><span>当你只想判断 Claude 这边的分析质量、摩擦模式、review 习惯和提示词约束时，用单平台报告更直接。</span></div>'
            '<div class="scenario-item"><strong>看 Codex-Only</strong><span>当你只想看执行层、阶段推进、施工画像和可回放性问题时，用单平台报告更聚焦。</span></div>'
            '</div>'
            '</div>'
        )
        claude_platform_html = (
            '<details class="platform-details" id="section-claude-report">'
            f'<summary>{title_with_help("Claude Platform Report", "claude_platform")}<span class="platform-summary-sub">展开查看完整 Claude-only 深度报告，用来回答判断层、review、证据链和 friction 的问题。</span></summary>'
            '<div class="platform-details-body">'
            f"{render_single_platform_block(platform_sections['claude'], 'claude-')}"
            '</div>'
            "</details>"
        )
        codex_platform_html = (
            '<details class="platform-details" id="section-codex-report">'
            f'<summary>{title_with_help("Codex Platform Report", "codex_platform")}<span class="platform-summary-sub">展开查看完整 Codex-only 深度报告，用来回答执行层、阶段推进、施工画像和回放能力的问题。</span></summary>'
            '<div class="platform-details-body">'
            f"{render_single_platform_block(platform_sections['codex'], 'codex-')}"
            '</div>'
            "</details>"
        )
    else:
        scenario_card_html = ""

    if meta.tool != "all":
        single_section = PlatformSection(
            meta=meta,
            data=data,
            period_comparison=period_comparison,
            narrative=narrative,
            project_cards=project_cards,
            extras=extras,
        )
        single_body = render_single_platform_block(single_section)
        single_nav = (
            '<a href="#section-quality">Quality</a>'
            '<a href="#section-snapshot">Snapshot</a>'
            '<a href="#section-trends">Trends</a>'
            '<a href="#section-recommendations">Recommendations</a>'
            '<a href="#section-llm">LLM</a>'
            '<a href="#work">What You Work On</a>'
            '<a href="#usage">Usage</a>'
            '<a href="#compare">Snapshot</a>'
            '<a href="#wins">Wins</a>'
            '<a href="#friction">Friction</a>'
            '<a href="#section-projects">Projects</a>'
            '<a href="#section-leaderboards">Leaderboards</a>'
            '<a href="#section-matrix">Task Matrix</a>'
            '<a href="#section-library">Prompt Library</a>'
            '<a href="#features">Features</a>'
            '<a href="#patterns">Patterns</a>'
            '<a href="#horizon">Horizon</a>'
        )
        return dedent(
            f"""\
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>{html.escape(meta.title)}</title>
              <style>
{page_styles()}
              </style>
            </head>
            <body class="report-mode-{meta.tool}">
              <div class="container">
                <h1>{title_with_help(meta.title, 'report_title')}</h1>
                <p class="subtitle">{html.escape(meta.subtitle_prefix)} | {total_msgs} 条用户消息，覆盖 {total_sessions} 个 sessions | {period.get('from', '')} 到 {period.get('to', '')} | 分析模型: {html.escape(meta.analyst_label)}</p>
                <div class="at-a-glance"><div class="glance-title">{title_with_help('At a Glance', 'at_a_glance')}</div><div class="glance-sections">{glance_html}</div></div>
                <nav class="nav-toc">{single_nav}</nav>
                {single_body}
                <div class="fun-ending">
                  <div class="fun-headline">{html.escape(narrative.ending_headline)}</div>
                  <div class="fun-detail">{html.escape(narrative.ending_detail)}</div>
                </div>
              </div>
              <script>
{page_scripts()}
              </script>
            </body>
            </html>
            """
        )

    return dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{html.escape(meta.title)}</title>
          <style>
{page_styles()}
          </style>
        </head>
        <body class="report-mode-{meta.tool}">
          <div class="container">
            <h1>{title_with_help(meta.title, 'report_title')}</h1>
            <p class="subtitle">{html.escape(meta.subtitle_prefix)} | {total_msgs} 条用户消息，覆盖 {total_sessions} 个 sessions | {period.get('from', '')} 到 {period.get('to', '')} | 分析模型: {html.escape(meta.analyst_label)}</p>
            <div class="at-a-glance"><div class="glance-title">{title_with_help('At a Glance', 'at_a_glance')}</div><div class="glance-sections">{glance_html}</div></div>
            {scenario_card_html}
            <nav class="nav-toc">
              <a href="#section-quality">Quality</a>
              <a href="#section-snapshot">Snapshot</a>
              <a href="#section-trends">Trends</a>
              <a href="#section-recommendations">Recommendations</a>
              <a href="#section-llm">LLM</a>
              <a href="#section-work">What You Work On</a>
              <a href="#section-usage">{html.escape(usage_heading)}</a>
              <a href="#section-compare">Usage Comparison</a>
              <a href="#section-period">Period over Period</a>
              <a href="#section-wins">Impressive Things</a>
              <a href="#section-friction">Where Things Go Wrong</a>
              <a href="#section-projects">Projects</a>
              <a href="#section-leaderboards">Leaderboards</a>
              <a href="#section-matrix">Task Matrix</a>
              <a href="#section-library">Prompt Library</a>
              <a href="#section-features">Features to Try</a>
              <a href="#section-patterns">New Usage Patterns</a>
              <a href="#section-horizon">On the Horizon</a>
              {'<a href="#section-claude-report">Claude Report</a><a href="#section-codex-report">Codex Report</a>' if meta.tool == 'all' else ''}
            </nav>
            <div class="stats-row">{stats_row_html}</div>
            {quality_html}
            {snapshot_html}
            {trend_html}
            {recommendation_html}
            {llm_analysis_html}
            {heading_html('h2', 'What You Work On', 'work', 'section-work')}
            <p class="section-intro">{html.escape(narrative.work_intro)}</p>
            <div class="project-areas">{project_html}</div>
            {drilldown_html}
            {heading_html('h2', usage_heading, 'usage', 'section-usage')}
            {usage_block_html}
            {heading_html('h2', 'Usage Comparison', 'compare', 'section-compare')}
            <table class="comparison-table">
              <thead><tr><th>维度</th><th>{'Claude Code' if meta.compare_sources else source_label(meta.primary_source or '')}</th>{'<th>Codex CLI</th>' if meta.compare_sources else ''}</tr></thead>
              <tbody>{comparison_html}</tbody>
            </table>
            {period_html}
            {first_chart_row}
            {second_chart_row}
            <div class="project-areas">{archetype_html if archetype_html else ''}</div>
            {heading_html('h2', 'Impressive Things You Did', 'wins', 'section-wins')}
            <p class="section-intro">{html.escape(narrative.wins_intro)}</p>
            <div class="big-wins">{wins_html}</div>
            {heading_html('h2', 'Where Things Go Wrong', 'friction', 'section-friction')}
            <p class="section-intro">{html.escape(narrative.friction_intro)}</p>
            <div class="friction-categories">{friction_html}</div>
            {friction_detail_html}
            {leaderboard_html}
            {matrix_html}
            {library_html}
            {claude_platform_html if meta.tool == 'all' else ''}
            {codex_platform_html if meta.tool == 'all' else ''}
            {heading_html('h2', 'Existing Features to Try', 'features', 'section-features')}
            <p class="section-intro">{html.escape(narrative.feature_intro)}</p>
            <div class="features-section">
              <button class="copy-all-btn" onclick="copyAllPrompts('features-section')">Copy All Feature Prompts</button>
              {feature_html}
            </div>
            {heading_html('h2', 'New Ways to Use These Tools', 'patterns', 'section-patterns')}
            {f'<p class="section-intro">{html.escape(narrative.pattern_intro)}</p>' if narrative.pattern_intro else ''}
            <div class="patterns-section">
              <button class="copy-all-btn" onclick="copyAllPrompts('patterns-section')">Copy All Pattern Prompts</button>
              {pattern_html}
            </div>
            {heading_html('h2', 'On the Horizon', 'horizon', 'section-horizon')}
            <p class="section-intro">{html.escape(narrative.horizon_intro)}</p>
            <div class="horizon-section">{horizon_html}</div>
            <div class="fun-ending">
              <div class="fun-headline">{html.escape(narrative.ending_headline)}</div>
              <div class="fun-detail">{html.escape(narrative.ending_detail)}</div>
            </div>
          </div>
          <script>
{page_scripts()}
          </script>
        </body>
        </html>
        """
    )
