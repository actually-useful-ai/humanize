# Scanner contract and migration

## Commands

Run `python3 <skill-root>/scripts/doc_humanizer.py scan <files-or-directories>`.
Use `--format json` for structured results, `--check` for a lint gate, and
`--parallel` for bounded concurrent scanning. `batch` is an alias for scanning.
`rules` prints the authoritative catalog. With no files, the scanner selects
existing README.md, CONTRIBUTING.md, and docs/ in the current directory.

Python 3.10+ is required. Processing stays local. No dependencies, downloads,
provider calls, or background services are needed.

## Coverage and limits

Supported files: UTF-8 `.md`, `.markdown`, and `.txt` (case-insensitive). Protection
is conservatively applied to all three. The scanner masks fenced/indented code,
inline code, links and images, URLs, quotes, references, front matter, and
embedded HTML. It preserves original positions. This is not a full CommonMark
parser: ambiguous regions are skipped and may hide otherwise editable prose.

The catalog has 13 rules. Eight general rules run by default. Three extra
contextual rules run with `--strict`. The `luke` profile adds two house-style
rules. General editorial work such as paragraph organization, source fidelity,
voice, acronym explanation, and useful summaries remains an agent task.

Instruction files, licenses, notices, changelogs, clinical/specification folders,
hidden/generated/vendor directories, and symlinks are excluded. Explicitly
requesting one does not bypass scanner protection. HTML, source code, and package
metadata are unsupported and reported as skipped. Named prose within such files
can still be edited through the skill with format-aware tools.

## Configuration

Pass `--config <path>` explicitly. No config is discovered or executed implicitly.
Use a JSON object:

```json
{
  "profile": "luke",
  "audience": "people installing a watch face",
  "genre": "installation instructions",
  "disabled_rules": ["H003"],
  "allow_terms": ["At its core"],
  "exclude": ["docs/archive/*"]
}
```

`--profile` overrides the config profile. `standard` is the default. Audience and
genre are editorial context carried in the report, not extra mechanical rules.
An allow-term suppresses overlapping findings, case-insensitively. Exclusions
only narrow the target set. Unknown settings and rule IDs are errors.

## Output and exit status

JSON schema version 2 contains files with `scanned`, `skipped`, or `error` status.
Each diagnostic includes a stable rule ID, matched text, severity, explanation,
suggestion, and `autofix: false`. `start`/`end` are zero-based Unicode code-point
offsets with exclusive end; `line`/`column` are one-based. These are not UTF-8 byte
offsets. Results are sorted by file and source position.

- **0:** at least one file scanned, no operational errors; findings are advisory.
- **1:** `--check` was supplied and findings exist.
- **2:** invalid arguments/config, an operational error, or no supported files
  scanned. Skips are always reported and are never labelled clean.

A mixed directory may contain supported and skipped files and still exit 0.
Callers that require full coverage must inspect the per-file status.

## Changes from 1.x

The agent command `/humanize` still performs requested contextual edits.
The Python scanner never writes targets. `fix`, `diff`, and `--dry-run` remain
accepted, with an explicit message that contextual agent editing is required.
No source-file writer remains, so no-op commands preserve bytes, BOM, line
endings, permissions, and modification times. This also avoids concurrent
source overwrites by the scanner. Agents editing files must recheck their diff
and concurrent changes through the host's normal editing tools.

`--confidence` and `--threshold` now fail with migration guidance. Use `--strict`
to include contextual suggestions and `--check` to gate on findings. The
`apply_transforms(text)` Python compatibility method returns its input unchanged;
a supplied old threshold produces a deprecation warning. Diagnostic fields and
JSON shape changed; integrations must migrate instead of interpreting severity
as a probability.

Automatic attribution, status, synonym, punctuation, and uncertainty rewrites
have been removed. There is no universal safe-edit allowlist yet. Adding a rule
to that category requires a separate preservation contract and adversarial tests.
