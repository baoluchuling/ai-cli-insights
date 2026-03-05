# ai-cli-insights

Cross-tool usage analytics for **Claude Code** and **Codex CLI**. Collects session data from both tools and generates rich HTML insight reports with narratives, trend charts, friction analysis, and actionable recommendations.

## Features

- Unified data collection from Claude Code (`~/.claude/`) and Codex CLI (`~/.codex/`)
- Three report modes: cross-tool comparison, Claude-only, Codex-only
- Period-over-period comparison, trend sparklines, quality scoring
- Friction pattern analysis with evidence-based recommendations
- Prompt library with copy-to-clipboard templates
- Zero third-party dependencies — pure Python standard library

## Installation

```bash
pip install ai-cli-insights
```

## Quick Start

```bash
# Generate a cross-tool report for the last 30 days
ai-cli-insights generate --days 30 --tool all

# Claude-only report
ai-cli-insights generate --tool claude

# Codex-only report
ai-cli-insights generate --tool codex

# Short form (generate is the default command)
ai-cli-insights --days 7 --tool claude
```

The HTML report is saved to the output directory and can be opened in any browser.

## Configuration

```bash
# Create a config template
ai-cli-insights init
```

This writes a `config.json` to your config directory:
- **macOS**: `~/Library/Application Support/ai-cli-insights/config.json`
- **Linux**: `~/.config/ai-cli-insights/config.json`

Edit it to customize:
- `domain_patterns` — keyword patterns to classify sessions into work domains
- `project_patterns` — patterns to identify which project a session belongs to
- `template_modes` — report titles and slugs

Without a config file, reports still work — domains and projects will just show raw paths.

## Claude Code Skill

```bash
# Install a Claude Code skill for easy /multi-insights access
ai-cli-insights install-skill

# Install a Codex CLI skill
ai-cli-insights install-codex-skill
```

This writes:
- Claude Code skill: `~/.claude/skills/multi-insights/SKILL.md`
- Codex CLI skill: `~/.codex/skills/multi-insights/SKILL.md`

## CLI Reference

```
ai-cli-insights [command] [options]

Commands:
  generate        Generate an HTML insights report (default)
  init            Write a config template to the config directory
  install-skill   Install Claude Code skill file
  install-codex-skill  Install Codex CLI skill file

Generate options:
  --days N        Analyze the last N days (default: 30)
  --tool MODE     all | claude | codex (default: all)
  --analyst WHO   codex | claude — label the analyzing model (default: codex)
  --output-dir    Override the output directory

python -m ai_cli_insights also works.
```

## Data Sources

| Tool | Source | What it provides |
|------|--------|-----------------|
| Claude Code | `~/.claude/usage-data/session-meta/*.json` | Session metadata, tool counts, tokens |
| Claude Code | `~/.claude/usage-data/facets/*.json` | Outcomes, friction, goals |
| Codex CLI | `~/.codex/state_5.sqlite` | Thread metadata, tokens |
| Codex CLI | `~/.codex/sessions/*.jsonl` | Event details, timestamps, tools |
| Codex CLI | `~/.codex/history.jsonl` | User message counts |

## License

MIT
