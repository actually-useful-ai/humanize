---
description: Strip robot language from user-facing content — runs the humanize skill on the given path (default: docs in cwd)
---

Apply the **humanize** skill (skills/humanize/SKILL.md in this plugin — the single source of the rules) to the target below. Do not improvise a second rule set here.

Target: `$ARGUMENTS` if given (file or directory); otherwise README.md, CHANGELOG.md, any `.md` under docs/, and package descriptions in package.json / pyproject.toml in the current working directory.

Follow the skill's principle — flow, not concealment — and its editing test: every change must make the sentence say something more directly, in a rhythm a person would use. Report what changed, file by file, and anything you deliberately left alone.
