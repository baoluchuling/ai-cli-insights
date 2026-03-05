from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class ReportMeta:
    tool: str
    title: str
    subtitle_prefix: str
    file_slug: str
    compare_sources: bool
    primary_source: str | None
    analyst_label: str


@dataclass
class AnalyzedData:
    raw: dict
    sessions: list[dict]
    comparison: dict
    domains: dict[str, Counter]
    projects: dict[str, Counter]
    friction_counts: Counter
    outcomes: Counter
    friction_sessions: list[dict]
    success_patterns: dict


@dataclass
class PeriodComparison:
    current_label: str
    previous_label: str
    current: dict
    previous: dict


@dataclass
class NarrativeBundle:
    glance_sections: list[str]
    work_intro: str
    usage_narrative: dict[str, str]
    wins_intro: str
    wins: list[dict]
    friction_intro: str
    friction_cards: list[dict]
    feature_intro: str
    feature_cards: list[dict]
    pattern_intro: str
    pattern_cards: list[dict]
    horizon_intro: str
    horizon_cards: list[dict]
    ending_headline: str
    ending_detail: str


@dataclass
class ReportExtras:
    snapshot_compare: dict
    trend_cards: list[dict]
    operational_signals: list[dict]
    platform_recommendations: list[dict]
    project_drilldown: list[dict]
    leaderboards: list[dict]
    prompt_library: dict[str, list[dict]]
    task_matrix: list[dict]
    quality_score: dict
    llm_analysis: dict | None = None


@dataclass
class PlatformSection:
    meta: ReportMeta
    data: AnalyzedData
    period_comparison: PeriodComparison | None
    narrative: NarrativeBundle
    project_cards: list[dict]
    extras: ReportExtras
