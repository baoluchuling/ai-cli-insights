from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .models import AnalyzedData, PeriodComparison, ReportExtras, ReportMeta

PROVIDER_ORDER = ("codex", "claude", "gemini")


def _available_providers() -> list[str]:
    return [name for name in PROVIDER_ORDER if shutil.which(name)]


def _pick_providers(requested: str) -> list[str]:
    if requested == "none":
        return []
    if requested == "auto":
        return _available_providers()
    return [requested]


def _compact_error(message: str, limit: int = 320) -> str:
    text = " ".join(part for part in message.strip().splitlines() if part.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _compact_payload(data: AnalyzedData, meta: ReportMeta, period: PeriodComparison | None, extras: ReportExtras) -> dict:
    sources: dict[str, dict] = {}
    for source, stats in data.comparison.items():
        sources[source] = {
            "sessions": stats.get("sessions", 0),
            "avg_duration_min": stats.get("avg_duration_min", 0),
            "avg_user_messages": stats.get("avg_user_messages", 0),
            "top_tools": stats.get("top_tools", [])[:5],
            "top_projects": stats.get("top_projects", [])[:5],
            "top_domains": stats.get("top_domains", [])[:5],
        }
    return {
        "meta": {
            "tool": meta.tool,
            "title": meta.title,
            "analyst_label": meta.analyst_label,
            "period": data.raw.get("stats", {}).get("period", {}),
        },
        "period_comparison": {
            "current_label": period.current_label if period else "",
            "previous_label": period.previous_label if period else "",
            "current": period.current if period else {},
            "previous": period.previous if period else {},
        },
        "sources": sources,
        "quality": extras.quality_score,
        "recommendations": extras.platform_recommendations,
        "project_drilldown": extras.project_drilldown[:5],
        "task_matrix": extras.task_matrix,
    }


def _analysis_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["headline", "summary", "insights", "actions", "risks"],
        "properties": {
            "headline": {"type": "string"},
            "summary": {"type": "string"},
            "insights": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
            "actions": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
            "risks": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
        },
    }


def _build_prompt(payload: dict) -> str:
    return (
        "你是资深工程效率分析师。请基于下面 JSON 数据，给出可执行、证据驱动的复盘。\n"
        "严格输出 JSON，不要输出 Markdown，不要输出解释。\n"
        "输出结构必须满足以下字段：headline, summary, insights[], actions[], risks[]。\n"
        "要求：\n"
        "- headline: 一句话结论\n"
        "- summary: 2-3 句总体判断\n"
        "- insights: 3-5 条关键洞察\n"
        "- actions: 3-5 条可立即执行动作\n"
        "- risks: 2-4 条主要风险\n\n"
        f"DATA:\n{json.dumps(payload, ensure_ascii=False)}\n"
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("empty response")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("response is not json")
        obj = json.loads(text[start : end + 1])

    if isinstance(obj, dict):
        if all(k in obj for k in ("headline", "summary", "insights", "actions", "risks")):
            return obj
        for key in ("result", "content", "output", "response"):
            value = obj.get(key)
            if isinstance(value, str):
                nested = _extract_json(value)
                if nested:
                    return nested
            if isinstance(value, dict) and all(k in value for k in ("headline", "summary", "insights", "actions", "risks")):
                return value
    raise ValueError("json shape mismatch")


def _normalize(result: dict) -> dict:
    def _arr(name: str, min_items: int, max_items: int) -> list[str]:
        items = result.get(name, [])
        if not isinstance(items, list):
            items = [str(items)]
        normalized = [str(item).strip() for item in items if str(item).strip()]
        return normalized[:max_items] if len(normalized) >= min_items else normalized

    normalized = {
        "headline": str(result.get("headline", "")).strip(),
        "summary": str(result.get("summary", "")).strip(),
        "insights": _arr("insights", 1, 5),
        "actions": _arr("actions", 1, 5),
        "risks": _arr("risks", 1, 4),
    }
    if not normalized["headline"] or not normalized["summary"]:
        raise ValueError("headline/summary missing")
    return normalized


def _run_codex(prompt: str, timeout_sec: int, model: str | None) -> str:
    with tempfile.TemporaryDirectory(prefix="ai-cli-insights-codex-") as tmpdir:
        out_path = Path(tmpdir) / "last_message.txt"
        schema_path = Path(tmpdir) / "schema.json"
        schema_path.write_text(json.dumps(_analysis_schema(), ensure_ascii=False), encoding="utf-8")
        cmd = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(out_path),
            "-",
        ]
        if model:
            cmd[2:2] = ["--model", model]
        proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout_sec)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "codex exec failed")
        if out_path.exists():
            out_text = out_path.read_text(encoding="utf-8").strip()
            if out_text:
                return out_text
        return proc.stdout


def _run_claude(prompt: str, timeout_sec: int, model: str | None) -> str:
    schema = json.dumps(_analysis_schema(), ensure_ascii=False)
    cmd = [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--permission-mode",
        "plan",
        "--json-schema",
        schema,
        prompt,
    ]
    if model:
        cmd[3:3] = ["--model", model]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_sec)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "claude print failed")
    return proc.stdout


def _run_gemini(prompt: str, timeout_sec: int, model: str | None) -> str:
    cmd = [
        "gemini",
        "--approval-mode",
        "plan",
        "-o",
        "json",
        "-p",
        prompt,
    ]
    if model:
        cmd[1:1] = ["-m", model]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_sec)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gemini prompt failed")
    return proc.stdout


def run_llm_analysis(
    data: AnalyzedData,
    meta: ReportMeta,
    period: PeriodComparison | None,
    extras: ReportExtras,
    provider: str = "auto",
    model: str | None = None,
    timeout_sec: int = 120,
) -> dict | None:
    candidates = _pick_providers(provider)
    if not candidates:
        return None

    payload = _compact_payload(data, meta, period, extras)
    prompt = _build_prompt(payload)
    errors: list[dict] = []
    for candidate in candidates:
        try:
            if candidate == "codex":
                output = _run_codex(prompt, timeout_sec, model)
            elif candidate == "claude":
                output = _run_claude(prompt, timeout_sec, model)
            elif candidate == "gemini":
                output = _run_gemini(prompt, timeout_sec, model)
            else:
                raise RuntimeError(f"unsupported provider: {candidate}")
            parsed = _normalize(_extract_json(output))
            parsed["status"] = "success"
            parsed["provider"] = candidate
            parsed["model"] = model or ""
            parsed["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return parsed
        except Exception as exc:  # pragma: no cover - fallback path
            errors.append({"provider": candidate, "error": _compact_error(str(exc))})

    return {
        "status": "failed",
        "provider": candidates[0] if len(candidates) == 1 else "auto",
        "model": model or "",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "errors": errors,
    }
