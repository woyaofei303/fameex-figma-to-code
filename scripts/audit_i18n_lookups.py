#!/usr/bin/env python3
import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Sequence, Set


SOURCE_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx'}
STRING_LITERAL = r'''(?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")'''
LITERAL_PATTERN = re.compile(r'^\s*(' + STRING_LITERAL + r')\s*$', re.DOTALL)
CONDITIONAL_PATTERN = re.compile(
    r'^\s*[^?]+\?\s*(?P<yes>'
    + STRING_LITERAL
    + r')\s*:\s*(?P<no>'
    + STRING_LITERAL
    + r')\s*$',
    re.DOTALL,
)
TRANSLATION_CALL_PATTERN = re.compile(r'\bt\s*\(')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Compare static translation lookups with namespace leaves.',
    )
    parser.add_argument('--namespace-json', required=True, type=Path)
    parser.add_argument(
        '--source',
        required=True,
        action='append',
        type=Path,
        help='Source file or directory. Repeat for multiple sources.',
    )
    parser.add_argument(
        '--key',
        action='append',
        default=[],
        help='Exact expansion for a computed or template lookup. Repeat as needed.',
    )
    parser.add_argument('--json', action='store_true', dest='as_json')
    return parser.parse_args()


def load_namespace(path: Path) -> Dict[str, object]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(
            'namespace JSON is not an existing file: {}'.format(resolved),
        )
    try:
        payload = json.loads(resolved.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        raise ValueError('invalid JSON in {}: {}'.format(resolved, error))
    except OSError as error:
        raise ValueError('cannot read namespace JSON {}: {}'.format(resolved, error))
    if not isinstance(payload, dict):
        raise ValueError('namespace JSON root must be a JSON object: {}'.format(resolved))
    return payload


def flatten_leaves(payload: Dict[str, object]) -> Set[str]:
    leaves: Set[str] = set()

    def visit(value: object, prefix: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_prefix = '{}.{}'.format(prefix, key) if prefix else key
                visit(child, child_prefix)
            return
        if prefix:
            leaves.add(prefix)

    visit(payload, '')
    return leaves


def source_files(sources: Sequence[Path]) -> List[Path]:
    files: Set[Path] = set()
    for source in sources:
        path = source.expanduser().resolve()
        if not path.exists():
            raise ValueError('source path does not exist: {}'.format(path))
        if path.is_file():
            if path.suffix.lower() in SOURCE_EXTENSIONS:
                files.add(path)
            continue
        if not path.is_dir():
            raise ValueError('source path is not a file or directory: {}'.format(path))
        files.update(
            candidate
            for candidate in path.rglob('*')
            if candidate.is_file()
            and candidate.suffix.lower() in SOURCE_EXTENSIONS
        )
    if not files:
        raise ValueError('no supported source files found')
    return sorted(files)


def first_argument(content: str, start: int) -> str:
    nesting: List[str] = []
    quote = ''
    escaped = False
    pairs = {')': '(', ']': '[', '}': '{'}
    index = start
    while index < len(content):
        character = content[index]
        if quote:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == quote:
                quote = ''
        elif character in "'\"`":
            quote = character
        elif character in '([{':
            nesting.append(character)
        elif character in ')]}':
            if character == ')' and not nesting:
                return content[start:index]
            if nesting and nesting[-1] == pairs[character]:
                nesting.pop()
        elif character == ',' and not nesting:
            return content[start:index]
        index += 1
    return content[start:]


def literal_value(literal: str) -> str:
    return ast.literal_eval(literal)


def keys_from_argument(argument: str) -> Set[str]:
    literal_match = LITERAL_PATTERN.fullmatch(argument)
    if literal_match:
        return {literal_value(literal_match.group(1))}

    conditional_match = CONDITIONAL_PATTERN.fullmatch(argument)
    if conditional_match:
        return {
            literal_value(conditional_match.group('yes')),
            literal_value(conditional_match.group('no')),
        }
    return set()


def referenced_keys(paths: Sequence[Path], explicit_keys: Sequence[str]) -> Set[str]:
    referenced = set(explicit_keys)
    for path in paths:
        try:
            content = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as error:
            raise ValueError('cannot read source {}: {}'.format(path, error))
        for match in TRANSLATION_CALL_PATTERN.finditer(content):
            referenced.update(keys_from_argument(first_argument(content, match.end())))
    return referenced


def result_payload(leaves: Set[str], referenced: Set[str]) -> Dict[str, object]:
    return {
        'referenced_count': len(referenced),
        'leaf_count': len(leaves),
        'missing_keys': sorted(referenced - leaves),
        'unused_keys': sorted(leaves - referenced),
    }


def print_plain(payload: Dict[str, object]) -> None:
    print(
        'i18n lookup audit: referenced={referenced_count} '
        'leaves={leaf_count} missing={missing} unused={unused}'.format(
            missing=len(payload['missing_keys']),
            unused=len(payload['unused_keys']),
            **payload,
        )
    )
    for key in payload['missing_keys']:
        print('missing:{}'.format(key))
    for key in payload['unused_keys']:
        print('unused:{}'.format(key))


def main() -> int:
    args = parse_args()
    try:
        leaves = flatten_leaves(load_namespace(args.namespace_json))
        paths = source_files(args.source)
        referenced = referenced_keys(paths, args.key)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    payload = result_payload(leaves, referenced)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    else:
        print_plain(payload)
    return 1 if payload['missing_keys'] or payload['unused_keys'] else 0


if __name__ == '__main__':
    sys.exit(main())
