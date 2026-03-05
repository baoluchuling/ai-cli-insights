from __future__ import annotations

from ..models import AnalyzedData, NarrativeBundle, ReportMeta
from .shared import achieved_counts, build_bundle, friction_text, success_domains_text, top_domains_text


def _fmt_top(items: list, n: int = 3) -> str:
    if not items:
        return "暂无"
    return ", ".join(f"{name}({value})" for name, value in items[:n])


def _split_tone(c_sessions: int, x_sessions: int) -> str:
    if c_sessions == 0 or x_sessions == 0:
        return "这块要吐槽：双工具分工是单腿走路，另一侧样本缺失会直接拉低判断可信度。"
    gap = abs(c_sessions - x_sessions)
    if gap <= max(2, int((c_sessions + x_sessions) * 0.25)):
        return "这块值得夸：双侧参与度平衡，分工结构是健康的。"
    return "分工方向是对的，但负载明显偏斜，建议把轻侧角色拉回到稳定节奏。"


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    c_sessions = claude.get("sessions", 0)
    x_sessions = codex.get("sessions", 0)
    c_avg_min = claude.get("avg_duration_min", 0)
    x_avg_min = codex.get("avg_duration_min", 0)
    c_avg_msg = claude.get("avg_user_messages", 0)
    x_avg_msg = codex.get("avg_user_messages", 0)
    top_domains = top_domains_text(data)
    efficient_domains = success_domains_text(data)
    friction_line = friction_text(data, n=3, sep=", ")
    achieved, not_achieved = achieved_counts(data)
    claude_tools = _fmt_top(claude.get("top_tools", []))
    codex_tools = _fmt_top(codex.get("top_tools", []))
    claude_projects = _fmt_top(claude.get("top_projects", []))
    codex_projects = _fmt_top(codex.get("top_projects", []))
    split_tone = _split_tone(c_sessions, x_sessions)

    usage_narrative = {
        "p1": (
            f"本期 Claude {c_sessions} 次会话，平均 {c_avg_min} 分钟、{c_avg_msg} 条消息；"
            f"Codex {x_sessions} 次会话，平均 {x_avg_min} 分钟、{x_avg_msg} 条消息。"
        ),
        "p2": (
            f"跨工具任务主要集中在 {top_domains}。Claude Top tools: {claude_tools}；"
            f"Codex Top tools: {codex_tools}。"
        ),
        "p3": (
            f"Outcome 汇总：fully/mostly={achieved}，partially/not={not_achieved}；"
            f"当前主要摩擦：{friction_line}。{split_tone}"
        ),
        "key": f"{split_tone} 优化重点是交接质量和验证门禁。",
    }

    wins = [
        {
            "title": "分工清晰",
            "desc": (
                f"Claude 与 Codex 的时长/消息密度差异明显。"
                + ("双侧都有稳定样本，跨工具协作基础已经形成。" if c_sessions > 0 and x_sessions > 0 else "当前已有有效样本，协作框架可继续扩展。")
            ),
        },
        {
            "title": "任务聚焦",
            "desc": f"Top domains: {top_domains}；高效样本集中在 {efficient_domains}。这块可以夸，说明你在把精力投到高价值区。",
        },
        {
            "title": "协作基础稳定",
            "desc": f"Claude Top projects: {claude_projects}；Codex Top projects: {codex_projects}。项目分布可读性不错，便于继续沉淀协作模板。",
        },
    ]

    friction_cards = [
        {
            "title": "分析到执行交接损耗",
            "desc": "当分析结论未结构化为执行清单时，执行层会产生重复澄清和返工。",
            "examples": [
                "交接时固定四项：目标、边界、相关文件、验证命令。",
                "执行开始前先确认禁止项与结束条件。",
            ],
        },
        {
            "title": "高频摩擦模式",
            "desc": f"当前主要摩擦：{friction_line}。建议把这些模式直接反写进提示模板。",
            "examples": [
                "先证据后结论，减少猜测型偏航。",
                "每批改动后验证前移，避免末端集中返工。",
            ],
        },
    ]

    feature_cards = [
        {
            "title": "交接模板",
            "summary": "先输出执行清单，再交给下一步工具。",
            "detail": "可降低跨工具信息损耗。",
            "starter": "固定四项清单模板。",
            "prompt": "请先输出执行清单：目标、边界、相关文件、验证命令。确认后再进入执行。",
        },
        {
            "title": "阶段门禁",
            "summary": "每批改动后立即做验证。",
            "detail": "把返工前移到阶段内。",
            "starter": "从 analyze + 关键检查开始。",
            "prompt": "每批改动后先执行验证门禁，通过后再继续下一批。",
        },
        {
            "title": "摩擦约束模板",
            "summary": "将高频摩擦模式转为固定输入约束。",
            "detail": "可持续降低偏航概率。",
            "starter": "先覆盖 top2 摩擦模式。",
            "prompt": "先复述目标与约束；若信息不足，仅列缺失项，不自行假设。",
        },
    ]

    pattern_cards = [
        {
            "title": "双层协作默认化",
            "summary": "分析层与执行层职责分离。",
            "detail": "分离后会话更短、返工更少、回放更清晰。",
            "starter": "复杂任务默认两阶段：收敛 -> 执行。",
            "prompt": "先收敛目标与边界，再按执行计划推进并阶段总结。",
        },
        {
            "title": "阶段总结协议",
            "summary": "把阶段回放作为标准交付。",
            "detail": "便于跨工具接力与后续复盘。",
            "starter": "每阶段固定四项输出。",
            "prompt": "每阶段输出：已完成、已验证、剩余风险、下一步。",
        },
        {
            "title": "项目边界显式化",
            "summary": "多 repo 任务必须明确边界。",
            "detail": "边界越清晰，归因越准确。",
            "starter": "任务开头声明 repo 与模块。",
            "prompt": "请先声明目标 repo、模块范围、验证命令，再开始执行。",
        },
    ]

    horizon_cards = [
        {"title": "跨工具质量闭环", "desc": "统一记录两侧 outcome/friction，建立可比质量追踪。"},
        {"title": "交接协议自动化", "desc": "将交接清单与阶段总结做成默认模板。"},
        {"title": "周度对比运营", "desc": "持续比较分工效率、摩擦趋势与返工成本。"},
    ]

    return build_bundle(
        glance_sections=[
            f"<strong>当前有效：</strong> 双工具分工稳定，Claude({c_sessions}) + Codex({x_sessions}) 协作清晰。 <a href=\"#section-wins\" class=\"see-more\">查看亮点 →</a>",
            f"<strong>当前阻碍：</strong> 当前主要摩擦是 {friction_line}。 <a href=\"#section-friction\" class=\"see-more\">查看问题 →</a>",
            f"<strong>短期可做：</strong> 固化交接模板和阶段门禁。 <a href=\"#section-features\" class=\"see-more\">查看可直接落地动作 →</a>",
            f"<strong>中长期方向：</strong> 建立跨工具质量闭环。 <a href=\"#section-horizon\" class=\"see-more\">查看后续规划 →</a>",
        ],
        work_intro=f"当前工作集中在 {top_domains}，跨工具价值主要体现在分析-执行协作效率。",
        usage_narrative=usage_narrative,
        wins_intro="以下亮点由本次统计值自动生成。",
        wins=wins,
        friction_intro="以下风险与建议由本次摩擦/结果数据自动生成。",
        friction_cards=friction_cards,
        feature_intro="以下动作可直接用于下一次跨工具任务。",
        feature_cards=feature_cards,
        pattern_intro="以下模式用于提升跨工具协作稳定性。",
        pattern_cards=pattern_cards,
        horizon_intro="下一阶段建议围绕模板自动化与质量闭环。",
        horizon_cards=horizon_cards,
        ending_headline="跨工具协作已成型，下一步是质量运营化。",
        ending_detail="把交接与验证协议标准化后，报告会从“描述现状”升级为“持续优化系统”。",
    )
