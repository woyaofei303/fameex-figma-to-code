#!/usr/bin/env python3
"""Build and validate reproducible visual-evidence receipts."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


RECEIPT_SCHEMA_VERSION = '1.0'
VALIDATOR_VERSION = '2.0'
TOOLCHAIN_FILES = (
    'audit_assets.py',
    'compare_assets_rgba.py',
    'validate_visual_evidence.py',
    'visual_evidence_provenance.py',
)


class SnapshotError(ValueError):
    """Raised when a repository or evidence snapshot cannot be built."""


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def relative_file_record(repo_root, path):
    root = repo_root.resolve()
    candidate = path.resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise SnapshotError(
            f'File is outside the repository: {path}'
        ) from exc
    if not candidate.is_file():
        raise SnapshotError(f'File does not exist: {path}')
    return {
        'path': relative.as_posix(),
        'bytes': candidate.stat().st_size,
        'sha256': sha256_file(candidate),
    }


def snapshot_files(repo_root, paths):
    records = {}
    for path in paths:
        record = relative_file_record(repo_root, Path(path))
        records[record['path']] = record
    return [records[path] for path in sorted(records)]


def snapshot_toolchain():
    scripts_dir = Path(__file__).resolve().parent
    return [
        {
            'path': f'scripts/{name}',
            'sha256': sha256_file(scripts_dir / name),
        }
        for name in TOOLCHAIN_FILES
    ]


def resolve_target_paths(repo_root, target_paths):
    root = repo_root.resolve()
    resolved = []
    for supplied in target_paths:
        path = Path(supplied)
        if path.is_absolute() or '..' in path.parts:
            raise SnapshotError(
                f'Target path must be repository-relative: {supplied}'
            )
        candidate = (root / path).resolve()
        if not candidate.is_file():
            raise SnapshotError(f'Target file does not exist: {supplied}')
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise SnapshotError(
                f'Target file is outside the repository: {supplied}'
            ) from exc
        resolved.append(candidate)
    return resolved


def run_git(repo_root, *args):
    result = subprocess.run(
        ['git', '-C', str(repo_root), *args],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        message = result.stderr.decode(errors='replace').strip()
        raise SnapshotError(message or 'Git command failed.')
    return result.stdout


def snapshot_git(repo_root):
    head = run_git(repo_root, 'rev-parse', 'HEAD').decode().strip()
    tree = run_git(
        repo_root,
        'rev-parse',
        'HEAD^{tree}',
    ).decode().strip()
    status = run_git(
        repo_root,
        'status',
        '--porcelain=v1',
        '-z',
        '--untracked-files=all',
    )
    tracked_diff = run_git(
        repo_root,
        'diff',
        '--binary',
        '--full-index',
        'HEAD',
        '--',
    )
    untracked_output = run_git(
        repo_root,
        'ls-files',
        '--others',
        '--exclude-standard',
        '-z',
    )
    untracked_paths = [
        repo_root / path.decode(errors='surrogateescape')
        for path in untracked_output.split(b'\0')
        if path
    ]
    return {
        'head': head,
        'tree': tree,
        'dirty': bool(status),
        'status_sha256': sha256_bytes(status),
        'tracked_diff_sha256': sha256_bytes(tracked_diff),
        'untracked': snapshot_files(repo_root, untracked_paths),
    }


def ensure_audit_ignored(repo_root, manifest_path):
    for path in (
        manifest_path,
        manifest_path.parent / 'validation-receipt.json',
    ):
        result = subprocess.run(
            [
                'git',
                '-C',
                str(repo_root),
                'check-ignore',
                '--quiet',
                '--no-index',
                str(path),
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode:
            raise SnapshotError(
                'The visual audit directory must be ignored by Git.'
            )


def build_receipt(
    manifest_path,
    repo_root,
    target_paths,
    artifacts,
    claim,
    require_clean=False,
):
    ensure_audit_ignored(repo_root, manifest_path)
    resolved_targets = resolve_target_paths(repo_root, target_paths)
    git = snapshot_git(repo_root)
    if require_clean and git['dirty']:
        raise SnapshotError(
            'The repository must be clean before writing a claim receipt.'
        )
    return {
        'schema_version': RECEIPT_SCHEMA_VERSION,
        'validator_version': VALIDATOR_VERSION,
        'validator_build': snapshot_toolchain(),
        'validated_at': datetime.now(timezone.utc).isoformat(),
        'manifest_sha256': sha256_file(manifest_path),
        'git': git,
        'targets': snapshot_files(repo_root, resolved_targets),
        'artifacts': snapshot_files(repo_root, artifacts),
        'claim': {
            'status': claim.get('status'),
            'level': claim.get('level'),
        },
    }


def stale_error(code, path, message):
    return {'code': code, 'path': path, 'message': message}


def validate_receipt(
    receipt,
    manifest_path,
    repo_root,
    target_paths,
    artifacts,
    claim,
):
    try:
        current = build_receipt(
            manifest_path=manifest_path,
            repo_root=repo_root,
            target_paths=target_paths,
            artifacts=artifacts,
            claim=claim,
            require_clean=False,
        )
    except (OSError, SnapshotError) as exc:
        return [
            stale_error(
                'receipt.snapshot_failed',
                'validation-receipt.json',
                str(exc),
            )
        ]

    errors = []
    if not isinstance(receipt, dict):
        return [
            stale_error(
                'receipt.invalid',
                'validation-receipt.json',
                'Receipt root must be an object.',
            )
        ]
    if (
        receipt.get('schema_version') != RECEIPT_SCHEMA_VERSION
        or receipt.get('validator_version') != VALIDATOR_VERSION
    ):
        errors.append(
            stale_error(
                'receipt.version',
                'validation-receipt.json',
                'Receipt or validator version is unsupported.',
            )
        )
    if receipt.get('validator_build') != current['validator_build']:
        errors.append(
            stale_error(
                'receipt.validator_build_stale',
                'validation-receipt.json',
                'Validator or evidence tool code changed after validation.',
            )
        )
    if receipt.get('manifest_sha256') != current['manifest_sha256']:
        errors.append(
            stale_error(
                'receipt.manifest_stale',
                'validation-receipt.json',
                'Manifest content changed after validation.',
            )
        )
    if receipt.get('git') != current['git']:
        errors.append(
            stale_error(
                'receipt.git_stale',
                'validation-receipt.json',
                'Git HEAD, tree, tracked diff, or untracked files changed '
                'after validation.',
            )
        )
    if receipt.get('targets') != current['targets']:
        errors.append(
            stale_error(
                'receipt.target_stale',
                'validation-receipt.json',
                'A target file changed after validation.',
            )
        )
    if receipt.get('artifacts') != current['artifacts']:
        errors.append(
            stale_error(
                'receipt.artifact_stale',
                'validation-receipt.json',
                'An evidence artifact changed after validation.',
            )
        )
    if receipt.get('claim') != current['claim']:
        errors.append(
            stale_error(
                'receipt.claim_stale',
                'validation-receipt.json',
                'Claim status or level changed after validation.',
            )
        )
    return errors


def read_receipt(path):
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise SnapshotError('Receipt root must be an object.')
    return payload


def write_receipt(path, payload):
    temporary = path.with_name(f'.{path.name}.tmp')
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    )
    temporary.replace(path)
