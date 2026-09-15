# Humanize development

Canonical source: actually-useful-ai/humanize. Installed caches are projections;
edit this repository and reinstall a versioned package.

The universal workflow is skills/humanize/SKILL.md. commands/humanize.md is a thin
Claude command wrapper. Keep Codex, Claude, and Cursor manifests aligned.

The dependency-free Python scanner reads references/rules.json and emits
contextual diagnostics. It never writes target files. Agent editing remains
scoped by the skill. No semantic rule currently qualifies for automatic fixing.

Run PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v and
python3 tests/evaluate_editorial.py. Add preservation/counterexample cases when
changing rules or Markdown protection. Do not turn corpus consistency checks
into claims of human writing-quality validation.

Keep Luke Steuber as author. Follow workspace Git guidance and stage only
intended files. Public documentation describes behavior and verified limits.
