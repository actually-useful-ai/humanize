# humanize

Claude Code plugin that strips machine-generated writing patterns from documentation.

## Structure

- `.claude-plugin/plugin.json` — Plugin metadata
- `.claude-plugin/marketplace.json` — Marketplace listing
- `skills/humanize/SKILL.md` — Full skill definition with 23 detection patterns and confidence scoring
- `commands/humanize.md` — `/humanize` command entry point
- `skills/humanize/scripts/doc_humanizer.py` — Deterministic scanner and high-confidence fixes
- `tests/test_plugin_package.py` — Package structure and metadata checks

## How It Works

One command: `/humanize [path] [--dry-run] [--strict]`

Scans Markdown files and package metadata for 23 categories of weak writing,
scores each match by confidence, then fixes high-confidence patterns and
suggests changes for the rest.

## Development

The plugin has no build step or third-party runtime dependency. Edit the
Markdown sources directly and use the standard-library Python scanner and tests
for validation.
