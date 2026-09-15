#!/usr/bin/env python3
"""Check declared fidelity literals; this cannot establish semantic quality.

Without candidates, validate the corpus. With a JSON object mapping case IDs to
edited text, report missing cases and literal-preservation failures. A passing
result still needs independent review of meaning, clarity, voice, and restraint.
The illustrative reference edits are never required as exact expected output.

Author: Luke Steuber
"""

import argparse
import json
from pathlib import Path
import sys


CORPUS = Path(__file__).parent / "fixtures" / "editorial.json"
REVIEW_QUESTIONS = [
    "Does the edit preserve facts, attribution, negation, uncertainty, conditions, and scope?",
    "Is the main point easier to find and understand?",
    "Does the edit retain the source's appropriate voice and intentional structure?",
    "Did the editor avoid unnecessary changes to already effective prose?",
]


def validate_corpus(corpus):
    errors = []
    seen = set()
    for case in corpus["cases"]:
        identity = case["id"]
        if identity in seen:
            errors.append(f"Duplicate case: {identity}")
        seen.add(identity)
        if case["split"] not in {"development", "holdout"}:
            errors.append(f"{identity}: unknown split")
        if case["action"] not in {"edit", "leave"}:
            errors.append(f"{identity}: unknown action")
        if case["action"] == "leave" and case["original"] != case["reference"]:
            errors.append(f"{identity}: unchanged reference must equal original")
        for token in case["preserve"]:
            for field in ("original", "reference"):
                if not token or token not in case[field]:
                    errors.append(f"{identity}: declared literal absent from {field}: {token!r}")
    return errors


def evaluate(corpus, candidates):
    errors = []
    known = {case["id"] for case in corpus["cases"]}
    for unknown in sorted(set(candidates) - known):
        errors.append(f"Unknown candidate: {unknown}")
    changed_leave_cases = []
    for case in corpus["cases"]:
        identity = case["id"]
        candidate = candidates.get(identity)
        if not isinstance(candidate, str):
            errors.append(f"{identity}: missing or non-text candidate")
            continue
        for token in case["preserve"]:
            if token not in candidate:
                errors.append(f"{identity}: missing declared literal: {token!r}")
        if case["action"] == "leave" and candidate != case["original"]:
            changed_leave_cases.append(identity)
    return {
        "literal_errors": errors,
        "changed_leave_cases_for_review": changed_leave_cases,
        "human_review_required": True,
        "review_questions": REVIEW_QUESTIONS,
        "limitation": "Literal checks are incomplete fidelity checks. They do not prove equivalent meaning or better writing.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", nargs="?", type=Path,
                        help="JSON object mapping every case ID to edited text")
    args = parser.parse_args()
    try:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        errors = validate_corpus(corpus)
        if errors:
            print(json.dumps({"corpus_errors": errors}, indent=2))
            return 1
        if args.candidates:
            candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
            if not isinstance(candidates, dict):
                raise ValueError("Candidates must be a JSON object mapping case IDs to text")
            result = evaluate(corpus, candidates)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return int(bool(result["literal_errors"]))
        print(json.dumps({"corpus_cases": len(corpus["cases"]),
                          "schema_valid": True,
                          "human_review_required": True}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Evaluation error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
