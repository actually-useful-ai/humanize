# humanize

Claude Code plugin that strips machine-generated writing patterns from documentation.

## Structure

- `.claude-plugin/plugin.json` — Plugin metadata
- `.claude-plugin/marketplace.json` — Marketplace listing
- `skills/humanize/SKILL.md` — Full skill definition (15 detection patterns, confidence scoring, 3-phase workflow)
- `commands/humanize.md` — `/humanize` command entry point

## How It Works

One command: `/humanize [path] [--dry-run] [--strict]`

Scans markdown files and package metadata for 15 categories of machine-generated writing indicators, scores each match by confidence, then auto-fixes high-confidence patterns and suggests changes for the rest.

## Development

Pure-markdown plugin. No build step, no dependencies. Edit the `.md` files directly.
