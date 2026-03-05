from __future__ import annotations

from ..models import AnalyzedData, NarrativeBundle, ReportMeta
from .shared import achieved_counts, build_bundle, friction_text, top_domains_text


def _fmt_top(items: list, n: int = 3) -> str:
    if not items:
        return "暂无"
    return ", ".join(f"{name}({value})" for name, value in items[:n])


def _session_tone(sessions: int) -> str:
    if sessions == 0:
        return "这块得直说：Claude 本期几乎没上场，分析层是空档状态。"
    if sessions < 3:
        return "有在用，但投入偏少，分析层还没形成稳定惯性。"
    return "分析层参与度不错，这段可以夸：你在收敛问题上是有持续投入的。"


def _wins_session_tone(sessions: int) -> str:
    if sessions == 0:
        return "本期样本较少，但已具备后续补样和对照分析的基础。"
    if sessions < 3:
        return "已有连续样本，后续继续补样即可放大结论可信度。"
    return "分析层参与度稳定，收敛质量有持续投入。"


def _outcome_tone(achieved: int, not_achieved: int) -> str:
    total = achieved + not_achieved
    if total <= 0:
        return "结果标注还不完整，复盘证据偏薄，建议先补齐 outcome。"
    ratio = achieved / total
    if ratio >= 0.7:
        return "结果面值得肯定：完成率在可夸区间。"
    if ratio >= 0.4:
        return "结果面中规中矩：有交付，但稳定性还不够硬。"
    return "这块要吐槽：未达成占比偏高，说明分析质量没有稳定转化为结果。"


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    claude = data.comparison.get("claude_code", {})
    sessions = claude.get("sessions", 0)
    avg_min = claude.get("avg_duration_min", 0)
    avg_msg = claude.get("avg_user_messages", 0)
    top_domains = top_domains_text(data)
    top_tools = _fmt_top(claude.get("top_tools", []))
    top_projects = _fmt_top(claude.get("top_projects", []))
    friction_line = friction_text(data, n=3, sep=", ")
    achieved, not_achieved = achieved_counts(data)
    session_tone = _session_tone(sessions)
    outcome_tone = _outcome_tone(achieved, not_achieved)

    usage_narrative = {
        "p1": f"最近窗口中 Claude 有 {sessions} 次会话，平均 {avg_min} 分钟、每次会话 {avg_msg} 条用户消息。",
        "p2": f"任务主要集中在 {top_domains}。工具分布 Top 为 {top_tools}，项目分布 Top 为 {top_projects}。",
        "p3": f"Outcome 汇总：fully/mostly={achieved}，partially/not={not_achieved}。主要摩擦：{friction_line}。{outcome_tone}",
        "key": f"{session_tone} 重点改进是先证据后结论，减少偏航摩擦。",
    }

    wins = [
        {"title": "分析层投入", "desc": f"{sessions} 次会话，平均时长 {avg_min} 分钟。{_wins_session_tone(sessions)}"},
        {"title": "任务聚焦度", "desc": f"Top domains: {top_domains}；Top projects: {top_projects}。这块聚焦做得比较清楚。"},
        {"title": "结果可复盘性", "desc": f"Outcome：achieved={achieved}，not_achieved={not_achieved}。结果数据已形成基础对照，便于持续优化。"},
    ]

    top_sessions = data.friction_sessions[:3]
    friction_cards = [
        {
            "title": "高频摩擦模式",
            "desc": f"当前主要摩擦为 {friction_line}。建议将其直接转为输入约束。",
            "examples": [
                (
                    f"{item['project']} | {item['first_prompt'] or '无标题'} | "
                    f"摩擦分 {item['score']} | {(item['friction_detail'] or item['summary'] or '')[:120]}"
                )
                for item in top_sessions
            ] or ["暂无高摩擦样本"],
        },
        {
            "title": "先证据后判断",
            "desc": "调试与评审场景中，若先给结论再找证据，返工成本会明显上升。",
            "examples": [
                "先复述目标、约束、禁止项，再进入分析。",
                "强制输出证据链后再给修复建议。",
            ],
        },
    ]

    feature_cards = [
        {
            "title": "分析起手模板",
            "summary": "固定目标/约束/证据/验证四段式。",
            "detail": "先填完整四段再给结论，可直接降低误解与偏航。",
            "starter": "先在调试任务里落地，随后扩展到 review。",
            "prompt": "请先按四段式输出：目标、约束、证据、验证。四段未完成前不要给最终结论。",
        },
        {
            "title": "Review 结构化输出",
            "summary": "统一结论、证据、风险、建议、验证。",
            "detail": "结构稳定后，交接给执行层更高效。",
            "starter": "所有 review 默认使用五段式。",
            "prompt": "请按五段式输出：结论、证据、风险、建议、验证，不要自由组织结构。",
        },
        {
            "title": "摩擦模式前置约束",
            "summary": "把高频摩擦直接写进提示约束。",
            "detail": "比泛化要求“更严谨”更可执行。",
            "starter": "先为 wrong_approach 增加“先证据后判断”门禁。",
            "prompt": "先复述目标与约束；若信息不足，仅列缺失项和影响，不要自行假设。",
        },
    ]

    pattern_cards = [
        {
            "title": "先收敛后执行",
            "summary": "Claude 先产出执行清单，再交接执行层。",
            "detail": "分析层与执行层分离后，整体返工率更低。",
            "starter": "先输出目标、边界、相关文件、验证命令。",
            "prompt": "先输出执行清单：目标、边界、相关文件、验证命令。确认后再进入方案。",
        },
        {
            "title": "调试证据链模板",
            "summary": "日志/调用链/相关文件先行。",
            "detail": "证据先行能避免大多数猜测型偏航。",
            "starter": "调试任务统一模板化。",
            "prompt": "不要猜。先给日志位置、调用链、相关文件，再给根因和最小修复。",
        },
        {
            "title": "结论门禁",
            "summary": "没有验证路径不允许输出最终建议。",
            "detail": "确保建议可执行、可验证。",
            "starter": "每条建议都附验证命令。",
            "prompt": "每条建议都必须附验证步骤或命令，否则标记为待补证据。",
        },
    ]

    horizon_cards = [
        {"title": "摩擦到规则闭环", "desc": "将高频摩擦持续写回模板约束，形成自动纠偏闭环。"},
        {"title": "结构化输出默认化", "desc": "统一输出协议后，跨工具交接与报告解释力会明显提升。"},
        {"title": "分析质量追踪", "desc": "按周追踪 achieved/not_achieved 与摩擦变化，持续优化提示模板。"},
    ]

    return build_bundle(
        glance_sections=[
            f"<strong>当前有效：</strong> Claude 本期 {sessions} 次会话，分析层角色稳定。 <a href=\"#section-wins\" class=\"see-more\">查看亮点 →</a>",
            f"<strong>当前阻碍：</strong> 主要摩擦是 {friction_line}。 <a href=\"#section-friction\" class=\"see-more\">查看问题 →</a>",
            f"<strong>短期可做：</strong> 先证据后结论 + 五段式输出。 <a href=\"#section-features\" class=\"see-more\">查看可直接落地动作 →</a>",
            f"<strong>中长期方向：</strong> 把摩擦模式持续反写进模板规则。 <a href=\"#section-horizon\" class=\"see-more\">查看后续规划 →</a>",
        ],
        work_intro=f"当前 Claude 工作集中在 {top_domains}，重点是判断质量与约束收敛质量。",
        usage_narrative=usage_narrative,
        wins_intro="以下亮点由本次统计值自动生成。",
        wins=wins,
        friction_intro="以下风险与建议由摩擦与 outcome 数据自动生成。",
        friction_cards=friction_cards,
        feature_intro="以下动作可直接用于下一次会话。",
        feature_cards=feature_cards,
        pattern_intro="以下模式用于稳定分析层输出质量。",
        pattern_cards=pattern_cards,
        horizon_intro="下一阶段建议围绕模板闭环与质量追踪。",
        horizon_cards=horizon_cards,
        ending_headline="Claude 当前角色是高约束分析层。",
        ending_detail="最有效的优化不是增加描述长度，而是提升证据链与输出结构稳定性。",
    )
