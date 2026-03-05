from __future__ import annotations

import html


SECTION_GUIDES = {
    "report_title": "先看副标题里的统计区间、覆盖 session 数和分析模型，再决定这份报告是拿来比较工具分工，还是单独判断某一个平台的表现。",
    "at_a_glance": "这是整份报告的速览区。建议先读这四段：什么在起作用、什么在拖后腿、有哪些短期可试动作、哪些工作流值得继续投资。",
    "scenario_card": "这一段不是数据结论，而是选阅读路径。先判断你现在要看跨工具协作，还是只看 Claude/Codex 单平台质量，再决定往哪里展开。",
    "quality": "这是对报告本身的完整度检查，不是对你工作质量的打分。分数越高，说明这份报表覆盖的数据、叙事和建议越完整，越适合拿来做复盘。",
    "snapshot": "这一段看的是和上一份快照相比发生了什么变化。适合先判断最近是更集中、更分散，还是只是样本波动。",
    "trends": "这里看时间序列，而不是单点数值。优先关注趋势方向、峰值出现在哪段时间，以及两个平台之间的差距是在扩大还是收敛。",
    "operational": "这里是运营信号层：成本、目标漂移、可复用资产。它回答的是“要不要改流程”，不是“改哪一行代码”。",
    "trend_card": "单张趋势卡用来观察一个指标在不同时间窗口里的变化。先看 latest，再看 peak，最后看和另一条线的 gap 是否稳定。",
    "recommendations": "这一段是把统计和叙事压缩成可执行建议。阅读时重点看哪些建议能直接改你的工作流，而不是把它当成泛泛而谈的总结。",
    "work": "这里回答你主要把模型用在哪些项目和领域。重点不是项目名本身，而是哪些工作类型最占时间、最值得优化。",
    "usage": "这一段是叙事型总结，解释你实际是怎么委托模型工作的。适合用来判断你的提示方式、分工方式和控制方式是否稳定。",
    "compare": "这是核心对比表。先看 session 数和平均时长，再看消息密度、工具分布和项目分布，判断两个平台在工作位上的差异。",
    "period": "这里看当前统计窗口相对上一窗口的变化。适合判断近期是否进入了更长会话、更高密度沟通，或某个平台的使用强度突然变化。",
    "wins": "这部分不是夸奖，而是提炼高价值模式。重点看哪些做法已经证明有效，值得被固化成默认工作流。",
    "friction": "这是最适合做复盘的区域。先看最高频摩擦，再看具体例子，判断真正的问题是目标不清、执行偏航，还是验证链路不够硬。",
    "projects": "这里把高频项目拆开看。适合判断某个仓库或业务域是否反复消耗你，或者是否已经形成稳定处理套路。",
    "leaderboards": "这是高价值样本榜单。不要只看第一名，更要看这些高信号 session 共同具备什么特征，哪些模式可以复制。",
    "library": "这一段收的是可复用 prompt/操作模板。适合挑出能直接复用的句式或流程，而不是逐条阅读所有内容。",
    "matrix": "这个矩阵把任务类型映射到推荐平台和 workflow。适合拿来做前置决策：这类任务先给谁、怎么交接、如何验证。",
    "features": "这里列的是当前就能马上试的现成用法。优先看那些不需要改系统配置、只需要改你发任务方式的建议。",
    "patterns": "这里是新的工作流模式，不一定立刻执行，但适合挑出值得实验的长期协作方式。",
    "horizon": "这一段看的是后续可以继续投资的方向。重点不是立刻落地，而是判断哪些方向值得你继续产品化或模板化。",
    "claude_platform": "这一折叠区是 Claude-only 深报。适合集中判断分析层、review、证据链和 friction 的稳定性。",
    "codex_platform": "这一折叠区是 Codex-only 深报。适合集中判断执行层、长链路推进、阶段验证和回放能力。",
    "usage_snapshot": "这是单平台或局部平台的快速对比表。重点看这个平台内部的项目、工具和消息密度画像，而不是拿它和全局总表混读。",
    "chart_top_tools": "看工具调用是否集中在少数几种工具上。集中度高通常代表流程稳定，过于分散则可能说明任务切换或探索成本偏高。",
    "chart_top_projects": "看会话主要落在哪些项目上。适合判断注意力是否过度集中在少数仓库，或是否存在长期高消耗项目。",
    "chart_top_domains": "看任务类别分布。它能帮助你判断当前是以调试、组件化、测试还是工作流设计为主。",
    "chart_execution_archetypes": "这是对 Codex 执行形态的推断，不是显式标签。适合把它当成行为画像来读，而不是绝对分类。",
    "chart_claude_friction": "看 Claude 侧最常见的摩擦类型。优先关注最高频那几类，因为它们最能解释为什么某些对话容易偏航。",
    "chart_claude_outcome": "看 Claude 会话最后落到了什么结果。建议结合 friction 一起读，判断高摩擦是否真的压低了结果质量。",
    "claude_friction_details": "这是 Claude 的摩擦明细区。上半部分看类型分布，下半部分看高摩擦 session 示例，便于你定位真实问题场景。",
}


def fmt_tool_list(items: list[tuple[str, int]]) -> str:
    if not items:
        return "无"
    return ", ".join(f"{name}({count})" for name, count in items)


def fmt_list(items: list[tuple[str, int]]) -> str:
    if not items:
        return "无"
    return ", ".join(name for name, _ in items)


def bar_rows(items: list[tuple[str, int]], color: str) -> str:
    if not items:
        return '<div class="empty">暂无数据</div>'
    max_value = max(count for _, count in items) or 1
    rows = []
    for name, count in items:
        width = round(count / max_value * 100, 2)
        rows.append(
            (
                '<div class="bar-row">'
                f'<div class="bar-label">{html.escape(name)}</div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;background:{color}"></div></div>'
                f'<div class="bar-value">{count}</div>'
                "</div>"
            )
        )
    return "\n".join(rows)


def format_metric(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.1f}"


def title_with_help(text: str, guide_key: str) -> str:
    guide = SECTION_GUIDES.get(guide_key, "")
    label = html.escape(text)
    if not guide:
        return f'<span class="title-label">{label}</span>'
    return (
        '<span class="title-with-help">'
        f'<span class="title-label">{label}</span>'
        '<span class="title-help" tabindex="0" aria-label="查看这一段的解读指南">'
        '?'
        f'<span class="title-help-tooltip">{html.escape(guide)}</span>'
        "</span>"
        "</span>"
    )


def heading_html(tag: str, text: str, guide_key: str, element_id: str | None = None) -> str:
    id_attr = f' id="{html.escape(element_id)}"' if element_id else ""
    return f"<{tag}{id_attr}>{title_with_help(text, guide_key)}</{tag}>"


def block_title_html(text: str, guide_key: str, class_name: str) -> str:
    return f'<div class="{class_name}">{title_with_help(text, guide_key)}</div>'


def page_styles() -> str:
    return """
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: Inter, -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background: var(--page-bg, #f8fafc); color: #334155; line-height: 1.65; padding: 48px 24px; }
            .container { max-width: 820px; margin: 0 auto; }
            h1 { font-size: 32px; font-weight: 700; color: var(--heading-color, #0f172a); margin-bottom: 8px; }
            h2 { font-size: 20px; font-weight: 600; color: #0f172a; margin-top: 48px; margin-bottom: 16px; }
            h3 { font-size: 17px; font-weight: 600; color: #0f172a; margin-top: 28px; margin-bottom: 12px; }
            .title-with-help { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
            .title-label { display: inline; }
            .title-help { position: relative; display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 999px; border: 1px solid #cbd5e1; background: rgba(255,255,255,.9); color: #64748b; font-size: 11px; font-weight: 700; line-height: 1; cursor: help; flex-shrink: 0; }
            .title-help:hover, .title-help:focus-visible { border-color: #94a3b8; color: #334155; outline: none; }
            .title-help-tooltip { position: absolute; left: 50%; top: calc(100% + 10px); transform: translateX(-50%); min-width: 220px; max-width: min(320px, calc(100vw - 48px)); padding: 10px 12px; border-radius: 10px; background: rgba(15, 23, 42, 0.96); color: #f8fafc; font-size: 12px; font-weight: 400; line-height: 1.55; box-shadow: 0 14px 32px rgba(15,23,42,.22); opacity: 0; visibility: hidden; pointer-events: none; transition: opacity .16s ease, visibility .16s ease, transform .16s ease; z-index: 20; text-align: left; }
            .title-help-tooltip::before { content: ""; position: absolute; left: 50%; top: -6px; transform: translateX(-50%) rotate(45deg); width: 12px; height: 12px; background: rgba(15, 23, 42, 0.96); }
            .title-help:hover .title-help-tooltip, .title-help:focus-visible .title-help-tooltip { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
            .subtitle { color: var(--subtitle-color, #64748b); font-size: 15px; margin-bottom: 32px; }
            .nav-toc { display: flex; flex-wrap: wrap; gap: 8px; margin: 24px 0 32px 0; padding: 16px; background: var(--surface-bg, white); border-radius: 8px; border: 1px solid var(--surface-border, #e2e8f0); box-shadow: var(--surface-shadow, none); }
            .nav-toc a { font-size: 12px; color: var(--nav-link-color, #64748b); text-decoration: none; padding: 6px 12px; border-radius: 6px; background: var(--nav-pill-bg, #f1f5f9); }
            .nav-toc a:hover { background: #e2e8f0; color: #334155; }
            .stats-row { display: flex; gap: 24px; margin-bottom: 40px; padding: 20px 0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; }
            .stat { text-align: center; min-width: 96px; }
            .stat-value { font-size: 24px; font-weight: 700; color: #0f172a; }
            .stat-label { font-size: 11px; color: #64748b; text-transform: uppercase; }
            .at-a-glance { background: var(--glance-bg, linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)); border: 1px solid var(--glance-border, #f59e0b); border-radius: 12px; padding: 20px 24px; margin-bottom: 32px; box-shadow: var(--surface-shadow, none); }
            .glance-title { font-size: 16px; font-weight: 700; color: var(--glance-title, #92400e); margin-bottom: 16px; }
            .glance-sections { display: flex; flex-direction: column; gap: 12px; }
            .glance-section { font-size: 14px; color: var(--glance-text, #78350f); line-height: 1.6; }
            .glance-section strong { color: var(--glance-strong, #92400e); }
            .see-more { color: #b45309; text-decoration: none; font-size: 13px; white-space: nowrap; }
            .see-more:hover { text-decoration: underline; }
            .project-areas { display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }
            .project-area { background: var(--surface-bg, white); border: 1px solid var(--surface-border, #e2e8f0); border-radius: 8px; padding: 16px; box-shadow: var(--surface-shadow, none); }
            .area-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; }
            .area-heading { display: flex; align-items: center; gap: 8px; min-width: 0; }
            .area-mode-pill, .card-kicker { display: inline-flex; align-items: center; width: fit-content; padding: 3px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
            .area-mode-pill { background: var(--nav-pill-bg, #eef2ff); color: var(--nav-link-color, #475569); border: 1px solid var(--surface-border, #dbe3ef); flex-shrink: 0; }
            .card-kicker { margin-bottom: 8px; background: var(--nav-pill-bg, #eef2ff); color: var(--nav-link-color, #475569); border: 1px solid var(--surface-border, #dbe3ef); }
            .area-name { font-weight: 600; font-size: 15px; color: #0f172a; }
            .area-count { font-size: 12px; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 4px; }
            .area-desc { font-size: 14px; color: #475569; line-height: 1.5; }
            .comparison-table { width: 100%; border-collapse: collapse; background: var(--surface-bg, white); border: 1px solid var(--surface-border, #e2e8f0); border-radius: 8px; overflow: hidden; margin-bottom: 24px; box-shadow: var(--surface-shadow, none); }
            .comparison-table th, .comparison-table td { padding: 12px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; font-size: 14px; }
            .comparison-table th { background: #f8fafc; color: #0f172a; font-weight: 600; }
            .comparison-table tr:last-child td { border-bottom: none; }
            .narrative { background: var(--surface-bg, white); border: 1px solid var(--surface-border, #e2e8f0); border-radius: 8px; padding: 20px; margin-bottom: 24px; box-shadow: var(--surface-shadow, none); }
            .narrative p { margin-bottom: 12px; font-size: 14px; color: #475569; line-height: 1.7; }
            .key-insight { background: var(--insight-bg, #f0fdf4); border: 1px solid var(--insight-border, #bbf7d0); border-radius: 8px; padding: 12px 16px; margin-top: 12px; font-size: 14px; color: var(--insight-text, #166534); }
            .section-intro { font-size: 14px; color: #64748b; margin-bottom: 16px; }
            .big-wins { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
            .big-win { background: var(--win-bg, #f0fdf4); border: 1px solid var(--win-border, #bbf7d0); border-radius: 8px; padding: 16px; }
            .big-win-title { font-weight: 600; font-size: 15px; color: #166534; margin-bottom: 8px; }
            .big-win-desc { font-size: 14px; color: #15803d; line-height: 1.5; }
            .friction-categories { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
            .friction-category { background: var(--friction-bg, #fef2f2); border: 1px solid var(--friction-border, #fca5a5); border-radius: 8px; padding: 16px; }
            .friction-title { font-weight: 600; font-size: 15px; color: #991b1b; margin-bottom: 6px; }
            .friction-desc { font-size: 13px; color: #7f1d1d; margin-bottom: 10px; }
            .friction-examples { margin: 0 0 0 20px; font-size: 13px; color: #334155; }
            .friction-examples li { margin-bottom: 4px; }
            .features-section, .patterns-section { display: flex; flex-direction: column; gap: 12px; margin: 16px 0; }
            .feature-card { background: var(--feature-bg, #f0fdf4); border: 1px solid var(--feature-border, #86efac); border-radius: 8px; padding: 16px; }
            .pattern-card { background: var(--pattern-bg, #f0f9ff); border: 1px solid var(--pattern-border, #7dd3fc); border-radius: 8px; padding: 16px; }
            .feature-title, .pattern-title { font-weight: 600; font-size: 15px; color: #0f172a; margin-bottom: 6px; }
            .feature-oneliner { font-size: 14px; color: #475569; margin-bottom: 8px; }
            .pattern-summary { font-size: 14px; color: #475569; margin-bottom: 8px; }
            .feature-why, .pattern-detail { font-size: 13px; color: #334155; line-height: 1.5; }
            .feature-starter, .pattern-starter { margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #475569; line-height: 1.5; }
            .copyable-prompt-section { margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0; }
            .copyable-prompt-row { display: flex; align-items: flex-start; gap: 8px; }
            .copyable-prompt { flex: 1; background: #f8fafc; padding: 10px 12px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #334155; border: 1px solid #e2e8f0; white-space: pre-wrap; line-height: 1.5; }
            .prompt-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }
            .copy-btn { background: #e2e8f0; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px; cursor: pointer; color: #475569; flex-shrink: 0; }
            .copy-btn:hover { background: #cbd5e1; }
            .copy-all-btn { background: #2563eb; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-size: 12px; cursor: pointer; font-weight: 500; margin-bottom: 12px; }
            .copy-all-btn:hover { background: #1d4ed8; }
            .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 24px 0; }
            .chart-card { background: var(--surface-bg, white); border: 1px solid var(--surface-border, #e2e8f0); border-radius: 8px; padding: 16px; box-shadow: var(--surface-shadow, none); }
            .chart-title { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 12px; }
            .bar-row { display: flex; align-items: center; margin-bottom: 6px; }
            .bar-label { width: 128px; font-size: 11px; color: #475569; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .bar-track { flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; margin: 0 8px; }
            .bar-fill { height: 100%; border-radius: 3px; }
            .bar-value { width: 40px; font-size: 11px; font-weight: 500; color: #64748b; text-align: right; }
            .empty { color: #94a3b8; font-size: 13px; }
            .horizon-section { display: flex; flex-direction: column; gap: 16px; }
            .horizon-card { background: var(--horizon-bg, linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%)); border: 1px solid var(--horizon-border, #c4b5fd); border-radius: 8px; padding: 16px; }
            .horizon-title { font-weight: 600; font-size: 15px; color: #5b21b6; margin-bottom: 8px; }
            .horizon-possible { font-size: 14px; color: #334155; line-height: 1.5; }
            .fun-ending { background: var(--ending-bg, linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)); border: 1px solid var(--ending-border, #fbbf24); border-radius: 12px; padding: 24px; margin-top: 40px; text-align: center; box-shadow: var(--surface-shadow, none); }
            .fun-headline { font-size: 18px; font-weight: 600; color: var(--ending-headline, #78350f); margin-bottom: 8px; }
            .fun-detail { font-size: 14px; color: var(--ending-detail, #92400e); }
            .scenario-card { background: var(--surface-bg, white); border: 1px solid var(--surface-border-strong, #cbd5e1); border-radius: 12px; padding: 18px 20px; margin-bottom: 28px; box-shadow: var(--surface-shadow, none); }
            .scenario-title { font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 10px; }
            .scenario-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
            .scenario-item { background: var(--nav-pill-bg, #f8fafc); border: 1px solid var(--surface-border, #e2e8f0); border-radius: 8px; padding: 12px; }
            .scenario-item strong { display: block; font-size: 13px; color: #0f172a; margin-bottom: 6px; }
            .scenario-item span { font-size: 13px; color: #475569; line-height: 1.5; display: block; }
            details.platform-details { margin: 20px 0; }
            details.platform-details > summary { list-style: none; cursor: pointer; background: var(--surface-bg, white); border: 1px solid var(--surface-border-strong, #cbd5e1); border-radius: 12px; padding: 16px 18px; font-weight: 600; color: #0f172a; box-shadow: var(--surface-shadow, none); }
            details.platform-details > summary::-webkit-details-marker { display: none; }
            .platform-summary-sub { display: block; margin-top: 6px; font-size: 13px; font-weight: 400; color: #64748b; }
            .platform-details-body { margin-top: 14px; }
            .decision-grid, .quality-grid, .leaderboard-grid, .prompt-library-grid, .matrix-grid, .drilldown-grid, .snapshot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0 24px; }
            .decision-card, .quality-card, .leaderboard-card, .prompt-card, .matrix-card, .drilldown-card, .snapshot-card { background: var(--surface-bg, white); border: 1px solid var(--surface-border, #e2e8f0); border-radius: 10px; padding: 16px; box-shadow: var(--surface-shadow, none); }
            .decision-card strong, .quality-card strong, .leaderboard-card strong, .prompt-card strong, .matrix-card strong, .drilldown-card strong, .snapshot-card strong { display: block; color: #0f172a; margin-bottom: 8px; font-size: 14px; }
            .decision-card span, .quality-card span, .leaderboard-card span, .prompt-card span, .matrix-card span, .drilldown-card span, .snapshot-card span { font-size: 13px; color: #475569; line-height: 1.5; display: block; }
            .mini-list { margin: 8px 0 0 18px; color: #475569; font-size: 13px; }
            .mini-list li { margin-bottom: 4px; }
            .score-badge { display: inline-block; margin-top: 4px; padding: 2px 8px; border-radius: 999px; background: #dbeafe; color: #1d4ed8; font-size: 12px; font-weight: 600; }
            .trend-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0 24px; }
            .trend-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }
            .trend-card-title { font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 10px; }
            .trend-card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 10px; }
            .trend-window-switcher { display: inline-flex; gap: 6px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 999px; padding: 4px; }
            .trend-window-btn { border: none; background: transparent; color: #64748b; border-radius: 999px; padding: 4px 10px; font-size: 11px; font-weight: 600; cursor: pointer; }
            .trend-window-btn.is-active { background: #0f172a; color: white; }
            .trend-window-panel[hidden] { display: none; }
            .trend-summary-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin-bottom: 10px; }
            .trend-summary-pill { background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; min-height: 68px; box-shadow: inset 0 1px 0 rgba(255,255,255,.8); }
            .trend-summary-pill.trend-pill-metric { border-top: 3px solid var(--pill-accent, #2563eb); background: linear-gradient(180deg, rgba(255,255,255,.98) 0%, color-mix(in srgb, var(--pill-accent, #2563eb) 8%, #ffffff) 100%); }
            .trend-summary-pill.delta-up { border-color: #86efac; background: linear-gradient(180deg, #f7fff8 0%, #ecfdf3 100%); color: #166534; }
            .trend-summary-pill.delta-down { border-color: #fecaca; background: linear-gradient(180deg, #fff8f8 0%, #fef2f2 100%); color: #991b1b; }
            .trend-summary-pill.delta-flat { border-color: #cbd5e1; background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); color: #475569; }
            .trend-pill-label { display: block; font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }
            .trend-pill-value { display: block; font-size: 16px; font-weight: 700; line-height: 1.15; color: #0f172a; }
            .trend-pill-subvalue { display: block; margin-top: 4px; font-size: 11px; line-height: 1.3; color: inherit; }
            .trend-window-meta { margin-top: 10px; font-size: 12px; color: #64748b; }
            .trend-legend { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 10px; }
            .trend-legend-item { font-size: 12px; color: #64748b; }
            .legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
            .trend-svg { width: 100%; height: 96px; }
            .trend-point { cursor: pointer; }
            .trend-grid-line { stroke: #e2e8f0; stroke-width: 1; stroke-dasharray: 2 3; }
            .trend-axis-label, .trend-annotation { font-size: 10px; fill: #64748b; }
            .trend-latest-label { font-size: 10px; font-weight: 600; }
            .matrix-table td, .matrix-table th { font-size: 13px; }
            .section-divider { margin: 32px 0 16px; border-top: 1px solid #e2e8f0; }
            body.report-mode-all, .platform-mode-all { --page-bg:#f6f8fc; --heading-color:#0f172a; --subtitle-color:#64748b; --surface-bg:#ffffff; --surface-border:#dbe3ef; --surface-border-strong:#cbd5e1; --surface-shadow:0 10px 28px rgba(15,23,42,.04); --nav-pill-bg:#eef2ff; --nav-link-color:#475569; --glance-bg:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%); --glance-border:#f59e0b; --glance-title:#92400e; --glance-text:#78350f; --glance-strong:#92400e; --win-bg:#f8fbff; --win-border:#bfdbfe; --feature-bg:#f0fdf4; --feature-border:#86efac; --pattern-bg:#eef4ff; --pattern-border:#bfdbfe; --horizon-bg:linear-gradient(135deg,#faf5ff 0%,#eef2ff 100%); --horizon-border:#c4b5fd; --ending-bg:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%); --ending-border:#fbbf24; --ending-headline:#78350f; --ending-detail:#92400e; --insight-bg:#eef4ff; --insight-border:#bfdbfe; --insight-text:#1d4ed8; --friction-bg:#fff7ed; --friction-border:#fdba74; }
            body.report-mode-all .trend-card, .platform-mode-all .trend-card { background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); border-color: #cbd5e1; }
            body.report-mode-all .trend-window-switcher, .platform-mode-all .trend-window-switcher { background: #eef2ff; border-color: #c7d2fe; }
            body.report-mode-all .trend-window-btn.is-active, .platform-mode-all .trend-window-btn.is-active { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); }
            body.report-mode-all .trend-summary-pill.delta-flat, .platform-mode-all .trend-summary-pill.delta-flat { background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%); border-color: #bfdbfe; color: #1d4ed8; }
            body.report-mode-all .trend-pill-label, .platform-mode-all .trend-pill-label { color: #475569; }
            body.report-mode-claude, .platform-mode-claude { --page-bg:radial-gradient(circle at top,#eff6ff 0%,#f8fbff 32%,#eef4ff 100%); --heading-color:#1d4ed8; --subtitle-color:#1e40af; --surface-bg:#ffffff; --surface-border:#bfdbfe; --surface-border-strong:#93c5fd; --surface-shadow:0 12px 30px rgba(37,99,235,.08); --nav-pill-bg:#eff6ff; --nav-link-color:#1e40af; --glance-bg:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 100%); --glance-border:#60a5fa; --glance-title:#1d4ed8; --glance-text:#1e3a8a; --glance-strong:#1d4ed8; --win-bg:#eff6ff; --win-border:#bfdbfe; --feature-bg:#f0f7ff; --feature-border:#93c5fd; --pattern-bg:#eef4ff; --pattern-border:#bfdbfe; --horizon-bg:linear-gradient(135deg,#eff6ff 0%,#e0ecff 100%); --horizon-border:#93c5fd; --ending-bg:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 100%); --ending-border:#60a5fa; --ending-headline:#1e3a8a; --ending-detail:#1d4ed8; --insight-bg:#eff6ff; --insight-border:#93c5fd; --insight-text:#1e3a8a; --friction-bg:#fff7ed; --friction-border:#fdba74; }
            body.report-mode-claude .project-area, .platform-mode-claude .project-area,
            body.report-mode-claude .decision-card, .platform-mode-claude .decision-card,
            body.report-mode-claude .quality-card, .platform-mode-claude .quality-card,
            body.report-mode-claude .leaderboard-card, .platform-mode-claude .leaderboard-card,
            body.report-mode-claude .prompt-card, .platform-mode-claude .prompt-card,
            body.report-mode-claude .drilldown-card, .platform-mode-claude .drilldown-card,
            body.report-mode-claude .snapshot-card, .platform-mode-claude .snapshot-card,
            body.report-mode-claude .narrative, .platform-mode-claude .narrative { border-left: 4px solid #60a5fa; }
            body.report-mode-claude .big-win, .platform-mode-claude .big-win,
            body.report-mode-claude .feature-card, .platform-mode-claude .feature-card,
            body.report-mode-claude .pattern-card, .platform-mode-claude .pattern-card,
            body.report-mode-claude .horizon-card, .platform-mode-claude .horizon-card { position: relative; overflow: hidden; }
            body.report-mode-claude .big-win::before, .platform-mode-claude .big-win::before,
            body.report-mode-claude .feature-card::before, .platform-mode-claude .feature-card::before,
            body.report-mode-claude .pattern-card::before, .platform-mode-claude .pattern-card::before,
            body.report-mode-claude .horizon-card::before, .platform-mode-claude .horizon-card::before { content:""; position:absolute; inset:0 auto 0 0; width:4px; background:linear-gradient(180deg,#60a5fa 0%,#2563eb 100%); }
            body.report-mode-claude .card-kicker, .platform-mode-claude .card-kicker,
            body.report-mode-claude .area-mode-pill, .platform-mode-claude .area-mode-pill { background:#eff6ff; color:#1d4ed8; border-color:#93c5fd; }
            body.report-mode-claude .nav-toc a:hover, .platform-mode-claude .nav-toc a:hover { background:#dbeafe; color:#1d4ed8; }
            body.report-mode-claude .trend-card, .platform-mode-claude .trend-card { background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%); border-color: #bfdbfe; box-shadow: 0 10px 30px rgba(37,99,235,.06); }
            body.report-mode-claude .trend-window-switcher, .platform-mode-claude .trend-window-switcher { background: #eff6ff; border-color: #bfdbfe; }
            body.report-mode-claude .trend-window-btn, .platform-mode-claude .trend-window-btn { color: #1e40af; }
            body.report-mode-claude .trend-window-btn.is-active, .platform-mode-claude .trend-window-btn.is-active { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; }
            body.report-mode-claude .trend-summary-pill.delta-flat, .platform-mode-claude .trend-summary-pill.delta-flat { background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%); border-color: #bfdbfe; color: #1d4ed8; }
            body.report-mode-claude .trend-pill-label, .platform-mode-claude .trend-pill-label { color: #1d4ed8; }
            body.report-mode-codex, .platform-mode-codex { --page-bg:radial-gradient(circle at top,#ecfdf5 0%,#f7fcf8 34%,#eefbf1 100%); --heading-color:#15803d; --subtitle-color:#166534; --surface-bg:#ffffff; --surface-border:#bbf7d0; --surface-border-strong:#86efac; --surface-shadow:0 12px 30px rgba(22,163,74,.08); --nav-pill-bg:#f0fdf4; --nav-link-color:#166534; --glance-bg:linear-gradient(135deg,#dcfce7 0%,#bbf7d0 100%); --glance-border:#4ade80; --glance-title:#15803d; --glance-text:#166534; --glance-strong:#15803d; --win-bg:#f0fdf4; --win-border:#86efac; --feature-bg:#effdf4; --feature-border:#86efac; --pattern-bg:#edfdf3; --pattern-border:#bbf7d0; --horizon-bg:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%); --horizon-border:#86efac; --ending-bg:linear-gradient(135deg,#dcfce7 0%,#bbf7d0 100%); --ending-border:#4ade80; --ending-headline:#166534; --ending-detail:#15803d; --insight-bg:#effdf4; --insight-border:#86efac; --insight-text:#166534; --friction-bg:#fefce8; --friction-border:#facc15; }
            body.report-mode-codex .project-area, .platform-mode-codex .project-area,
            body.report-mode-codex .decision-card, .platform-mode-codex .decision-card,
            body.report-mode-codex .quality-card, .platform-mode-codex .quality-card,
            body.report-mode-codex .leaderboard-card, .platform-mode-codex .leaderboard-card,
            body.report-mode-codex .prompt-card, .platform-mode-codex .prompt-card,
            body.report-mode-codex .drilldown-card, .platform-mode-codex .drilldown-card,
            body.report-mode-codex .snapshot-card, .platform-mode-codex .snapshot-card,
            body.report-mode-codex .narrative, .platform-mode-codex .narrative { border-left: 4px solid #22c55e; }
            body.report-mode-codex .big-win, .platform-mode-codex .big-win,
            body.report-mode-codex .feature-card, .platform-mode-codex .feature-card,
            body.report-mode-codex .pattern-card, .platform-mode-codex .pattern-card,
            body.report-mode-codex .horizon-card, .platform-mode-codex .horizon-card { position: relative; box-shadow: 0 8px 24px rgba(22,163,74,.06); }
            body.report-mode-codex .big-win::before, .platform-mode-codex .big-win::before,
            body.report-mode-codex .feature-card::before, .platform-mode-codex .feature-card::before,
            body.report-mode-codex .pattern-card::before, .platform-mode-codex .pattern-card::before,
            body.report-mode-codex .horizon-card::before, .platform-mode-codex .horizon-card::before { content:""; display:block; height:5px; margin:-16px -16px 12px -16px; background:linear-gradient(90deg,#22c55e 0%,#15803d 100%); border-radius:8px 8px 0 0; }
            body.report-mode-codex .card-kicker, .platform-mode-codex .card-kicker,
            body.report-mode-codex .area-mode-pill, .platform-mode-codex .area-mode-pill { background:#f0fdf4; color:#15803d; border-color:#86efac; }
            body.report-mode-codex .nav-toc a:hover, .platform-mode-codex .nav-toc a:hover { background:#dcfce7; color:#15803d; }
            body.report-mode-codex .trend-card, .platform-mode-codex .trend-card { background: linear-gradient(180deg, #ffffff 0%, #f7fcf8 100%); border-color: #bbf7d0; box-shadow: 0 10px 30px rgba(22,163,74,.06); }
            body.report-mode-codex .trend-window-switcher, .platform-mode-codex .trend-window-switcher { background: #f0fdf4; border-color: #86efac; }
            body.report-mode-codex .trend-window-btn, .platform-mode-codex .trend-window-btn { color: #166534; }
            body.report-mode-codex .trend-window-btn.is-active, .platform-mode-codex .trend-window-btn.is-active { background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: #ffffff; }
            body.report-mode-codex .trend-summary-pill.delta-flat, .platform-mode-codex .trend-summary-pill.delta-flat { background: linear-gradient(180deg, #f7fff8 0%, #eefbf1 100%); border-color: #86efac; color: #166534; }
            body.report-mode-codex .trend-pill-label, .platform-mode-codex .trend-pill-label { color: #15803d; }
            @media (max-width: 640px) { .charts-row, .decision-grid, .quality-grid, .leaderboard-grid, .prompt-library-grid, .matrix-grid, .drilldown-grid, .snapshot-grid, .trend-grid { grid-template-columns: 1fr; } .stats-row { justify-content: center; } .scenario-grid { grid-template-columns: 1fr; } }
    """


def page_scripts() -> str:
    return """
            function copyText(button) {
              const code = button.parentElement.querySelector('.copyable-prompt');
              const text = code.innerText;
              navigator.clipboard.writeText(text).then(() => {
                const original = button.innerText;
                button.innerText = 'Copied';
                setTimeout(() => { button.innerText = original; }, 1200);
              });
            }
            function copyAllPrompts(sectionClass) {
              const section = document.querySelector('.' + sectionClass);
              const prompts = Array.from(section.querySelectorAll('.copyable-prompt')).map(node => node.innerText.trim()).join('\\n\\n');
              navigator.clipboard.writeText(prompts);
            }
            function switchTrendWindow(button, windowKey) {
              const card = button.closest('.trend-card');
              if (!card) return;
              card.querySelectorAll('.trend-window-btn').forEach(node => node.classList.remove('is-active'));
              button.classList.add('is-active');
              card.querySelectorAll('.trend-window-panel').forEach(panel => {
                panel.hidden = panel.dataset.window !== windowKey;
              });
            }
    """


def _point_geometry(
    points: list[dict],
    width: int,
    height: int,
    padding_left: int,
    padding_right: int,
    padding_top: int,
    padding_bottom: int,
    min_value: float,
    max_value: float,
) -> list[dict]:
    if not points:
        return []
    span = max(max_value - min_value, 1)
    coords = []
    usable_w = width - padding_left - padding_right
    usable_h = height - padding_top - padding_bottom
    for index, point in enumerate(points):
        x = padding_left + (usable_w * index / max(len(points) - 1, 1))
        y = padding_top + usable_h - ((point["value"] - min_value) / span * usable_h)
        coords.append(
            {
                "x": round(x, 2),
                "y": round(y, 2),
                "label": point.get("label", ""),
                "full_label": point.get("full_label", point.get("label", "")),
                "value": point["value"],
            }
        )
    return coords


def sparkline_svg(series: list[dict], width: int = 320, height: int = 96) -> str:
    padding_left = 32
    padding_right = 12
    padding_top = 12
    padding_bottom = 12
    all_values = [point["value"] for item in series for point in item["points"]]
    if not all_values:
        return (
            f'<svg class="trend-svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none">'
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" class="trend-axis-label">暂无趋势数据</text>'
            "</svg>"
        )
    min_value = min(all_values)
    max_value = max(all_values)
    mid_value = min_value + (max_value - min_value) / 2
    axis_labels = [
        (padding_top, max_value),
        ((height - padding_bottom + padding_top) / 2, mid_value),
        (height - padding_bottom, min_value),
    ]
    grid_lines = []
    for y, value in axis_labels:
        grid_lines.append(
            f'<line class="trend-grid-line" x1="{padding_left}" y1="{round(y, 2)}" x2="{width - padding_right}" y2="{round(y, 2)}" />'
        )
        grid_lines.append(
            f'<text class="trend-axis-label" x="{padding_left - 6}" y="{round(y + 3, 2)}" text-anchor="end">{html.escape(format_metric(value))}</text>'
        )
    polylines = []
    markers = []
    annotations = []
    for item in series:
        point_geometry = _point_geometry(
            item["points"],
            width,
            height,
            padding_left,
            padding_right,
            padding_top,
            padding_bottom,
            min_value,
            max_value,
        )
        if not point_geometry:
            continue
        coords = " ".join(f'{point["x"]},{point["y"]}' for point in point_geometry)
        polylines.append(
            f'<polyline fill="none" stroke="{item["color"]}" stroke-width="2.5" points="{coords}" />'
        )
        peak_point = max(point_geometry, key=lambda point: point["value"])
        label_y = max(peak_point["y"] - 8, padding_top + 10)
        annotations.append(
            f'<text class="trend-annotation" x="{peak_point["x"]}" y="{label_y}" text-anchor="middle" fill="{item["color"]}">'
            f'{html.escape(item["name"])} peak {format_metric(peak_point["value"])}'
            "</text>"
        )
        latest_point = point_geometry[-1]
        latest_label_y = latest_point["y"] + 14 if latest_point["y"] <= padding_top + 18 else latest_point["y"] - 8
        latest_label_x = latest_point["x"] - 4
        annotations.append(
            f'<text class="trend-latest-label" x="{latest_label_x}" y="{round(latest_label_y, 2)}" text-anchor="end" fill="{item["color"]}">'
            f'Latest {format_metric(latest_point["value"])}'
            "</text>"
        )
        for point in point_geometry:
            markers.append(
                f'<circle class="trend-point" cx="{point["x"]}" cy="{point["y"]}" r="3.5" fill="{item["color"]}">'
                f'<title>{html.escape(item["name"])} | {html.escape(point["full_label"])} | {html.escape(format_metric(point["value"]))}</title>'
                "</circle>"
            )
    return (
        f'<svg class="trend-svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none">'
        + "".join(grid_lines)
        + f'<line x1="{padding_left}" y1="{height-padding_bottom}" x2="{width-padding_right}" y2="{height-padding_bottom}" stroke="#cbd5e1" stroke-width="1" />'
        + "".join(polylines)
        + "".join(markers)
        + "".join(annotations)
        + "</svg>"
    )
