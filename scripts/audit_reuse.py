#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Sequence, Set, Tuple


SOURCE_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.vue'}
LIBRARIES = (
    '@fameex/ui',
    '@heroui/react',
    'antd',
    'element-ui',
    'element-plus',
)
DEFAULT_LIMIT = 100
MAX_SOURCE_LENGTH = 240
COMPONENT_IMPORT_PATTERN = re.compile(
    r"\b(?:from\s*|import\s*)['\"](?P<name>"
    + '|'.join(re.escape(library) for library in LIBRARIES)
    + r")[\"']",
)
NATIVE_CONTROL_PATTERN = re.compile(
    r'<(?P<name>button|input|select|textarea)\b',
)
IMAGE_PATTERN = re.compile(r'<img\b')
ICON_PATTERN = re.compile(r'icon-\[fx--[A-Za-z0-9_-]+\]')


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError('must be zero or greater')
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='List reuse candidates for agent review.',
    )
    parser.add_argument('--repo-root', required=True, type=Path)
    parser.add_argument(
        '--limit',
        type=non_negative_int,
        default=DEFAULT_LIMIT,
        help='Maximum candidates to print (default: %(default)s).',
    )
    parser.add_argument('targets', nargs='+', type=Path)
    parser.add_argument('--json', action='store_true', dest='as_json')
    return parser.parse_args()


def source_files(targets: Sequence[Path]) -> List[Path]:
    files: Set[Path] = set()
    for target in targets:
        path = target.expanduser().resolve()
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS:
            files.add(path)
        elif path.is_dir():
            files.update(
                candidate
                for candidate in path.rglob('*')
                if candidate.is_file()
                and candidate.suffix.lower() in SOURCE_EXTENSIONS
            )
        elif not path.exists():
            raise ValueError('target does not exist: {}'.format(target))
    return sorted(files)


def load_available_icons(repo_root: Path) -> Set[str]:
    icon_list = repo_root / 'packages/icon/output/icon-list.json'
    if not icon_list.is_file():
        return set()
    try:
        payload = json.loads(icon_list.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return set()
    if isinstance(payload, list):
        return {item for item in payload if isinstance(item, str)}
    if isinstance(payload, dict):
        return {item for item in payload if isinstance(item, str)}
    return set()


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def compact_source(line: str) -> str:
    source = line.strip()
    if len(source) <= MAX_SOURCE_LENGTH:
        return source
    return source[: MAX_SOURCE_LENGTH - 3] + '...'


def line_candidates(
    path: Path,
    repo_root: Path,
    line_number: int,
    line: str,
    available_icons: Set[str],
) -> List[Dict[str, object]]:
    file_name = display_path(path, repo_root)
    source = compact_source(line)
    matches: List[Tuple[int, int, Dict[str, object]]] = []

    def add_candidate(
        column: int,
        order: int,
        kind: str,
        name: str,
        available: object = None,
    ) -> None:
        candidate: Dict[str, object] = {
            'kind': kind,
            'name': name,
            'file': file_name,
            'line': line_number,
            'source': source,
        }
        if available is not None:
            candidate['available'] = available
        matches.append((column, order, candidate))

    for match in COMPONENT_IMPORT_PATTERN.finditer(line):
        add_candidate(match.start(), 0, 'component-import', match.group('name'))
    for match in NATIVE_CONTROL_PATTERN.finditer(line):
        add_candidate(match.start(), 1, 'native-control', match.group('name'))
    for match in IMAGE_PATTERN.finditer(line):
        add_candidate(match.start(), 2, 'image', 'img')
    for match in ICON_PATTERN.finditer(line):
        icon = match.group(0)
        add_candidate(
            match.start(),
            3,
            'icon-literal',
            icon,
            icon in available_icons,
        )
    return [item[2] for item in sorted(matches, key=lambda item: item[:2])]


def audit(repo_root: Path, targets: Sequence[Path]) -> List[Dict[str, object]]:
    available_icons = load_available_icons(repo_root)
    candidates: List[Dict[str, object]] = []
    for path in source_files(targets):
        content = path.read_text(encoding='utf-8', errors='ignore')
        for line_number, line in enumerate(content.splitlines(), start=1):
            candidates.extend(
                line_candidates(
                    path,
                    repo_root,
                    line_number,
                    line,
                    available_icons,
                )
            )
    return candidates


def result_payload(
    candidates: Sequence[Dict[str, object]],
    limit: int,
) -> Dict[str, object]:
    shown = list(candidates[:limit])
    return {
        'candidates': shown,
        'limit': limit,
        'total': len(candidates),
        'omitted': len(candidates) - len(shown),
    }


def print_plain(payload: Dict[str, object]) -> None:
    print(
        'Reuse audit candidates: showing {shown} of {total}; '
        'omitted {omitted}; limit {limit}'.format(
            shown=len(payload['candidates']),
            **payload,
        )
    )
    for candidate in payload['candidates']:
        availability = ''
        if 'available' in candidate:
            availability = ' available={}'.format(
                str(candidate['available']).lower(),
            )
        print(
            '{file}:{line} [{kind}] {name}{availability} | {source}'.format(
                availability=availability,
                **candidate,
            )
        )
    print(
        'Candidates only; agent judgement required for comments, strings, '
        'fixtures, and indirect usage.',
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    try:
        candidates = audit(repo_root, args.targets)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    payload = result_payload(candidates, args.limit)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    else:
        print_plain(payload)
    return 0


if __name__ == '__main__':
    sys.exit(main())
