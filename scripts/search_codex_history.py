#!/usr/bin/env python3
"""Search direct user messages in local Codex JSONL history, read-only."""

import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import sys


EXCLUDED_PREFIXES = (
    '<recommended_plugins>',
    '<skill>',
    '<environment_context>',
    '<codex_internal_context',
    '<permissions',
    '<developer',
    '# agents.md',
    '## agents.md',
)
MAX_EXCERPT = 280


def parse_args():
    parser = argparse.ArgumentParser(
        description='Search bounded, direct user messages in Codex history.',
    )
    parser.add_argument('--ticket')
    parser.add_argument('--route')
    parser.add_argument(
        '--term',
        action='append',
        default=[],
        help='Additional exact case-insensitive term; repeat as needed.',
    )
    parser.add_argument('--since', type=date.fromisoformat)
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument(
        '--root',
        action='append',
        type=Path,
        help='Override history root; repeat as needed.',
    )
    parser.add_argument('--json', action='store_true')
    return parser.parse_args()


def default_roots():
    codex_root = Path.home() / '.codex'
    return [codex_root / 'sessions', codex_root / 'archived_sessions']


def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def extract_user_text(payload):
    if (
        not isinstance(payload, dict)
        or payload.get('type') != 'message'
        or payload.get('role') != 'user'
    ):
        return None
    texts = []
    for item in payload.get('content', []):
        if (
            isinstance(item, dict)
            and item.get('type') == 'input_text'
            and isinstance(item.get('text'), str)
        ):
            texts.append(item['text'])
    text = '\n'.join(texts).strip()
    if not text:
        return None
    lowered = text.lower()
    if any(lowered.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return None
    return text


def excerpt(text):
    compact = re.sub(r'\s+', ' ', text).strip()
    if len(compact) <= MAX_EXCERPT:
        return compact
    return compact[: MAX_EXCERPT - 1].rstrip() + '…'


def iter_jsonl_files(roots):
    seen = set()
    for root in roots:
        expanded = root.expanduser()
        if expanded.is_file() and expanded.suffix == '.jsonl':
            candidates = [expanded]
        elif expanded.is_dir():
            candidates = expanded.rglob('*.jsonl')
        else:
            continue
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield resolved


def read_matches(path, filters, since):
    session_id = path.stem
    results = []
    try:
        history_file = path.open(errors='replace')
    except OSError:
        return results
    with history_file:
        for line_number, line in enumerate(history_file, 1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get('type') == 'session_meta':
                payload = item.get('payload', {})
                session_id = payload.get('id') or session_id
                continue
            if item.get('type') != 'response_item':
                continue
            text = extract_user_text(item.get('payload'))
            if text is None:
                continue
            timestamp = parse_timestamp(item.get('timestamp'))
            if since and (timestamp is None or timestamp.date() < since):
                continue
            lowered = text.lower()
            if any(
                value.lower() not in lowered
                for value in filters.values()
            ):
                continue
            fingerprint = hashlib.sha256(
                f"{item.get('timestamp', '')}\0{text}".encode()
            ).hexdigest()
            results.append(
                {
                    'timestamp': item.get('timestamp'),
                    'session_id': session_id,
                    'source': str(path),
                    'line': line_number,
                    'excerpt': excerpt(text),
                    'matched': filters,
                    '_fingerprint': fingerprint,
                    '_sort_value': (
                        timestamp.timestamp()
                        if timestamp is not None
                        else float('-inf')
                    ),
                }
            )
    return results


def emit_text(matches):
    if not matches:
        print('No matching direct user messages.')
        return
    for match in matches:
        print(
            f"{match['timestamp'] or 'unknown'} "
            f"{match['session_id']} {match['source']}:{match['line']}"
        )
        print(f"  {match['excerpt']}")


def main():
    args = parse_args()
    if args.limit < 1:
        print('--limit must be greater than zero.', file=sys.stderr)
        return 2
    filters = {}
    if args.ticket:
        filters['ticket'] = args.ticket
    if args.route:
        filters['route'] = args.route
    for index, term in enumerate(args.term, 1):
        filters[f'term_{index}'] = term
    if not filters:
        print(
            'Provide --ticket, --route, or at least one --term.',
            file=sys.stderr,
        )
        return 2

    matches = []
    roots = args.root or default_roots()
    for path in iter_jsonl_files(roots):
        matches.extend(read_matches(path, filters, args.since))
    matches.sort(
        key=lambda item: item['_sort_value'],
        reverse=True,
    )
    deduplicated = []
    fingerprints = set()
    for match in matches:
        fingerprint = match.pop('_fingerprint')
        match.pop('_sort_value')
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        deduplicated.append(match)
        if len(deduplicated) == args.limit:
            break

    if args.json:
        print(
            json.dumps(
                {
                    'query': {
                        'filters': filters,
                        'since': (
                            args.since.isoformat() if args.since else None
                        ),
                        'limit': args.limit,
                    },
                    'count': len(deduplicated),
                    'matches': deduplicated,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        emit_text(deduplicated)
    return 0


if __name__ == '__main__':
    sys.exit(main())
