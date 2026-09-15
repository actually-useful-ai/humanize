# Editing guidance

## Reader and structure

Identify what the reader should understand or do after reading. Put that point
where they can find it. Keep context needed to assess the claim. A summary helps
someone returning to a long document; a list helps someone follow instructions.
Neither is a defect by itself.

Before: “This document provides an overview of how to restore a backup. The
backup must be less than 30 days old. To restore, choose Restore.”

After: “To restore a backup, choose Restore. The backup must be less than 30 days old.”

Counterexample: a heading such as “Overview” can help navigation. Keep it when
it serves the document.

## Specificity without invention

A concrete detail must come from the source or user. Replace empty adjectives
with supported behavior. If the source gives no detail, simplify or flag the
gap. Do not make a feature sound proven by supplying imagined numbers.

Before: “The tool provides a seamless export experience. It exports CSV.”

After: “The tool exports CSV.”

Counterexample: “robust estimator” names a technical property. Keep it.

## Evidence and uncertainty

Before: “The patch could potentially reduce startup time.”

After: “The patch could reduce startup time.”

Counterexample: “The patch might fail on older devices” is useful uncertainty.
Keep it. Preserve “up to,” sample sizes, dates, versions, units, negative findings,
and the distinction between observed behavior and expectation. Grammar checks
cannot establish whether a claim is true.

## Voice

Follow an explicit writing sample's rhythm, register, and word choices, subject
to the task's factual constraints. Otherwise retain the author's voice. Personal
writing can keep jokes, opinions, fragments, and uncertainty. Reference material
should help the reader find an answer. Interface text should make actions and
recovery clear. Avoid adding a personality that the source did not have.

Before: “I tried the new layout. I liked the old one better, honestly.”

After: unchanged.

Counterexample: a forced one-line closer after every paragraph can make prose
repetitive. Remove a closer only if it adds no information or useful emphasis.

## Connections and cadence

Explain how adjacent points relate. “However” can express a real exception;
“also” can add a second capability. Check repeated sentence openings and
paragraph shapes. Do not enforce sentence-length quotas or a fixed number of
triplets, dashes, or bullets.

Before: “The parser validates entries. The server serves those entries. The
parser runs hourly.”

After: “The parser validates entries hourly. The server serves the validated entries.”

Counterexample: parallel wording can make comparable choices easier to scan.

## Actors and ownership

Use active voice when it clarifies responsibility. Keep passive voice when the
actor is unknown or irrelevant. Never invent an actor to satisfy a rule.

Before: “The file is checked by the server.”

After: “The server checks the file.”

Counterexample: “The password is encrypted at rest” can be clear as written.
Keep model involvement and third-party credit accurate. Solo-author preferences
do not authorize replacing someone else's attribution.

## Source notes

Reviewed September 14, 2026. These sources inform the approach; examples above
are original. No third-party rules or implementation code are copied.

- [Google developer style: tone](https://developers.google.com/style/tone) and
  [voice](https://developers.google.com/style/voice): useful conversational prose
  and contextual use of passive voice.
- [W3C clear-content guidance](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o3-clear-content/):
  clear language, manageable chunks, separate instructions, useful summaries.
  This supplemental guidance does not establish WCAG conformance.
- [Vale scopes](https://docs.vale.sh/topics/scopes): separate document regions
  before applying a prose rule. Vale remains an optional future integration.
- [blader/humanizer](https://github.com/blader/humanizer), MIT, version 3.0.0:
  voice samples, source fidelity, contextual rather than universal patterns.
- [Agent Skills specification](https://agentskills.io/specification): compact
  core instructions with focused references.
