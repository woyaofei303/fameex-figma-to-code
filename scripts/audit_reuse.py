#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


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
    if clause.lstrip().startswith('type '):
        return

    named_match = re.search(r'\{(.*?)\}', clause, re.DOTALL)
    if named_match:
        for item in named_match.group(1).split(','):
            imported_name = item.strip()
            if imported_name.startswith('type '):
                continue
            imported_name = re.split(r'\s+as\s+', imported_name, maxsplit=1)[0]
            if re.fullmatch(r'[A-Za-z_$][\w$]*', imported_name):
                yield imported_name

    default_clause = clause.split('{', maxsplit=1)[0].rstrip(' ,\n\t')
    if default_clause and not default_clause.startswith(('*', 'type ')):
        default_name = default_clause.split(',', maxsplit=1)[0].strip()
        if re.fullmatch(r'[A-Za-z_$][\w$]*', default_name):
            yield default_name


def sanitized_views(content: str) -> Tuple[str, str]:
    structural: List[str] = []
    icon_source: List[str] = []
    state = 'code'
    quote = ''
    preserve_string_for_icons = False
    in_tag = False
    tag_expression_depth = 0
    class_binding_depth: Optional[int] = None
    tag_buffer = ''
    index = 0

    def append_hidden(character: str) -> None:
        hidden = '\n' if character == '\n' else ' '
        structural.append(hidden)
        icon_source.append(hidden)

    while index < len(content):
        character = content[index]
        following = content[index + 1] if index + 1 < len(content) else ''

        if state == 'line_comment':
            if character == '\n':
                structural.append(character)
                icon_source.append(character)
                if in_tag:
                    tag_buffer += character
                state = 'code'
            else:
                append_hidden(character)
                if in_tag:
                    tag_buffer += ' '
            index += 1
            continue

        if state in ('block_comment', 'html_comment'):
            terminator = '*/' if state == 'block_comment' else '-->'
            if content.startswith(terminator, index):
                for terminator_character in terminator:
                    append_hidden(terminator_character)
                    if in_tag:
                        tag_buffer += ' '
                index += len(terminator)
                state = 'code'
                continue
            append_hidden(character)
            if in_tag:
                tag_buffer += '\n' if character == '\n' else ' '
            index += 1
            continue

        if state == 'string':
            structural.append('\n' if character == '\n' else ' ')
            if preserve_string_for_icons:
                icon_source.append(character)
            else:
                icon_source.append('\n' if character == '\n' else ' ')
            if in_tag:
                tag_buffer += '\n' if character == '\n' else ' '

            if character == '\\' and following:
                structural.append('\n' if following == '\n' else ' ')
                if preserve_string_for_icons:
                    icon_source.append(following)
                else:
                    icon_source.append('\n' if following == '\n' else ' ')
                if in_tag:
                    tag_buffer += '\n' if following == '\n' else ' '
                index += 2
                continue
            if character == quote:
                state = 'code'
                preserve_string_for_icons = False
            index += 1
            continue

        if content.startswith('<!--', index):
            state = 'html_comment'
            continue
        if character == '/' and following == '/':
            state = 'line_comment'
            continue
        if character == '/' and following == '*':
            state = 'block_comment'
            continue
        if character in ("'", '"', '`'):
            quote = character
            preserve_string_for_icons = bool(
                in_tag
                and (
                    class_binding_depth is not None
                    or CLASS_ATTRIBUTE_PATTERN.search(tag_buffer)
                )
            )
            structural.append(' ')
            icon_source.append(character if preserve_string_for_icons else ' ')
            if in_tag:
                tag_buffer += ' '
            state = 'string'
            index += 1
            continue

        structural.append(character)
        icon_source.append(character)

        if not in_tag and character == '<':
            remainder = content[index + 1 :]
            if re.match(r'/?[A-Za-z][\w:.-]*', remainder):
                in_tag = True
                tag_expression_depth = 0
                class_binding_depth = None
                tag_buffer = '<'
        elif in_tag:
            tag_buffer += character
            if character == '{':
                tag_expression_depth += 1
                if (
                    class_binding_depth is None
                    and CLASS_ATTRIBUTE_PATTERN.search(tag_buffer[:-1])
                ):
                    class_binding_depth = tag_expression_depth
            elif character == '}' and tag_expression_depth > 0:
                if class_binding_depth == tag_expression_depth:
                    class_binding_depth = None
                tag_expression_depth -= 1
            elif character == '>' and tag_expression_depth == 0:
                in_tag = False
                tag_buffer = ''

        index += 1

    return ''.join(structural), ''.join(icon_source)


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
        structural, icon_source = sanitized_views(content)
        for match in IMPORT_PATTERN.finditer(content):
            if not structural.startswith('import', match.start()):
                continue
            library_components[match.group('library')].update(
                imported_components(match.group('clause')),
            )
        for control in NATIVE_CONTROLS:
            native_controls[control] += len(
                re.findall(r'<{}\b'.format(control), structural),
            )
        image_count += len(re.findall(r'<img\b', structural))
        for icon_class in ICON_PATTERN.findall(icon_source):
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
