# Humanize

Humanize edits prose for clarity, flow, and the writer's voice. It preserves
facts, uncertainty, attribution, code, and citations. Good prose can stay as it is.

Use it to improve a README, clarify product copy, tighten release notes, or match
a supplied writing sample. The agent performs the editorial pass. An optional
local Python scanner points out contextual patterns without changing files.

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

### Cursor

```sh
cursor-agent plugin marketplace add https://github.com/actually-useful-ai/humanize
cursor-agent
```

Open `/plugin` in the interactive agent and install Humanize at user scope so
the same installation is available in the IDE and CLI.

## Usage

```text
/humanize README.md
/humanize docs/
/humanize README.md --dry-run
/humanize README.md --strict
```

An editing request authorizes changes to the named prose. A dry run reports
suggestions. Strict mode adds scrutiny while keeping the same preservation rules.
With no target, Humanize uses existing README.md, CONTRIBUTING.md, and Markdown
under docs/ in the current project.

For a voice match, provide a short sample and identify the intended reader.
For an embedded editing task, Humanize returns only the requested final prose.

## What improves

- Organization around the reader's task.
- Concrete subjects and actions, with useful transitions.
- Less repetition and promotional filler.
- Rhythm and register consistent with the source.
- Clear explanations that retain uncertainty and technical meaning.

For example, “The patch could potentially reduce latency” can become “The patch
could reduce latency.” The possibility remains a possibility.

## Local scanner

Python 3.10+ is sufficient; no packages or services are required.

```sh
python3 skills/humanize/scripts/doc_humanizer.py scan README.md
python3 skills/humanize/scripts/doc_humanizer.py scan docs/ --format json --check
python3 skills/humanize/scripts/doc_humanizer.py scan README.md --profile luke
python3 skills/humanize/scripts/doc_humanizer.py rules
```

The [rule catalog](skills/humanize/references/rules.json) defines 13 contextual
checks: eight general checks, three additional strict checks, and two Luke
house-style checks. Findings are suggestions, with exact locations and reasons.
The scanner supports UTF-8 Markdown and plain text. Unsupported formats and
protected content are reported separately. It never writes target files.

The agent handles paragraph flow, voice, evidence, and contextual editing.
Mechanical checks do not establish authorship, factual accuracy, or accessibility
conformance. See the [scanner contract](skills/humanize/references/scanner.md)
for configuration, format limits, and exit codes.

## Upgrading from 1.x

Version 2 removes automatic attribution/status deletion, synonym replacement,
punctuation replacement, and numeric confidence thresholds. Legacy scanner
`fix` and `diff` commands report suggestions and leave files unchanged. The
`/humanize` agent workflow still completes requested prose edits.

Update the installed plugin through its runtime and start a new session. Check
the loaded version; an updated checkout does not update an existing plugin cache.
Use one intended installation per runtime to avoid duplicate skill resolution.

## Development

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 tests/evaluate_editorial.py
```

Tests cover package consistency, source preservation, diagnostic locations, and
CLI behavior. The original editorial corpus contains development and held-out
examples. Its automated checks validate explicit preservation literals; human
review is still needed to establish writing quality. No readability improvement
percentage is claimed.

## License

MIT. Copyright Luke Steuber. See [LICENSE](LICENSE).
