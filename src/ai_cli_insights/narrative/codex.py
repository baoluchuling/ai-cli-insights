from __future__ import annotations

from ..models import AnalyzedData, NarrativeBundle, ReportMeta
from .shared import build_bundle, codex_archetype_line, top_domains_text


def _fmt_top(items: list, n: int = 3) -> str:
    if not items:
        return "暂无"
    return ", ".join(f"{name}({value})" for name, value in items[:n])


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    codex = data.comparison.get("codex_cli", {})
    sessions = codex.get("sessions", 0)
    avg_min = codex.get("avg_duration_min", 0)
    avg_msg = codex.get("avg_user_messages", 0)
    top_domains = top_domains_text(data)
    archetype = codex_archetype_line(data)
    top_tools = _fmt_top(codex.get("top_tools", []))
    top_projects = _fmt_top(codex.get("top_projects", []))
    long_chain = len([s for s in data.sessions if s.get("active_minutes", 0) >= 120])

    usage_narrative = {
        "p1": f"最近窗口中 Codex 有 {sessions} 个 sessions，平均 {avg_min} 分钟、每个 session {avg_msg} 条用户消息。",
        "p2": f"任务主要集中在 {top_domains}。工具分布 Top 为 {top_tools}，项目分布 Top 为 {top_projects}。",
        "p3": f"执行画像为 {archetype}。其中长链路会话（active>=120 分钟）共 {long_chain} 个。",
        "key": f"当前 Codex 的主要价值是执行推进；关键改进点是把 {sessions} 个 sessions 的阶段回放做得更稳定。",
    }

    wins = [
        {"title": "执行强度", "desc": f"{sessions} 个 sessions，平均时长 {avg_min} 分钟，说明执行层使用稳定。"},
        {"title": "工具集中度", "desc": f"Top tools: {top_tools}。工具调用集中，适合继续沉淀固定 runbook。"},
        {"title": "任务聚焦", "desc": f"Top domains: {top_domains}；Top projects: {top_projects}。当前优化目标足够明确。"},
    ]

    friction_cards = [
        {
            "title": "阶段回放风险",
            "desc": f"当前有 {sessions} 个执行 session。若阶段小结不固定，后续回放和交接成本会升高。",
            "examples": [
                "每阶段固定输出: 已完成 / 已验证 / 剩余风险 / 下一步。",
                "跨 repo 任务按 repo 结账，不要混在同一段执行日志里。",
            ],
        },
        {
            "title": "上下文边界风险",
            "desc": "当任务在多个 repo 间切换但上下文未显式声明时，报告聚类与问题归因会变弱。",
            "examples": [
                "任务开头明确 repo、模块、验证命令。",
                "每个 repo 单独输出阶段总结。",
            ],
        },
    ]

    feature_cards = [
        {
            "title": "阶段小结协议",
            "summary": "把执行过程结构化，降低回放成本。",
            "detail": f"适用于当前 {sessions} 个 sessions 的执行节奏，优先提升可回放性。",
            "starter": "每批改动后立即输出四项小结。",
            "prompt": "每完成一批改动后输出: 已改文件、已验证项、未解决风险、下一步。",
        },
        {
            "title": "多 repo 拆单",
            "summary": "将跨仓执行拆成并行单元，避免状态混乱。",
            "detail": "拆分后每个单元有独立目标与验证，返工更可控。",
            "starter": "一个 repo 一个执行单元。",
            "prompt": "请把当前多 repo 任务拆成并行单元，并给出每个单元的目标、改动范围、验证命令与结束条件。",
        },
        {
            "title": "验证前移",
            "summary": "每批改动后做轻量门禁，减少末端爆雷。",
            "detail": "建议先从 analyze + 关键 grep 开始。",
            "starter": "门禁通过再进入下一批。",
            "prompt": "按门禁循环推进，每批改动后先做 analyze 和关键检查，通过后再继续下一批。",
        },
    ]

    pattern_cards = [
        {
            "title": "执行前阶段化",
            "summary": "先切阶段再开工。",
            "detail": "阶段边界清晰时，执行链更稳、回放更快。",
            "starter": "每阶段只解决一个明确目标。",
            "prompt": "先列阶段计划：目标文件、预期改动、验证命令、结束条件。",
        },
        {
            "title": "批次后总结",
            "summary": "把总结做成默认动作。",
            "detail": "避免后期只剩大段日志难以复盘。",
            "starter": "每批次必写小结。",
            "prompt": "每批改动后输出固定小结：完成项、验证项、风险、下一步。",
        },
        {
            "title": "需求边界锁定",
            "summary": "执行层不改需求，只执行既定边界。",
            "detail": "边界漂移会放大返工成本。",
            "starter": "发现边界不足时先回报，不自行扩展。",
            "prompt": "按给定目标和边界执行，不要扩展需求；若信息不足，仅输出缺失项与影响。",
        },
    ]

    horizon_cards = [
        {"title": "补齐 outcome/friction", "desc": "为 Codex 增加结构化 outcome/friction 后，可直接评估执行质量而非仅工作量。"},
        {"title": "阶段协议默认化", "desc": "把阶段小结设为默认协议，可显著提升跨会话连续性。"},
        {"title": "验证链模板化", "desc": "将 analyze/测试/grep 门禁模板化，让执行链更稳定。"},
    ]

    return build_bundle(
        glance_sections=[
            f"<strong>What's working:</strong> Codex 本期 {sessions} 个 sessions，执行主线稳定。 <a href=\"#section-wins\" class=\"see-more\">Impressive Things You Did →</a>",
            f"<strong>What's hindering you:</strong> 长链路与跨 repo 任务的阶段回放成本仍高。 <a href=\"#section-friction\" class=\"see-more\">Where Things Go Wrong →</a>",
            f"<strong>Quick wins to try:</strong> 先落地阶段小结协议与验证前移。 <a href=\"#section-features\" class=\"see-more\">Features to Try →</a>",
            f"<strong>Ambitious workflows:</strong> 补齐 outcome/friction 后可升级为执行质量闭环。 <a href=\"#section-horizon\" class=\"see-more\">On the Horizon →</a>",
        ],
        work_intro=f"当前 Codex 工作主要集中在 {top_domains}。重点是执行推进效率与可回放性。",
        usage_narrative=usage_narrative,
        wins_intro="以下亮点基于本次统计值自动生成。",
        wins=wins,
        friction_intro="以下风险与改进建议基于本次执行数据生成。",
        friction_cards=friction_cards,
        feature_intro="以下是可直接执行的优化动作。",
        feature_cards=feature_cards,
        pattern_intro="以下模式用于提高长链路执行稳定性。",
        pattern_cards=pattern_cards,
        horizon_intro="下一阶段建议围绕质量标注与协议固化。",
        horizon_cards=horizon_cards,
        ending_headline="Codex 当前角色是稳定执行层。",
        ending_detail="继续优化的核心是阶段化与可回放，而不是增加对话长度。",
    )
