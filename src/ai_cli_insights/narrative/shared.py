from __future__ import annotations

from collections import Counter

from ..analytics import infer_codex_archetypes
from ..models import AnalyzedData, NarrativeBundle, ReportMeta

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
        dominant = "Claude" if claude_count > codex_count else "Codex" if codex_count > claude_count else "Balanced"
        cards.append(
            {
                "name": domain,
                "count": count,
                "desc": (
                    f"{domain} 在当前窗口共 {count} 个 sessions。"
                    f"分布为 Claude {claude_count} / Codex {codex_count}，"
                    f"主导侧: {dominant}。"
                ),
                "split": split,
            }
        )
    return cards


def top_domains_text(data: AnalyzedData, n: int = 3) -> str:
    combined = Counter()
    for counter in data.domains.values():
        combined.update(counter)
    return ", ".join(name for name, _ in combined.most_common(n)) or "暂无"


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
