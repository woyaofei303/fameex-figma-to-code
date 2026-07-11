#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple


SOURCE_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.vue'}
LIBRARIES = (
    '@fameex/ui',
    '@heroui/react',
    'antd',
    'element-ui',
    'element-plus',
)
NATIVE_CONTROLS = ('button', 'input', 'select', 'textarea')
IMPORT_PATTERN = re.compile(
    r"\bimport\s+(?P<clause>(?:(?!\bfrom\s*['\"]).)*?)"
    r"\s+from\s*['\"](?P<library>"
    + '|'.join(re.escape(library) for library in LIBRARIES)
    + r")[\"']",
    re.DOTALL,
)
ICON_PATTERN = re.compile(r'icon-\[fx--[A-Za-z0-9_-]+\]')
CLASS_ATTRIBUTE_PATTERN = re.compile(
    r'(?:^|\s)(?:class|className|:class|v-bind:class)\s*=\s*$',
)
TAG_START_PATTERN = re.compile(r'<(?P<closing>/)?(?P<name>[A-Za-z][\w:.-]*)')
VOID_ELEMENTS = {
    'area',
    'base',
    'br',
    'col',
    'embed',
    'hr',
    'img',
    'input',
    'link',
    'meta',
    'param',
    'source',
    'track',
    'wbr',
}


class StringToken(NamedTuple):
    start: int
    value: str
    class_context: bool


class LexedSource(NamedTuple):
    structural: str
    strings: List[StringToken]
    class_expression_spans: List[Tuple[int, int]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Audit source files for reusable UI components and native controls.',
    )
    parser.add_argument('--repo-root', required=True, type=Path)
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


def imported_components(clause: str) -> Iterable[str]:
    if re.match(r'type\b', clause.lstrip()):
        return

    named_match = re.search(r'\{(.*?)\}', clause, re.DOTALL)
    if named_match:
        for item in named_match.group(1).split(','):
            imported_name = item.strip()
            if re.match(r'type\b', imported_name):
                continue
            imported_name = re.split(r'\s+as\s+', imported_name, maxsplit=1)[0]
            if re.fullmatch(r'[A-Za-z_$][\w$]*', imported_name):
                yield imported_name

    default_clause = clause.split('{', maxsplit=1)[0].rstrip(' ,\n\t')
    if default_clause and not default_clause.startswith(('*', 'type ')):
        default_name = default_clause.split(',', maxsplit=1)[0].strip()
        if re.fullmatch(r'[A-Za-z_$][\w$]*', default_name):
            yield default_name


def hidden_text(value: str) -> str:
    return ''.join('\n' if character == '\n' else ' ' for character in value)


def consume_string(content: str, start: int) -> Tuple[int, str]:
    quote = content[start]
    index = start + 1
    while index < len(content):
        if content[index] == '\\' and index + 1 < len(content):
            index += 2
            continue
        if content[index] == quote:
            return index + 1, content[start + 1 : index]
        index += 1
    return len(content), content[start + 1 :]


def consume_comment(content: str, start: int, terminator: str) -> int:
    end = content.find(terminator, start + 2)
    return len(content) if end == -1 else end + len(terminator)


def regex_can_start(structural: Sequence[str]) -> bool:
    prefix = ''.join(structural[-120:]).rstrip()
    if not prefix:
        return True
    if prefix.endswith('=>'):
        return True
    if prefix[-1] in '=([{,:;!?&|~+-*%^':
        return True
    return bool(
        re.search(
            r'\b(?:case|delete|in|instanceof|new|of|return|throw|typeof|void|yield)$',
            prefix,
        )
    )


def consume_regex(content: str, start: int) -> int:
    index = start + 1
    in_character_class = False
    while index < len(content):
        character = content[index]
        if character == '\\' and index + 1 < len(content):
            index += 2
            continue
        if character == '[':
            in_character_class = True
        elif character == ']':
            in_character_class = False
        elif character == '/' and not in_character_class:
            index += 1
            while index < len(content) and content[index].isalpha():
                index += 1
            return index
        elif character == '\n':
            return start + 1
        index += 1
    return start + 1


def tag_at(content: str, index: int) -> Optional[Tuple[bool, str]]:
    if content.startswith('</>', index):
        return True, ''
    if content.startswith('<>', index):
        return False, ''
    match = TAG_START_PATTERN.match(content, index)
    if not match:
        return None
    return bool(match.group('closing')), match.group('name')


def lex_source(content: str) -> LexedSource:
    structural: List[str] = []
    strings: List[StringToken] = []
    class_expression_spans: List[Tuple[int, int]] = []
    element_parent_modes: List[str] = []
    mode = 'code'
    raw_tag: Optional[str] = None
    jsx_expression_depth = 0
    tag_parent_mode = 'code'
    tag_closing = False
    tag_name = ''
    tag_buffer = ''
    tag_expression_depth = 0
    class_binding_depth: Optional[int] = None
    class_expression_start: Optional[int] = None
    index = 0

    def hide(end: int, include_in_tag: bool = False) -> None:
        nonlocal index, tag_buffer
        masked = hidden_text(content[index:end])
        structural.extend(masked)
        if include_in_tag:
            tag_buffer += masked
        index = end

    def begin_tag(closing: bool, name: str) -> None:
        nonlocal mode, tag_parent_mode, tag_closing, tag_name
        nonlocal tag_buffer, tag_expression_depth
        nonlocal class_binding_depth, class_expression_start
        tag_parent_mode = mode
        tag_closing = closing
        tag_name = name
        tag_buffer = ''
        tag_expression_depth = 0
        class_binding_depth = None
        class_expression_start = None
        mode = 'tag'

    while index < len(content):
        if mode == 'raw_text':
            closing = tag_at(content, index)
            if closing and closing == (True, raw_tag or ''):
                begin_tag(*closing)
                continue
            hide(index + 1)
            continue

        if mode == 'jsx_text':
            if content.startswith('<!--', index):
                hide(consume_comment(content, index, '-->'))
                continue
            tag = tag_at(content, index)
            if tag:
                begin_tag(*tag)
                continue
            if content[index] == '{':
                structural.append('{')
                jsx_expression_depth = 1
                mode = 'code'
                index += 1
                continue
            hide(index + 1)
            continue

        if mode == 'code' and raw_tag == 'script':
            closing = tag_at(content, index)
            if closing == (True, 'script'):
                begin_tag(*closing)
                continue

        if content.startswith('<!--', index):
            hide(
                consume_comment(content, index, '-->'),
                include_in_tag=mode == 'tag',
            )
            continue
        if content.startswith('//', index):
            newline = content.find('\n', index + 2)
            hide(
                len(content) if newline == -1 else newline,
                include_in_tag=mode == 'tag',
            )
            continue
        if content.startswith('/*', index):
            hide(
                consume_comment(content, index, '*/'),
                include_in_tag=mode == 'tag',
            )
            continue

        character = content[index]
        if character in ("'", '"', '`'):
            end, value = consume_string(content, index)
            class_context = bool(
                mode == 'tag'
                and (
                    class_binding_depth is not None
                    or CLASS_ATTRIBUTE_PATTERN.search(tag_buffer)
                )
            )
            strings.append(StringToken(index, value, class_context))
            hide(end, include_in_tag=mode == 'tag')
            continue

        if character == '/' and (
            mode == 'code' or (mode == 'tag' and tag_expression_depth > 0)
        ) and regex_can_start(structural):
            end = consume_regex(content, index)
            if end > index + 1:
                hide(end, include_in_tag=mode == 'tag')
                continue

        if mode == 'code':
            tag = tag_at(content, index)
            if tag:
                begin_tag(*tag)
                continue

        structural.append(character)

        if mode == 'code':
            if jsx_expression_depth > 0:
                if character == '{':
                    jsx_expression_depth += 1
                elif character == '}':
                    jsx_expression_depth -= 1
                    if jsx_expression_depth == 0:
                        mode = 'jsx_text'
            index += 1
            continue

        tag_buffer += character
        if character == '{':
            if (
                class_binding_depth is None
                and CLASS_ATTRIBUTE_PATTERN.search(tag_buffer[:-1])
            ):
                class_binding_depth = tag_expression_depth + 1
                class_expression_start = index + 1
            tag_expression_depth += 1
        elif character == '}' and tag_expression_depth > 0:
            if class_binding_depth == tag_expression_depth:
                if class_expression_start is not None:
                    class_expression_spans.append(
                        (class_expression_start, index),
                    )
                class_binding_depth = None
                class_expression_start = None
            tag_expression_depth -= 1
        elif character == '>' and tag_expression_depth == 0:
            normalized_name = tag_name.lower()
            self_closing = (
                tag_buffer.rstrip().endswith('/>')
                or normalized_name in VOID_ELEMENTS
            )
            if tag_closing:
                mode = element_parent_modes.pop() if element_parent_modes else 'code'
                if normalized_name == raw_tag:
                    raw_tag = None
            elif self_closing:
                mode = tag_parent_mode
            else:
                element_parent_modes.append(tag_parent_mode)
                if normalized_name == 'script':
                    raw_tag = 'script'
                    mode = 'code'
                elif normalized_name == 'style':
                    raw_tag = 'style'
                    mode = 'raw_text'
                else:
                    mode = 'jsx_text'
            tag_buffer = ''
        index += 1

    return LexedSource(
        ''.join(structural),
        strings,
        class_expression_spans,
    )


def token_container_names(structural: str, token_start: int) -> Iterable[str]:
    prefix = structural[:token_start]
    assignments = list(
        re.finditer(
            r'\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([\[{])',
            prefix,
        )
    )
    for match in reversed(assignments):
        opening = match.group(2)
        closing = ']' if opening == '[' else '}'
        segment = structural[match.end() - 1 : token_start]
        if segment.count(opening) > segment.count(closing):
            yield match.group(1)


def token_is_class_referenced(
    token: StringToken,
    structural: str,
    class_references: str,
) -> bool:
    prefix = structural[: token.start]
    identifier = re.search(
        r'\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*$',
        prefix[-500:],
    )
    if identifier and re.search(
        r'(?<![\w$]){}(?![\w$])'.format(re.escape(identifier.group(1))),
        class_references,
    ):
        return True

    property_name = re.search(r'([A-Za-z_$][\w$]*)\s*:\s*$', prefix[-200:])
    if property_name and re.search(
        r'\.\s*{}\b'.format(re.escape(property_name.group(1))),
        class_references,
    ):
        return True

    return any(
        re.search(
            r'(?<![\w$]){}(?![\w$])'.format(re.escape(container)),
            class_references,
        )
        for container in token_container_names(structural, token.start)
    )


def semantic_icon_classes(lexed: LexedSource) -> Iterable[str]:
    class_references = '\n'.join(
        [
            lexed.structural[start:end]
            for start, end in lexed.class_expression_spans
        ]
        + [token.value for token in lexed.strings if token.class_context]
    )
    for token in lexed.strings:
        icons = ICON_PATTERN.findall(token.value)
        if not icons:
            continue
        if token.class_context:
            yield from icons
            continue
        if '<' in token.value or re.search(r'\bimport\b', token.value):
            continue
        if token_is_class_referenced(
            token,
            lexed.structural,
            class_references,
        ):
            yield from icons


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


def audit(repo_root: Path, targets: Sequence[Path]) -> Dict[str, object]:
    library_components: Dict[str, Set[str]] = {
        library: set() for library in LIBRARIES
    }
    native_controls = {control: 0 for control in NATIVE_CONTROLS}
    image_count = 0
    icon_classes: List[str] = []
    seen_icons: Set[str] = set()

    for path in source_files(targets):
        content = path.read_text(encoding='utf-8', errors='ignore')
        lexed = lex_source(content)
        for match in IMPORT_PATTERN.finditer(content):
            if not lexed.structural.startswith('import', match.start()):
                continue
            library_components[match.group('library')].update(
                imported_components(match.group('clause')),
            )
        for control in NATIVE_CONTROLS:
            native_controls[control] += len(
                re.findall(r'<{}\b'.format(control), lexed.structural),
            )
        image_count += len(re.findall(r'<img\b', lexed.structural))
        for icon_class in semantic_icon_classes(lexed):
            if icon_class not in seen_icons:
                seen_icons.add(icon_class)
                icon_classes.append(icon_class)

    available_icons = load_available_icons(repo_root)
    return {
        'libraries': {
            library: sorted(components)
            for library, components in library_components.items()
            if components
        },
        'native_controls': native_controls,
        'images': image_count,
        'icons': [
            {
                'class': icon_class,
                'available': icon_class in available_icons,
            }
            for icon_class in icon_classes
        ],
    }


def print_plain(result: Dict[str, object]) -> None:
    libraries = result['libraries']
    print('Libraries:')
    if libraries:
        for library, components in libraries.items():
            print('  {}: {}'.format(library, ', '.join(components)))
    else:
        print('  none')

    controls = result['native_controls']
    print(
        'Native controls: '
        + ', '.join(
            '{}={}'.format(control, controls[control])
            for control in NATIVE_CONTROLS
        ),
    )
    print('Images: {}'.format(result['images']))
    print('FameEX icons:')
    icons = result['icons']
    if icons:
        for icon in icons:
            availability = 'available' if icon['available'] else 'missing'
            print('  {}: {}'.format(icon['class'], availability))
    else:
        print('  none')


def main() -> int:
    args = parse_args()
    try:
        result = audit(args.repo_root.expanduser().resolve(), args.targets)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    else:
        print_plain(result)
    return 0


if __name__ == '__main__':
    sys.exit(main())
