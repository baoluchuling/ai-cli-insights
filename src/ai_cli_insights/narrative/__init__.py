from __future__ import annotations

from . import all as all_mode
from . import claude as claude_mode
from . import codex as codex_mode
from .shared import build_project_area_cards
from ..models import AnalyzedData, NarrativeBundle, ReportMeta


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    if meta.tool == "claude":
        return claude_mode.build_narrative_bundle(data, meta)
    if meta.tool == "codex":
        return codex_mode.build_narrative_bundle(data, meta)
    return all_mode.build_narrative_bundle(data, meta)
