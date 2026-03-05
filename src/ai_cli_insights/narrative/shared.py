from __future__ import annotations

from collections import Counter

from ..analytics import infer_codex_archetypes
from ..models import AnalyzedData, NarrativeBundle, ReportMeta


DOMAIN_DESCRIPTIONS = {
    "Flutter 多仓开发与组件化": "这仍然是你最像“工程负责人”而不只是“使用者”的一类工作。你不是在单仓修小问题，而是在多个 Flutter 仓库之间同步行为、迁移模块边界、收口桥接层、补齐 i18n 与页面包装；这类任务天然需要先有判断层，再有执行层，所以也最能体现 Claude 与 Codex 的互补性。",
    "调试与构建故障": "这一类任务最能暴露模型质量差异。问题通常涉及运行时报错、构建失败、SDK 兼容、原生崩溃或证书/依赖约束，表面看是修 bug，实质上是在比谁更能先贴住证据再给判断。Claude 的价值主要出现在 root cause 分析，但最高频摩擦也集中在这里；Codex 则更适合带着日志和编译输出持续推进修复。",
    "测试与验证": "测试相关工作虽然 session 数不算最高，但很关键，因为它决定你是“改完就算”还是“改完可回放”。你已经在做读取测试计划、组件校验、回归验证和结果沉淀，这说明你在把 AI 从一次性输出，往可验证流程推进。",
    "工作流与记忆系统": "这部分很说明问题。你不只是让模型回答问题，而是在建设自己的 AI 工作台：.memory、skills、目录约定、自动学习和跨工具分析本身，都是在减少未来每个 session 的重新发现成本。换句话说，你已经在把“如何使用模型”当成一个可持续优化的系统工程。",
    "工具开发与可视化": "Agent 管理平台、worklog 类桌面工具和可视化面板之所以占比高，不只是因为它们复杂，而是因为它们同时要求实现、调试、界面表达和运行链路闭环。这类项目很容易把模型的优点和短板同时放大，所以也是最值得拿来观察工作流设计的样本。",
    "技术调研与问答": "这类 session 数量不高，但通常决定后面的方向是否会偏。你往往先用这类对话澄清导入规则、条件编译、架构限制或技术边界，然后再进入后续实施；也就是说，它们更像路线选择，而不是产出本身。",
}


def build_project_area_cards(data: AnalyzedData, meta: ReportMeta) -> list[dict]:
    combined = Counter()
    for counter in data.domains.values():
        combined.update(counter)

    cards = []
    for domain, count in combined.most_common(5):
        claude_count = data.domains.get("claude_code", Counter()).get(domain, 0)
        codex_count = data.domains.get("codex_cli", Counter()).get(domain, 0)
        if meta.tool == "all":
            split = f"Claude {claude_count} / Codex {codex_count}"
        elif meta.tool == "claude":
            split = f"Claude {claude_count}"
        else:
            split = f"Codex {codex_count}"
        cards.append(
            {
                "name": domain,
                "count": count,
                "desc": DOMAIN_DESCRIPTIONS.get(domain, ""),
                "split": split,
            }
        )
    return cards


def top_domains_text(data: AnalyzedData, n: int = 3) -> str:
    combined = Counter()
    for counter in data.domains.values():
        combined.update(counter)
    return ", ".join(name for name, _ in combined.most_common(n)) or "多仓开发与工作流建设"


def success_domains_text(data: AnalyzedData, n: int = 3) -> str:
    return ", ".join(name for name, _ in data.success_patterns["domains"].most_common(n)) or "暂无"


def friction_text(data: AnalyzedData, n: int = 2, sep: str = "、") -> str:
    top_friction = data.friction_counts.most_common(n)
    return sep.join(f"{name}({count})" for name, count in top_friction) if top_friction else "暂无"


def achieved_counts(data: AnalyzedData) -> tuple[int, int]:
    outcomes = data.outcomes
    achieved = outcomes.get("fully_achieved", 0) + outcomes.get("mostly_achieved", 0)
    not_achieved = outcomes.get("partially_achieved", 0) + outcomes.get("not_achieved", 0)
    return achieved, not_achieved


def codex_archetype_line(data: AnalyzedData) -> str:
    archetypes = infer_codex_archetypes(data)
    return "、".join(item["title"] for item in archetypes) if archetypes else "长链路执行"


def build_bundle(
    *,
    glance_sections: list[str],
    work_intro: str,
    usage_narrative: dict[str, str],
    wins_intro: str,
    wins: list[dict],
    friction_intro: str,
    friction_cards: list[dict],
    feature_intro: str,
    feature_cards: list[dict],
    pattern_intro: str,
    pattern_cards: list[dict],
    horizon_intro: str,
    horizon_cards: list[dict],
    ending_headline: str,
    ending_detail: str,
) -> NarrativeBundle:
    return NarrativeBundle(
        glance_sections=glance_sections,
        work_intro=work_intro,
        usage_narrative=usage_narrative,
        wins_intro=wins_intro,
        wins=wins,
        friction_intro=friction_intro,
        friction_cards=friction_cards,
        feature_intro=feature_intro,
        feature_cards=feature_cards,
        pattern_intro=pattern_intro,
        pattern_cards=pattern_cards,
        horizon_intro=horizon_intro,
        horizon_cards=horizon_cards,
        ending_headline=ending_headline,
        ending_detail=ending_detail,
    )

