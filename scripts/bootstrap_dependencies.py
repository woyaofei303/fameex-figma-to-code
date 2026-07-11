#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Dict, List, Sequence, Tuple


DEPENDENCIES = (
    'figma',
    'figma-implement-design',
    'playwright',
    'verification-before-completion',
)


def parse_args() -> argparse.Namespace:
    default_home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    parser = argparse.ArgumentParser(
        description='Create missing fallback skills without overwriting existing skills.',
    )
    parser.add_argument('--codex-home', type=Path, default=default_home)
    parser.add_argument(
        '--dependency',
        action='append',
        choices=DEPENDENCIES,
        help='Bootstrap only this dependency. Repeat for multiple dependencies.',
    )
    parser.add_argument('--json', action='store_true', dest='as_json')
    return parser.parse_args()


def validate_skill(skill_dir: Path, expected_name: str) -> Tuple[bool, str]:
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.is_file():
        return False, 'SKILL.md not found'

    content = skill_md.read_text()
    frontmatter = re.match(r'^---\n(.*?)\n---(?:\n|$)', content, re.DOTALL)
    if not frontmatter:
        return False, 'invalid YAML frontmatter delimiters'

    block = frontmatter.group(1)
    name_match = re.search(
        r'^name:\s*["\']?([a-z0-9-]+)["\']?\s*$',
        block,
        re.MULTILINE,
    )
    description_match = re.search(
        r'^description:\s*["\']?(.+?)["\']?\s*$',
        block,
        re.MULTILINE,
    )
    if not name_match:
        return False, 'frontmatter name missing or invalid'
    if name_match.group(1) != expected_name:
        return False, 'frontmatter name does not match directory'
    if not description_match or not description_match.group(1).strip():
        return False, 'frontmatter description missing'
    return True, 'valid'


def prerequisite_for(name: str) -> str:
    if name == 'playwright':
        return 'ok:npx' if shutil.which('npx') else 'missing:npx'
    return 'not-applicable'


def bootstrap_dependency(
    name: str,
    codex_home: Path,
    template_root: Path,
) -> Dict[str, str]:
    skills_dir = codex_home / 'skills'
    skills_dir.mkdir(parents=True, exist_ok=True)
    target = skills_dir / name
    source = template_root / name

    if target.exists():
        valid, reason = validate_skill(target, name)
        status = 'present' if valid else 'invalid'
        prerequisite = prerequisite_for(name) if valid else 'not-checked'
        return {
            'name': name,
            'status': status,
            'path': str(target),
            'prerequisite': prerequisite,
            'message': reason,
        }

    if not source.is_dir():
        return {
            'name': name,
            'status': 'invalid',
            'path': str(target),
            'prerequisite': 'not-checked',
            'message': 'fallback template not found',
        }

    try:
        shutil.copytree(source, target)
    except OSError as error:
        return {
            'name': name,
            'status': 'invalid',
            'path': str(target),
            'prerequisite': 'not-checked',
            'message': 'copy failed: {}'.format(error),
        }

    valid, reason = validate_skill(target, name)
    if not valid:
        shutil.rmtree(target)
        return {
            'name': name,
            'status': 'invalid',
            'path': str(target),
            'prerequisite': 'not-checked',
            'message': 'created fallback failed validation: {}'.format(reason),
        }

    return {
        'name': name,
        'status': 'created',
        'path': str(target),
        'prerequisite': prerequisite_for(name),
        'message': 'fallback skill created',
    }


def has_failure(results: Sequence[Dict[str, str]]) -> bool:
    return any(
        item['status'] == 'invalid'
        or item['prerequisite'].startswith('missing:')
        for item in results
    )


def print_plain(results: Sequence[Dict[str, str]]) -> None:
    for item in results:
        print(
            '{name}: {status} ({prerequisite}) {path}'.format(**item),
        )


def main() -> int:
    args = parse_args()
    requested: List[str] = list(dict.fromkeys(args.dependency or DEPENDENCIES))
    skill_root = Path(__file__).resolve().parent.parent
    template_root = skill_root / 'assets' / 'fallback-skills'
    codex_home = args.codex_home.expanduser().resolve()
    results = [
        bootstrap_dependency(name, codex_home, template_root)
        for name in requested
    ]

    payload = {'codex_home': str(codex_home), 'results': results}
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_plain(results)
    return 1 if has_failure(results) else 0


if __name__ == '__main__':
    sys.exit(main())
