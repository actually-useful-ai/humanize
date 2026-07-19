# humanize

Humanize restores natural flow to documentation and other user-facing prose.

LLM-generated text has tells: em-dashes for dramatic effect, contrast pivots ("It's not just X, it's Y"), corporate jargon clusters ("leverage a robust ecosystem"), rhetorical pivots ("The result? ..."), and stiff constructions like "It is important to note that." This plugin detects 23 categories of these patterns and fixes them.

Humanize edits for clarity, not to disguise authorship. These constructions are tells because they're weak writing: they pad, they hedge, they substitute cadence for content. A human editor would cut them for the same reason this plugin does. The goal is prose that's direct, specific, varied in rhythm, and allowed to have some personality.

## Install

### Codex

Clone the repository, then open the Codex desktop Plugin Directory, choose **Import local plugin**, and select the cloned `humanize` folder.

```bash
mkdir -p "$HOME/plugins"
git clone https://github.com/actually-useful-ai/humanize.git "$HOME/plugins/humanize"
```

Codex versions that load personal skills directly can use a guarded symlink instead:

```bash
mkdir -p "$HOME/.codex/skills"
target="$HOME/.codex/skills/humanize"
source_dir="$HOME/plugins/humanize/skills/humanize"

if [ -e "$target" ] || [ -L "$target" ]; then
  printf 'Humanize already exists at %s\n' "$target"
else
  ln -s "$source_dir" "$target"
fi
```

### Claude Code

Run these commands inside Claude Code:

```
/plugin marketplace add actually-useful-ai/humanize
/plugin install humanize@actually-useful-ai-humanize
```

## Usage

```
/humanize              # scan README.md, CHANGELOG.md, docs/*.md in cwd
/humanize src/docs/    # scan a specific directory
/humanize README.md    # scan a specific file
/humanize --dry-run    # report without making changes
/humanize --strict     # also auto-fix medium-confidence patterns
```

## What It Detects

| Pattern | Confidence | Example |
|---------|-----------|---------|
| Em-dashes | 0.95 | "provides--and this is critical--updates" |
| Corporate jargon | 0.90 | "leverage", "synergy", "ecosystem" |
| Buzzword clusters | 0.90 | "optimized, scalable, future-proof" |
| Stiff construction | 0.90 | "It is important to note that..." |
| Redundancy | 0.95 | "advance planning", "past history" |
| LLM attribution | 1.0 | "Claude generated this", "the assistant" |
| Solo "we" to "I" | 0.90 | "We implemented" in solo context |
| Passive voice | 0.85 | "The data is processed by the system" |
| Hedge phrases | 0.80 | "might potentially", "could perhaps" |
| Formal metadata | 0.85 | "This document provides an overview" |
| Success metrics | 0.85 | "improves performance by up to 80%" |
| Acronyms | 0.80 | Unexpanded on first use |
| Transition phrases | 0.75 | "Furthermore", "Moreover" |
| Excessive dates | 0.75 | Timestamps in narrative prose |
| Over-structuring | 0.70 | Numbered lists for 2-3 items |
| Contrast pivot | 0.90 | "It's not just X, it's Y" |
| Trailing participles | 0.85 | ", ensuring reliability" |
| Rhetorical pivots | 0.85 | "The result? A faster pipeline." |
| Significance inflation | 0.85 | "At its core", "game-changer" |
| Audience hedging | 0.85 | "Whether you're a beginner or..." |
| Summary closers | 0.80 | "In conclusion", "Ultimately" |
| Rule-of-three cadence | 0.75 | Triplets as every sentence's rhythm |
| Monotone rhythm | 0.65 | Same sentence shape, wall to wall |

## How It Works

1. **Checkpoint** -- commits any uncommitted changes before touching files
2. **Scan** -- applies all 23 detection patterns with confidence scores
3. **Transform** -- auto-fixes high-confidence (>0.9), suggests medium (0.7-0.9), flags low (<0.7)
4. **Report** -- shows a summary with before/after diffs

## Safety

- Never modifies code blocks, URLs, or citations
- Never changes meaning or removes attribution to real people
- Skips CLAUDE.md files (system instructions, not prose)
- Always creates a git checkpoint before making changes
- Shows diff previews for all changes

## Terminology Ban

The plugin also flags prohibited umbrella branding. Use "LLM", "language model", or name the specific model instead.

## License

MIT
