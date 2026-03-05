"""CLI entry point for ai-cli-insights."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .analytics import analyze, build_period_comparison, run_collect, subset_raw_by_source
from .config import config_dir, output_dir, make_report_meta
from .extras import build_report_extras, snapshot_payload
from .html_renderer import load_previous_snapshot, render_html, run_self_check, write_report, write_snapshot
from .narrative import build_narrative_bundle, build_project_area_cards
from .models import PlatformSection


def cmd_generate(args: argparse.Namespace) -> None:
    raw = run_collect(args.days, args.tool)
    analyst_label = "Claude" if args.analyst == "claude" else "GPT (Codex CLI)"
    meta = make_report_meta(args.tool, analyst_label=analyst_label)
    out = Path(args.output_dir)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = analyze(raw)
    period_comparison = build_period_comparison(args.days, args.tool)
    narrative = build_narrative_bundle(data, meta)
    project_cards = build_project_area_cards(data, meta)
    previous_snapshot = load_previous_snapshot(out, meta)
    extras = build_report_extras(data, meta, narrative, previous_snapshot)
    platform_sections: dict[str, PlatformSection] = {}
    if args.tool == "all":
        for tool_name, source in (("claude", "claude_code"), ("codex", "codex_cli")):
            sub_meta = make_report_meta(tool_name, analyst_label=analyst_label)
            sub_data = analyze(subset_raw_by_source(raw, source))
            sub_narrative = build_narrative_bundle(sub_data, sub_meta)
            sub_previous_snapshot = load_previous_snapshot(out, sub_meta)
            sub_extras = build_report_extras(sub_data, sub_meta, sub_narrative, sub_previous_snapshot)
            platform_sections[tool_name] = PlatformSection(
                meta=sub_meta,
                data=sub_data,
                period_comparison=build_period_comparison(args.days, tool_name),
                narrative=sub_narrative,
                project_cards=build_project_area_cards(sub_data, sub_meta),
                extras=sub_extras,
            )
    html_text = render_html(data, meta, period_comparison, narrative, project_cards, extras, platform_sections)
    missing = run_self_check(html_text)
    report_date = datetime.now().strftime("%Y-%m-%d")
    html_path = write_report(out, report_date, html_text, meta)
    write_snapshot(out, meta, generated_at, snapshot_payload(data, extras.quality_score, generated_at))

    print(
        json.dumps(
            {
                "html_report": str(html_path),
                "self_check_missing": missing,
                "period": raw.get("stats", {}).get("period", {}),
                "sources": {
                    source: {
                        "sessions": stats.get("sessions", 0),
                        "avg_duration_min": stats.get("avg_duration_min", 0),
                        "avg_user_messages": stats.get("avg_user_messages", 0),
                    }
                    for source, stats in data.comparison.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_init(args: argparse.Namespace) -> None:
    cfg_dir = config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "config.json"
    if cfg_path.exists() and not args.force:
        print(f"Config already exists at {cfg_path}. Use --force to overwrite.")
        return

    template = {
        "domain_patterns": {
            "Example Domain": ["keyword1", "keyword2"],
        },
        "domain_priority": ["Example Domain"],
        "project_patterns": [
            {"name": "my-project", "patterns": ["my-project", "my_project"]},
        ],
        "template_modes": {
            "all": {
                "title": "Multi-CLI Insights",
                "subtitle_prefix": "Cross-tool analysis",
                "file_slug": "multi-insights",
                "compare_sources": True,
            },
            "claude": {
                "title": "Claude Code Insights",
                "subtitle_prefix": "Claude single-tool analysis",
                "file_slug": "multi-insights-claude-only",
                "compare_sources": False,
            },
            "codex": {
                "title": "Codex CLI Insights",
                "subtitle_prefix": "Codex single-tool analysis",
                "file_slug": "multi-insights-codex-only",
                "compare_sources": False,
            },
        },
    }
    cfg_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Config template written to {cfg_path}")
    print("Edit domain_patterns / project_patterns to match your workflow.")


def cmd_install_skill(args: argparse.Namespace) -> None:
    from .skills import install_skill
    install_skill()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ai-cli-insights",
        description="Cross-tool usage analytics for Claude Code and Codex CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # generate (default)
    gen = subparsers.add_parser("generate", help="Generate an HTML insights report")
    gen.add_argument("--days", type=int, default=30)
    gen.add_argument("--tool", choices=["all", "claude", "codex"], default="all")
    gen.add_argument(
        "--analyst",
        choices=["codex", "claude"],
        default="codex",
        help="Label the analyzing model source (does not affect data collection).",
    )
    gen.add_argument("--output-dir", default=None, help="Output directory (default: XDG data dir)")
    gen.set_defaults(func=cmd_generate)

    # init
    init = subparsers.add_parser("init", help="Write a config template to the config directory")
    init.add_argument("--force", action="store_true", help="Overwrite existing config")
    init.set_defaults(func=cmd_init)

    # install-skill
    skill = subparsers.add_parser("install-skill", help="Install Claude Code skill file")
    skill.set_defaults(func=cmd_install_skill)

    args = parser.parse_args()

    # Default to generate if no subcommand
    if args.command is None:
        # Re-parse as generate
        gen_parser = argparse.ArgumentParser(prog="ai-cli-insights")
        gen_parser.add_argument("--days", type=int, default=30)
        gen_parser.add_argument("--tool", choices=["all", "claude", "codex"], default="all")
        gen_parser.add_argument("--analyst", choices=["codex", "claude"], default="codex")
        gen_parser.add_argument("--output-dir", default=None)
        args = gen_parser.parse_args()
        args.func = cmd_generate

    # Fill in default output-dir if not specified
    if hasattr(args, "output_dir") and args.output_dir is None:
        args.output_dir = str(output_dir())

    args.func(args)
