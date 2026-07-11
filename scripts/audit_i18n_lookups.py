#!/usr/bin/env python3
import argparse
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
HEX_DIGITS = frozenset('0123456789abcdefABCDEF')
SIMPLE_ESCAPES = {
    "'": "'",
    '"': '"',
    '\\': '\\',
    '/': '/',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'b': '\b',
    'f': '\f',
    'v': '\v',
    '0': '\0',
}


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
    state = 'normal'
    escaped = False
    pairs = {')': '(', ']': '[', '}': '{'}
    index = start
    while index < len(content):
        character = content[index]
        next_character = content[index + 1] if index + 1 < len(content) else ''
        if state in {'single', 'double', 'template'}:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif (
                (state == 'single' and character == "'")
                or (state == 'double' and character == '"')
                or (state == 'template' and character == '`')
            ):
                state = 'normal'
        elif state == 'line-comment':
            if character in '\r\n':
                state = 'normal'
        elif state == 'block-comment':
            if character == '*' and next_character == '/':
                state = 'normal'
                index += 1
        elif character == '/' and next_character == '/':
            state = 'line-comment'
            index += 1
        elif character == '/' and next_character == '*':
            state = 'block-comment'
            index += 1
        elif character == "'":
            state = 'single'
        elif character == '"':
            state = 'double'
        elif character == '`':
            state = 'template'
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


def is_identifier_character(character: str) -> bool:
    return bool(character) and (
        character.isalnum() or character in {'_', '$'}
    )


def translation_call_starts(content: str) -> List[int]:
    starts: List[int] = []
    state = 'normal'
    escaped = False
    interpolation_depths: List[int] = []
    last_significant = ''
    index = 0
    while index < len(content):
        character = content[index]
        next_character = content[index + 1] if index + 1 < len(content) else ''
        if state in {'single', 'double'}:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif (
                (state == 'single' and character == "'")
                or (state == 'double' and character == '"')
            ):
                state = 'normal'
        elif state == 'template':
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == '`':
                state = 'normal'
                last_significant = '`'
            elif character == '$' and next_character == '{':
                interpolation_depths.append(1)
                state = 'normal'
                last_significant = '{'
                index += 1
        elif state == 'line-comment':
            if character in '\r\n':
                state = 'normal'
        elif state == 'block-comment':
            if character == '*' and next_character == '/':
                state = 'normal'
                index += 1
        elif character == '/' and next_character == '/':
            state = 'line-comment'
            index += 1
        elif character == '/' and next_character == '*':
            state = 'block-comment'
            index += 1
        elif character == "'":
            state = 'single'
            last_significant = "'"
        elif character == '"':
            state = 'double'
            last_significant = '"'
        elif character == '`':
            state = 'template'
            last_significant = '`'
        elif interpolation_depths and character == '{':
            interpolation_depths[-1] += 1
            last_significant = character
        elif interpolation_depths and character == '}':
            interpolation_depths[-1] -= 1
            last_significant = character
            if interpolation_depths[-1] == 0:
                interpolation_depths.pop()
                state = 'template'
        elif character == 't':
            previous = content[index - 1] if index else ''
            cursor = index + 1
            while cursor < len(content) and content[cursor].isspace():
                cursor += 1
            if (
                previous != '.'
                and not is_identifier_character(previous)
                and last_significant != '.'
                and cursor < len(content)
                and content[cursor] == '('
            ):
                starts.append(cursor + 1)
            last_significant = character
        elif not character.isspace():
            last_significant = character
        index += 1
    return starts


def strip_comments(content: str) -> str:
    stripped = list(content)
    state = 'normal'
    escaped = False
    index = 0
    while index < len(content):
        character = content[index]
        next_character = content[index + 1] if index + 1 < len(content) else ''
        if state in {'single', 'double', 'template'}:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif (
                (state == 'single' and character == "'")
                or (state == 'double' and character == '"')
                or (state == 'template' and character == '`')
            ):
                state = 'normal'
        elif state == 'line-comment':
            if character in '\r\n':
                state = 'normal'
            else:
                stripped[index] = ' '
        elif state == 'block-comment':
            if character == '*' and next_character == '/':
                stripped[index] = ' '
                stripped[index + 1] = ' '
                state = 'normal'
                index += 1
            elif character not in '\r\n':
                stripped[index] = ' '
        elif character == '/' and next_character == '/':
            stripped[index] = ' '
            stripped[index + 1] = ' '
            state = 'line-comment'
            index += 1
        elif character == '/' and next_character == '*':
            stripped[index] = ' '
            stripped[index + 1] = ' '
            state = 'block-comment'
            index += 1
        elif character == "'":
            state = 'single'
        elif character == '"':
            state = 'double'
        elif character == '`':
            state = 'template'
        index += 1
    return ''.join(stripped)


def decode_hex_escape(
    body: str,
    start: int,
    length: int,
    escape_name: str,
) -> str:
    end = start + length
    digits = body[start:end]
    if len(digits) != length or any(digit not in HEX_DIGITS for digit in digits):
        raise ValueError(
            'invalid JavaScript string literal: invalid {}'.format(escape_name),
        )
    return chr(int(digits, 16))


def literal_value(literal: str) -> str:
    body = literal[1:-1]
    decoded: List[str] = []
    index = 0
    while index < len(body):
        character = body[index]
        if character in {'\r', '\n', '\u2028', '\u2029'}:
            raise ValueError(
                'invalid JavaScript string literal: unescaped line terminator',
            )
        if character != '\\':
            decoded.append(character)
            index += 1
            continue

        index += 1
        if index >= len(body):
            raise ValueError(
                'invalid JavaScript string literal: trailing backslash',
            )
        escape = body[index]
        if escape in {'\n', '\u2028', '\u2029'}:
            index += 1
            continue
        if escape == '\r':
            index += 2 if index + 1 < len(body) and body[index + 1] == '\n' else 1
            continue
        if escape in SIMPLE_ESCAPES:
            if escape == '0' and index + 1 < len(body) and body[index + 1].isdigit():
                raise ValueError(
                    'invalid JavaScript string literal: legacy octal escape',
                )
            decoded.append(SIMPLE_ESCAPES[escape])
            index += 1
            continue
        if escape == 'x':
            decoded.append(decode_hex_escape(body, index + 1, 2, '\\x escape'))
            index += 3
            continue
        if escape == 'u':
            if index + 1 < len(body) and body[index + 1] == '{':
                closing = body.find('}', index + 2)
                digits = body[index + 2:closing] if closing != -1 else ''
                if (
                    not digits
                    or any(digit not in HEX_DIGITS for digit in digits)
                    or int(digits, 16) > 0x10FFFF
                ):
                    raise ValueError(
                        'invalid JavaScript string literal: invalid \\u{} escape',
                    )
                decoded.append(chr(int(digits, 16)))
                index = closing + 1
                continue
            decoded.append(decode_hex_escape(body, index + 1, 4, '\\u escape'))
            index += 5
            continue
        raise ValueError(
            'invalid JavaScript string literal: unsupported escape \\{}'.format(
                escape,
            ),
        )
    return ''.join(decoded)


def keys_from_argument(argument: str) -> Set[str]:
    argument = strip_comments(argument)
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
        for start in translation_call_starts(content):
            referenced.update(keys_from_argument(first_argument(content, start)))
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
