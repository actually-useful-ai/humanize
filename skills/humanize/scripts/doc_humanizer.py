#!/usr/bin/env python3
"""Contextual English prose diagnostics. Author: Luke Steuber.

The scanner never writes target files. All semantic editing belongs to the
agent workflow. Offsets are zero-based Unicode code points, end-exclusive;
line and column are one-based. No external runtime dependencies or network.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import difflib
import fnmatch
import json
from pathlib import Path
import re
import sys
import warnings

CATALOG_PATH = Path(__file__).resolve().parent.parent / 'references' / 'rules.json'
SUPPORTED = {'.md', '.markdown', '.txt'}
PROTECTED_NAMES = {'agents.md', 'claude.md', 'skill.md', 'license', 'license.md',
                   'license.txt', 'copying', 'notice', 'notice.md', 'changelog.md',
                   'changelog.txt', 'changelog.markdown'}
PROTECTED_DIRS = {'.git', '.claude', '.codex', '.cursor', '.antigravity', 'node_modules',
                  'vendor', 'dist', 'build', 'generated', '__pycache__', 'clinical', 'specs',
                  'specifications', '.venv', 'venv'}


@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    line: int
    column: int
    start: int
    end: int
    text: str
    severity: str
    message: str
    suggestion: str
    autofix: bool = False


# Older integrations can still import the name, but its fields changed in 2.0.
Indicator = Diagnostic


def masked_prose(content: str) -> str:
    """Conservatively mask Markdown syntax without changing offsets/newlines.

    This is a protection scanner, not a CommonMark parser. Ambiguous blocks,
    quotes, links and embedded HTML are deliberately excluded from diagnostics.
    HTML documents and source code are not supported file types.
    """
    masked = list(content)

    def hide(start: int, end: int) -> None:
        for pos in range(start, end):
            if content[pos] not in '\r\n':
                masked[pos] = '\x00'

    lines = content.splitlines(keepends=True)
    offset = 0
    fence = None
    front = None
    block = False
    html = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if index == 0 and stripped.lstrip('\ufeff') in {'---', '+++'}:
            front = stripped.lstrip('\ufeff')
            hide(offset, offset + len(line))
        elif front:
            hide(offset, offset + len(line))
            if stripped == front or (front == '---' and stripped == '...'):
                front = None
        elif fence:
            hide(offset, offset + len(line))
            close = re.match(r'^\s*([`~]+)\s*$', line)
            if close and set(close[1]) == {fence[0]} and len(close[1]) >= fence[1]:
                fence = None
        elif html:
            hide(offset, offset + len(line))
            if html == 'blank' and not stripped:
                html = None
            elif html != 'blank' and html in line.lower():
                html = None
        elif block and stripped:
            hide(offset, offset + len(line))
        else:
            block = False
            opening = re.match(r'^\s*(?:[-+*]\s+|\d+[.)]\s+)?(`{3,}|~{3,})(.*)$', line)
            if opening:
                fence = (opening[1][0], len(opening[1]))
                hide(offset, offset + len(line))
            elif re.match(r'^\s*>|^\s*\[[^\]]+\]:', line):
                block = True  # includes lazy quote / reference continuation
                hide(offset, offset + len(line))
            elif re.match(r'^(?: {4}|\t)', line):
                hide(offset, offset + len(line))
            elif re.search(r'<!--|<(?:script|style|pre|code|textarea)\b', line, re.I):
                tag = re.search(r'<!--|<(script|style|pre|code|textarea)\b', line, re.I)
                end = '-->' if tag[0] == '<!--' else '</' + tag[1].lower() + '>'
                hide(offset, offset + len(line))
                if end not in line[tag.end():].lower():
                    html = end
            elif re.match(r'^\s*</?[A-Za-z][\w:-]*(?:\s|>|/)', line):
                hide(offset, offset + len(line))
                html = 'blank'
        offset += len(line)

    # Code spans can cross lines. Only an equal-length backtick run closes one.
    i = 0
    while i < len(content):
        if masked[i] == '\x00':
            i += 1
            continue
        if content[i] == '\\' and i + 1 < len(content):
            hide(i, i + 2)
            i += 2
            continue
        if content[i] == '`':
            run = re.match(r'`+', content[i:])[0]
            end = re.search(r'(?<!`)' + re.escape(run) + r'(?!`)', content[i + len(run):])
            stop = i + len(run) + end.end() if end else len(content)
            hide(i, stop)
            i = stop
            continue
        if content[i] == '[' or (content[i] == '!' and content[i:i + 2] == '!['):
            # Protect complete nested labels and balanced destinations. An
            # ambiguous/unclosed label protects to end of its paragraph.
            start = i
            bracket = i + (content[i] == '!')
            depth = 1
            j = bracket + 1
            while j < len(content) and depth:
                if content[j] == '\\':
                    j += 2
                    continue
                if content[j] == '[':
                    depth += 1
                elif content[j] == ']':
                    depth -= 1
                j += 1
            if depth:
                paragraph_end = content.find('\n\n', start)
                j = paragraph_end if paragraph_end != -1 else len(content)
            elif j < len(content) and content[j] in '([':
                opener = content[j]
                closer = ')' if opener == '(' else ']'
                depth = 1
                j += 1
                while j < len(content) and depth:
                    if content[j] == '\\':
                        j += 2
                        continue
                    if content[j] == opener:
                        depth += 1
                    elif content[j] == closer:
                        depth -= 1
                    j += 1
            hide(start, min(j, len(content)))
            i = j
            continue
        if content[i] in {'"', '“', '‘', "'"} and (i == 0 or not content[i - 1].isalnum()):
            closer = {'“': '”', '‘': '’'}.get(content[i], content[i])
            end = i + 1
            paragraph = re.search(r'\r?\n[ \t]*\r?\n', content[end:])
            limit = end + paragraph.start() if paragraph else len(content)
            while end < limit:
                if content[end] == '\\':
                    end += 2
                    continue
                if content[end] == closer:
                    break
                end += 1
            if end < limit:
                hide(i, end + 1)
                i = end + 1
                continue
        if content[i] == '<':
            end = content.find('>', i + 1)
            if end != -1:
                # Inline paired HTML is opaque as well as its attributes.
                tag = re.match(r'<([A-Za-z][\w:-]*)\b', content[i:])
                if tag:
                    depth = 1
                    closing_end = None
                    for token in re.finditer(r'</?' + re.escape(tag[1]) + r'\b[^>]*>', content[end + 1:], re.I):
                        depth += -1 if token[0].startswith('</') else (0 if token[0].endswith('/>') else 1)
                        if depth == 0:
                            closing_end = end + 1 + token.end() - 1
                            break
                    if closing_end is not None:
                        end = closing_end
                    else:
                        newline = content.find('\n', end + 1)
                        end = newline - 1 if newline != -1 else len(content) - 1
                hide(i, end + 1)
                i = end + 1
                continue
        i += 1
    for match in re.finditer(r'(?:https?://|www\.)[^\s<>]+|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', content):
        hide(match.start(), match.end())
    return ''.join(masked)


def read_config(path: str | None) -> dict:
    if not path:
        return {}
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    allowed = {'profile', 'disabled_rules', 'allow_terms', 'exclude', 'audience', 'genre'}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ValueError('Config must be an object with profile, disabled_rules, allow_terms, exclude, audience or genre.')
    for key in {'disabled_rules', 'allow_terms', 'exclude'}:
        if key in config and (not isinstance(config[key], list) or not all(isinstance(x, str) and x for x in config[key])):
            raise ValueError(f'{key} must be a list of nonempty strings')
    for key in {'profile', 'audience', 'genre'}:
        if key in config and not isinstance(config[key], str):
            raise ValueError(f'{key} must be a string')
    return config


def protected_reason(path: Path, excludes=()) -> str | None:
    system_aliases = {Path('/var'), Path('/tmp'), Path('/etc')} if sys.platform == 'darwin' else set()
    if any(p.is_symlink() and p not in system_aliases for p in (path, *path.parents)):
        return 'symlinks are excluded'
    if path.name.lower() in PROTECTED_NAMES or path.name.lower().startswith(('license.', 'notice.')):
        return 'protected document'
    if any(part.lower() in PROTECTED_DIRS or part.startswith('.') for part in path.parts if part not in {'.', '..'}):
        return 'protected or hidden directory'
    if any(fnmatch.fnmatch(path.as_posix(), pattern) or path.match(pattern) for pattern in excludes):
        return 'excluded by configuration'
    return None


class DocumentHumanizer:
    def __init__(self, profile='standard', config=None):
        self.config = config or {}
        self.profile = self.config.get('profile', profile)
        if self.profile not in {'standard', 'luke'}:
            raise ValueError('Profile must be standard or luke')
        self.rules = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))['rules']
        unknown = set(self.config.get('disabled_rules', [])) - {r['id'] for r in self.rules}
        if unknown:
            raise ValueError('Unknown disabled rules: ' + ', '.join(sorted(unknown)))

    def scan_text(self, content: str, strict=False) -> list[Diagnostic]:
        masked = masked_prose(content)
        line_starts = [0] + [m.end() for m in re.finditer('\n', content)]
        allowed_spans = []
        for term in self.config.get('allow_terms', []):
            allowed_spans.extend((m.start(), m.end()) for m in re.finditer(re.escape(term), content, re.I))
        found = []
        for rule in self.rules:
            if self.profile not in rule['profiles'] or rule['id'] in self.config.get('disabled_rules', []):
                continue
            if rule['strict'] and not strict:
                continue
            for match in re.finditer(rule['pattern'], masked, re.I):
                start, end = match.span()
                if '\x00' in masked[start:end] or any(start < b and end > a for a, b in allowed_spans):
                    continue
                line = bisect_right(line_starts, start)
                found.append(Diagnostic(rule['id'], line, start - line_starts[line - 1] + 1,
                                        start, end, content[start:end], rule['severity'],
                                        rule['message'], rule['suggestion']))
        return sorted(found, key=lambda item: (item.start, item.end, item.rule_id))

    def scan_file(self, filepath: str, strict=False) -> dict[str, list[Diagnostic]]:
        path = Path(filepath).absolute()
        reason = protected_reason(path, self.config.get('exclude', []))
        if reason:
            raise ValueError(f'{filepath}: {reason}')
        if path.suffix.lower() not in SUPPORTED:
            raise ValueError(f'Unsupported file type: {path.suffix or "none"}')
        content = path.read_bytes().decode('utf-8')
        grouped = {}
        for item in self.scan_text(content, strict):
            grouped.setdefault(item.rule_id, []).append(item)
        return grouped

    def apply_transforms(self, content: str, confidence_threshold=None) -> str:
        """Compatibility no-op. No lexical rewrite has an automatic safety contract."""
        if confidence_threshold is not None:
            warnings.warn('Confidence thresholds were removed in 2.0; text is unchanged.', DeprecationWarning, stacklevel=2)
        return content

    def generate_diff(self, original: str, transformed: str) -> str:
        return ''.join(difflib.unified_diff(original.splitlines(keepends=True), transformed.splitlines(keepends=True),
                                            fromfile='original', tofile='edited'))

    def batch_process(self, file_paths, parallel=True, max_workers=4):
        def scan(path):
            try:
                return path, self.scan_file(path)
            except (OSError, ValueError, UnicodeError) as error:
                return path, {'error': str(error)}
        if max_workers < 1:
            raise ValueError('max_workers must be positive')
        paths = sorted(set(map(str, file_paths)))
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                return dict(executor.map(scan, paths))
        return dict(map(scan, paths))


def select_files(targets, excludes=()):
    selected, skipped, errors = {}, {}, {}
    def visit(path):
        path = path.absolute()
        name = str(path)
        reason = protected_reason(path, excludes)
        if reason:
            skipped[name] = reason
        elif not path.exists():
            errors[name] = 'path does not exist'
        elif path.is_dir():
            try:
                for child in sorted(path.iterdir()):
                    visit(child)
            except OSError as error:
                errors[name] = str(error)
        elif not path.is_file():
            skipped[name] = 'not a regular file'
        elif path.suffix.lower() not in SUPPORTED:
            skipped[name] = 'unsupported file type'
        else:
            selected[name] = path
    for target in targets:
        visit(Path(target))
    return [selected[k] for k in sorted(selected)], skipped, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description='Review English prose while preserving source files.')
    parser.add_argument('command', choices=['scan', 'batch', 'fix', 'diff', 'rules'])
    parser.add_argument('files', nargs='*')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--strict', action='store_true', help='Include contextual suggestions; never grants write access')
    parser.add_argument('--profile', choices=['standard', 'luke'])
    parser.add_argument('--config', help='Explicit local JSON configuration')
    parser.add_argument('--check', action='store_true', help='Exit 1 for findings; operational errors exit 2')
    parser.add_argument('--dry-run', action='store_true', help='Accepted for compatibility; all commands preserve files')
    parser.add_argument('--parallel', action='store_true', help='Scan files concurrently with stable output ordering')
    parser.add_argument('--max-workers', type=int, default=4)
    parser.add_argument('--confidence', help=argparse.SUPPRESS)
    parser.add_argument('--threshold', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.confidence is not None or args.threshold is not None:
        parser.error('Numeric confidence was removed in 2.0. Use --strict or --check; no semantic fixes are automatic.')
    if args.max_workers < 1 or args.max_workers > 32:
        parser.error('--max-workers must be between 1 and 32')
    try:
        config = read_config(args.config)
        if args.profile:
            config['profile'] = args.profile
        humanizer = DocumentHumanizer(config=config)
        if args.command == 'rules':
            if args.files:
                parser.error('rules does not take file targets')
            print(json.dumps({'schema_version': 1, 'rules': humanizer.rules}, ensure_ascii=False, indent=2))
            return 0
        targets = args.files or [p for p in ['README.md', 'CONTRIBUTING.md', 'docs'] if Path(p).exists()]
        paths, skipped, errors = select_files(targets, config.get('exclude', []))
        def scan(path):
            try:
                findings = humanizer.scan_file(str(path), args.strict)
                return {'path': str(path), 'status': 'scanned', 'diagnostics': [asdict(d) for group in findings.values() for d in group]}
            except (OSError, ValueError, UnicodeError) as error:
                return {'path': str(path), 'status': 'error', 'reason': str(error), 'diagnostics': []}
        if args.parallel:
            with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                results = list(executor.map(scan, paths))
        else:
            results = list(map(scan, paths))
        results += [{'path': p, 'status': 'skipped', 'reason': why, 'diagnostics': []} for p, why in skipped.items()]
        results += [{'path': p, 'status': 'error', 'reason': why, 'diagnostics': []} for p, why in errors.items()]
        results.sort(key=lambda r: r['path'])
        for result in results:
            result['diagnostics'].sort(key=lambda d: (d['start'], d['end'], d['rule_id']))
        count = sum(len(r['diagnostics']) for r in results)
        scanned = sum(r['status'] == 'scanned' for r in results)
        report = {'schema_version': 2, 'command': args.command, 'profile': humanizer.profile,
                  'context': {k: config[k] for k in ('audience', 'genre') if k in config},
                  'changed_files': 0, 'findings': count, 'files': results,
                  'editing': 'Contextual agent editing required; no automatic text changes.'}
        if args.format == 'json':
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            for result in results:
                print(f"{result['path']}: {result['status']}" + (': ' + result['reason'] if 'reason' in result else ''))
                for d in result['diagnostics']:
                    print(f"  {d['line']}:{d['column']} {d['rule_id']} {d['severity']}: {d['message']}\n    {d['suggestion']}")
            print(f'{scanned} files scanned; {count} suggestions; 0 files changed.')
            if args.command in {'fix', 'diff'}:
                print(report['editing'])
        if not scanned or any(r['status'] == 'error' for r in results):
            return 2
        return 1 if args.check and count else 0
    except (OSError, ValueError, UnicodeError) as error:
        print(f'Humanize: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
