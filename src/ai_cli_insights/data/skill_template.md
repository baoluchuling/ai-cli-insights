---
name: multi-insights
description: "Cross-tool usage analytics. Collects Claude Code and Codex CLI session data and generates comparison insight reports. Use /multi-insights to trigger."
---

# Multi-Insights Skill

Generate cross-tool usage analytics reports for Claude Code and Codex CLI.

## Usage

Run the following command to generate a report:

```bash
{command} generate --days 30 --tool all --analyst claude
```

### Options

- `--days N` — Analyze the last N days (default: 30)
- `--tool all|claude|codex` — Which tool's data to include
- `--analyst codex|claude` — Label the analyzing model

### Other commands

```bash
# Initialize a config template
{command} init

# Install this skill file
{command} install-skill
```

## Data Sources

- **Claude Code**: `~/.claude/usage-data/session-meta` and `facets`
- **Codex CLI**: `~/.codex/sessions/*.jsonl` and SQLite database

## Output

HTML report saved to the configured output directory. Open in any browser.
