#!/usr/bin/env python3
"""Validate canonical FameEX visual evidence without third-party packages."""

import argparse
import json
from pathlib import Path
import sys

from audit_assets import inspect_asset


VERIFIED_STATUS = 'verified'
FULL_CLAIMS = {'feature-complete', 'release-ready', 'released'}
UNRESOLVED_API = {'missing', 'unresolved', 'waiting'}
MEASUREMENT_FIELDS = ('start', 'width', 'center')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Validate a FameEX visual-evidence.json manifest.',
    )
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--repo-root', required=True, type=Path)
    parser.add_argument(
        '--json',
        action='store_true',
        help='Write a machine-readable result to stdout.',
    )
    return parser.parse_args()


def add_error(errors, code, path, message):
    errors.append({'code': code, 'path': path, 'message': message})


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def resolve_artifact(value, manifest_dir, repo_root):
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    candidates = [path] if path.is_absolute() else [
        repo_root / path,
        manifest_dir / path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def artifact_exists(value, manifest_dir, repo_root):
    return resolve_artifact(value, manifest_dir, repo_root) is not None


def require_artifact(
    errors,
    evidence,
    path,
    code,
    manifest_dir,
    repo_root,
):
    artifact = evidence.get('artifact') if isinstance(evidence, dict) else None
    resolved = resolve_artifact(artifact, manifest_dir, repo_root)
    if resolved is None:
        add_error(
            errors,
            code,
            f'{path}.artifact',
            'Evidence artifact is missing or cannot be resolved.',
        )
    elif not is_within(resolved, manifest_dir.resolve()):
        add_error(
            errors,
            'artifact.scope',
            f'{path}.artifact',
            'Evidence must stay inside the task visual-audit directory.',
        )
    return resolved


def read_json_artifact(path):
    if path is None or path.suffix.lower() != '.json':
        return None
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def resolve_repository_file(value, repo_root):
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    candidate = path if path.is_absolute() else repo_root / path
    if not candidate.is_file():
        return None
    resolved = candidate.resolve()
    return resolved if is_within(resolved, repo_root.resolve()) else None


def check_unique_ids(errors, entries, collection):
    seen = set()
    for index, entry in enumerate(entries):
        entry_id = entry.get('id') if isinstance(entry, dict) else None
        if not entry_id:
            add_error(
                errors,
                'manifest.id',
                f'{collection}[{index}].id',
                'A stable id is required.',
            )
        elif entry_id in seen:
            add_error(
                errors,
                'manifest.duplicate_id',
                f'{collection}[{index}].id',
                f'Duplicate id: {entry_id}',
            )
        else:
            seen.add(entry_id)
    return seen


def validate_frames(
    errors,
    frames,
    claim_verified,
    manifest_dir,
    repo_root,
):
    frame_ids = check_unique_ids(errors, frames, 'frames')
    if claim_verified and not frames:
        add_error(
            errors,
            'frame.missing',
            'frames',
            'At least one exact Figma frame is required.',
        )
    for index, frame in enumerate(frames):
        path = f'frames[{index}]'
        if not isinstance(frame, dict):
            add_error(
                errors,
                'frame.invalid',
                path,
                'Frame must be an object.',
            )
            continue
        for field in ('file_key', 'node_id', 'state'):
            if not frame.get(field):
                add_error(
                    errors,
                    'frame.exact_node',
                    f'{path}.{field}',
                    f'Exact frame {field} is required.',
                )
        if not claim_verified:
            continue
        context = frame.get('structured_context', {})
        if context.get('status') != 'passed':
            add_error(
                errors,
                'frame.context',
                f'{path}.structured_context.status',
                'Structured context from the exact node must pass.',
            )
        else:
            require_artifact(
                errors,
                context,
                f'{path}.structured_context',
                'frame.context',
                manifest_dir,
                repo_root,
            )
        screenshot = frame.get('same_node_screenshot', {})
        if screenshot.get('status') != 'passed':
            add_error(
                errors,
                'frame.screenshot',
                f'{path}.same_node_screenshot.status',
                'A same-node screenshot must pass.',
            )
        else:
            require_artifact(
                errors,
                screenshot,
                f'{path}.same_node_screenshot',
                'frame.screenshot',
                manifest_dir,
                repo_root,
            )
    return frame_ids


def validate_sections(
    errors,
    sections,
    frame_ids,
    claim_verified,
    manifest_dir,
    repo_root,
):
    section_ids = check_unique_ids(errors, sections, 'sections')
    ranking_ids = set()
    motion_ids = set()
    correction_refs = set()
    for index, section in enumerate(sections):
        path = f'sections[{index}]'
        if not isinstance(section, dict):
            add_error(
                errors,
                'section.invalid',
                path,
                'Section must be an object.',
            )
            continue
        section_id = section.get('id')
        if section.get('frame_id') not in frame_ids:
            add_error(
                errors,
                'section.frame_reference',
                f'{path}.frame_id',
                'Section must reference an existing exact frame.',
            )
        if section.get('kind') in {'ranking', 'table'}:
            ranking_ids.add(section_id)
        if section.get('motion_required') is True:
            motion_ids.add(section_id)
        correction_refs.update(section.get('correction_ids', []))
        if not claim_verified:
            continue

        geometry = section.get('geometry', {})
        if geometry.get('status') != 'passed':
            add_error(
                errors,
                'section.geometry',
                f'{path}.geometry.status',
                'Section geometry measurements must pass.',
            )
        else:
            require_artifact(
                errors,
                geometry,
                f'{path}.geometry',
                'section.geometry',
                manifest_dir,
                repo_root,
            )

        style = section.get('style', {})
        if (
            style.get('tailwind_status') != 'passed'
            or style.get('computed_style_status') != 'passed'
        ):
            add_error(
                errors,
                'section.style',
                f'{path}.style',
                'Tailwind tokens and computed styles must both pass.',
            )
        else:
            require_artifact(
                errors,
                style,
                f'{path}.style',
                'section.style',
                manifest_dir,
                repo_root,
            )

        implementation = section.get('implementation', {})
        for field in ('crop', 'comparison'):
            require_artifact(
                errors,
                {'artifact': implementation.get(field)},
                f'{path}.implementation.{field}',
                'section.comparison',
                manifest_dir,
                repo_root,
            )

        mismatch = section.get('mismatch', {})
        if (
            mismatch.get('salience') == 'high'
            and mismatch.get('status') != 'closed'
        ):
            add_error(
                errors,
                'section.high_mismatch',
                f'{path}.mismatch',
                'A high-salience mismatch remains open.',
            )

        for layer_index, layer in enumerate(
            section.get('visual_layers', []),
        ):
            if not isinstance(layer, dict) or not layer.get('visible', True):
                continue
            layer_path = f'{path}.visual_layers[{layer_index}]'
            source = layer.get('source', {})
            if (
                source.get('status') != 'resolved'
                or not source.get('locator')
            ):
                add_error(
                    errors,
                    'layer.source',
                    f'{layer_path}.source',
                    'Every visible asset/effect layer needs a source.',
                )
            composition = layer.get('composition', {})
            if composition.get('status') != 'passed':
                add_error(
                    errors,
                    'layer.composition',
                    f'{layer_path}.composition.status',
                    'Visible layer composition must pass.',
                )
            else:
                require_artifact(
                    errors,
                    composition,
                    f'{layer_path}.composition',
                    'layer.composition',
                    manifest_dir,
                    repo_root,
                )
        sizing_rows = section.get('sizing', [])
        if not sizing_rows:
            add_error(
                errors,
                'layout.missing',
                f'{path}.sizing',
                'Verified sections require sizing evidence.',
            )
        for sizing_index, sizing in enumerate(sizing_rows):
            sizing_path = f'{path}.sizing[{sizing_index}]'
            expected = (
                sizing.get('expected', {})
                if isinstance(sizing, dict)
                else {}
            )
            actual = (
                sizing.get('actual', {})
                if isinstance(sizing, dict)
                else {}
            )
            if (
                not sizing.get('target')
                or not sizing.get('source')
                or not sizing.get('tailwind')
                or not isinstance(sizing.get('computed'), dict)
                or not sizing.get('computed')
                or sizing.get('status') != 'passed'
            ):
                add_error(
                    errors,
                    'layout.evidence',
                    sizing_path,
                    'Sizing target, source, Tailwind, computed values, and passed status are required.',
                )
            if not expected or not actual:
                add_error(
                    errors,
                    'layout.constraint',
                    sizing_path,
                    'Expected and actual sizing constraints are required.',
                )
                continue
            mismatch = False
            for field, expected_value in expected.items():
                actual_value = actual.get(field)
                if is_number(expected_value) and is_number(actual_value):
                    if abs(expected_value - actual_value) > 0.5:
                        mismatch = True
                elif actual_value != expected_value:
                    mismatch = True
            if mismatch:
                add_error(
                    errors,
                    'layout.constraint',
                    sizing_path,
                    'Actual sizing/distribution does not match sourced expectations.',
                )
    return section_ids, ranking_ids, motion_ids, correction_refs


def validate_responsive(
    errors,
    responsive_rows,
    required_viewports,
    claim_verified,
    manifest_dir,
    repo_root,
):
    check_unique_ids(errors, responsive_rows, 'responsive_matrix')
    check_unique_ids(errors, required_viewports, 'required_viewports')
    if not claim_verified:
        return
    if not required_viewports:
        add_error(
            errors,
            'responsive.requirements_missing',
            'required_viewports',
            'Verified visual work requires sourced viewport requirements.',
        )
    for index, requirement in enumerate(required_viewports):
        path = f'required_viewports[{index}]'
        if (
            not isinstance(requirement, dict)
            or not requirement.get('source')
            or not is_number(requirement.get('width'))
            or not is_number(requirement.get('height'))
            or requirement.get('kind') not in {'desktop', 'h5'}
        ):
            add_error(
                errors,
                'responsive.requirement',
                path,
                'Required viewport needs a source, kind, width, and height.',
            )
            continue
        matching = [
            row
            for row in responsive_rows
            if isinstance(row, dict)
            and row.get('viewport', {}).get('kind')
            == requirement.get('kind')
            and row.get('viewport', {}).get('width')
            == requirement.get('width')
            and row.get('viewport', {}).get('height')
            == requirement.get('height')
        ]
        if not matching:
            add_error(
                errors,
                'responsive.required_viewport',
                path,
                'No responsive row matches this sourced viewport.',
            )
        elif requirement.get('full_interaction') is True:
            validate_full_interaction(
                errors,
                matching[0],
                f'{path}.full_interaction',
                manifest_dir,
                repo_root,
            )
    for index, row in enumerate(responsive_rows):
        viewport = row.get('viewport', {}) if isinstance(row, dict) else {}
        if (
            viewport.get('kind') != 'h5'
            or viewport.get('short_height') is not True
        ):
            continue
        validate_full_interaction(
            errors,
            row,
            f'responsive_matrix[{index}].full_interaction',
            manifest_dir,
            repo_root,
        )


def validate_full_interaction(
    errors,
    row,
    path,
    manifest_dir,
    repo_root,
):
    viewport = row.get('viewport', {})
    interaction = row.get('full_interaction', {})
    required = (
        'trigger',
        'scroll_owner',
        'close_control',
        'final_action',
        'safe_area',
    )
    complete = (
        interaction.get('status') == 'passed'
        and all(interaction.get(field) is True for field in required)
        and interaction.get('horizontal_scroll')
        in (True, 'not-applicable')
    )
    if not complete:
        add_error(
            errors,
            'responsive.short_height',
            path,
            'Short-height H5 requires the complete reachable interaction.',
        )
        return
    artifact = require_artifact(
        errors,
        interaction,
        path,
        'responsive.short_height',
        manifest_dir,
        repo_root,
    )
    payload = read_json_artifact(artifact)
    steps = payload.get('steps', {}) if payload else {}
    artifact_matches = (
        payload is not None
        and payload.get('source') == 'playwright'
        and payload.get('status') == 'passed'
        and payload.get('viewport') == {
            'width': viewport.get('width'),
            'height': viewport.get('height'),
        }
        and all(steps.get(field) is True for field in required)
        and steps.get('horizontal_scroll')
        == interaction.get('horizontal_scroll')
    )
    if not artifact_matches:
        add_error(
            errors,
            'responsive.interaction_artifact',
            f'{path}.artifact',
            'Interaction artifact must be machine-readable Playwright evidence for the same viewport and steps.',
        )


def validate_tables(
    errors,
    table_checks,
    ranking_ids,
    claim_verified,
    manifest_dir,
    repo_root,
):
    check_unique_ids(errors, table_checks, 'table_checks')
    checks_by_section = {
        check.get('section_id'): check
        for check in table_checks
        if isinstance(check, dict)
    }
    if claim_verified:
        for section_id in ranking_ids:
            if section_id not in checks_by_section:
                add_error(
                    errors,
                    'table.missing',
                    'table_checks',
                    f'Ranking/table section {section_id} has no check.',
                )
    for index, check in enumerate(table_checks):
        if not isinstance(check, dict) or not claim_verified:
            continue
        path = f'table_checks[{index}]'
        if check.get('status') != 'passed':
            add_error(
                errors,
                'table.status',
                f'{path}.status',
                'Table alignment check must pass.',
            )
        require_artifact(
            errors,
            check,
            path,
            'table.artifact',
            manifest_dir,
            repo_root,
        )
        columns = check.get('columns', [])
        if not columns:
            add_error(
                errors,
                'table.columns',
                f'{path}.columns',
                'Measured columns are required.',
            )
        for column_index, column in enumerate(columns):
            column_path = f'{path}.columns[{column_index}]'
            header = column.get('th', {})
            cells = column.get('td', [])
            if not cells:
                add_error(
                    errors,
                    'table.cells',
                    f'{column_path}.td',
                    'Representative body cell measurements are required.',
                )
                continue
            if not all(
                is_number(header.get(field))
                for field in MEASUREMENT_FIELDS
            ):
                add_error(
                    errors,
                    'table.header_measurement',
                    f'{column_path}.th',
                    'Header start, width, and center must be numeric.',
                )
                continue
            for cell_index, cell in enumerate(cells):
                if not all(
                    is_number(cell.get(field))
                    for field in MEASUREMENT_FIELDS
                ):
                    add_error(
                        errors,
                        'table.cell_measurement',
                        f'{column_path}.td[{cell_index}]',
                        'Cell start, width, and center must be numeric.',
                    )
                    continue
                if any(
                    abs(header[field] - cell[field]) > 0.5
                    for field in MEASUREMENT_FIELDS
                ):
                    add_error(
                        errors,
                        'table.column_alignment',
                        f'{column_path}.td[{cell_index}]',
                        'Header and body must share column measurements.',
                    )


def validate_motion(
    errors,
    motion_checks,
    required_sections,
    claim_verified,
    manifest_dir,
    repo_root,
):
    check_unique_ids(errors, motion_checks, 'motion_checks')
    checks_by_section = {
        check.get('section_id'): check
        for check in motion_checks
        if isinstance(check, dict)
    }
    if claim_verified:
        for section_id in required_sections:
            if section_id not in checks_by_section:
                add_error(
                    errors,
                    'motion.missing',
                    'motion_checks',
                    f'Motion section {section_id} has no lifecycle check.',
                )
    fields = ('trigger', 'order', 'input_lock', 'completion', 'unmount')
    for index, check in enumerate(motion_checks):
        if not isinstance(check, dict) or not claim_verified:
            continue
        path = f'motion_checks[{index}]'
        if check.get('status') != 'passed':
            add_error(
                errors,
                'motion.status',
                f'{path}.status',
                'Motion verification must pass.',
            )
        for field in fields:
            if check.get(field) is not True:
                add_error(
                    errors,
                    f'motion.{field}',
                    f'{path}.{field}',
                    f'Motion {field} verification is required.',
                )
        require_artifact(
            errors,
            check,
            path,
            'motion.artifact',
            manifest_dir,
            repo_root,
        )


def validate_corrections(
    errors,
    corrections,
    correction_refs,
    claim_verified,
    manifest_dir,
    repo_root,
):
    correction_ids = check_unique_ids(errors, corrections, 'corrections')
    for correction_id in correction_refs - correction_ids:
        add_error(
            errors,
            'correction.reference',
            'sections[].correction_ids',
            f'Unknown correction id: {correction_id}',
        )
    for index, correction in enumerate(corrections):
        if not isinstance(correction, dict) or not claim_verified:
            continue
        path = f'corrections[{index}]'
        reverify = correction.get('reverification', {})
        if (
            correction.get('status') != 'closed'
            or reverify.get('status') != 'passed'
            or not correction.get('affected_rows')
        ):
            add_error(
                errors,
                'correction.reverification',
                path,
                'Closed user feedback must re-verify all affected rows.',
            )
        else:
            require_artifact(
                errors,
                reverify,
                f'{path}.reverification',
                'correction.reverification',
                manifest_dir,
                repo_root,
            )


def validate_asset_conversions(
    errors,
    conversions,
    manifest_dir,
    repo_root,
):
    for index, conversion in enumerate(conversions):
        if not isinstance(conversion, dict):
            continue
        if (
            str(conversion.get('target_format', '')).lower() != 'webp'
            or conversion.get('decision') != 'accepted'
        ):
            continue
        path = f'asset_conversions[{index}]'
        source_path = resolve_repository_file(
            conversion.get('source'),
            repo_root,
        )
        candidate_path = resolve_repository_file(
            conversion.get('candidate'),
            repo_root,
        )
        if source_path is None:
            add_error(
                errors,
                'asset.source',
                f'{path}.source',
                'Accepted conversion source must exist inside the repository.',
            )
        if candidate_path is None:
            add_error(
                errors,
                'asset.candidate',
                f'{path}.candidate',
                'Accepted WebP candidate must exist inside the repository.',
            )
        if source_path is None or candidate_path is None:
            continue
        try:
            source_audit = inspect_asset(source_path)
            candidate_audit = inspect_asset(candidate_path)
        except (OSError, ValueError) as exc:
            add_error(
                errors,
                'asset.audit',
                path,
                f'Unable to audit accepted conversion files: {exc}',
            )
            continue
        comparison = conversion.get('visual_comparison', {})
        recorded_dimensions_match = (
            conversion.get('source_dimensions')
            == conversion.get('candidate_dimensions')
        )
        audited_dimensions_match = (
            source_audit['intrinsic_dimensions']
            == candidate_audit['intrinsic_dimensions']
            == conversion.get('source_dimensions')
            == conversion.get('candidate_dimensions')
        )
        bytes_valid = (
            conversion.get('before_bytes') == source_audit['bytes']
            and conversion.get('after_bytes') == candidate_audit['bytes']
            and candidate_audit['bytes'] < source_audit['bytes']
        )
        audited_alpha = {
            'source': (
                'present' if source_audit['alpha_capable'] else 'absent'
            ),
            'candidate': (
                'present'
                if candidate_audit['alpha_capable']
                else 'absent'
            ),
        }
        alpha = conversion.get('alpha', {})
        alpha_match = (
            alpha == audited_alpha
            and alpha.get('source') == alpha.get('candidate')
            and candidate_audit['format'] == 'webp'
        )
        comparison_artifact = resolve_artifact(
            comparison.get('artifact'),
            manifest_dir,
            repo_root,
        )
        comparison_payload = read_json_artifact(comparison_artifact)
        pixels_expected = (
            source_audit['intrinsic_dimensions']['width']
            * source_audit['intrinsic_dimensions']['height']
        )
        comparison_valid = (
            comparison.get('status') == 'passed'
            and bool(comparison.get('tool'))
            and comparison_artifact is not None
            and is_within(
                comparison_artifact,
                manifest_dir.resolve(),
            )
            and comparison_payload is not None
            and comparison_payload.get('source_sha256')
            == source_audit['sha256']
            and comparison_payload.get('candidate_sha256')
            == candidate_audit['sha256']
            and comparison_payload.get('tool') == comparison.get('tool')
            and comparison_payload.get('status') == 'passed'
            and comparison_payload.get('metric') == 'rgba'
            and comparison_payload.get('pixels_compared')
            == pixels_expected
            and is_number(comparison_payload.get('different_pixels'))
            and is_number(comparison_payload.get('max_channel_delta'))
            and comparison_payload.get('alpha_different_pixels') == 0
        )
        if not (
            recorded_dimensions_match
            and audited_dimensions_match
            and bytes_valid
            and alpha_match
            and comparison_valid
        ):
            add_error(
                errors,
                'asset.webp_comparison',
                path,
                'Accepted WebP requires size, dimension, alpha, and visual comparison evidence.',
            )


def validate_manifest(manifest, manifest_path, repo_root):
    errors = []
    required_collections = (
        'required_viewports',
        'frames',
        'sections',
        'responsive_matrix',
        'table_checks',
        'motion_checks',
        'historical_reuse',
        'entry_surfaces',
        'asset_conversions',
        'corrections',
        'api_contracts',
    )
    for key in ('schema_version', 'task', 'claim', *required_collections):
        if key not in manifest:
            add_error(
                errors,
                'manifest.required',
                key,
                f'Missing required top-level key: {key}',
            )
    if errors:
        return errors

    task = manifest.get('task', {})
    declared_repo = task.get('repository')
    if not declared_repo:
        add_error(
            errors,
            'task.repository',
            'task.repository',
            'Repository is required.',
        )
    else:
        declared_path = Path(declared_repo).expanduser()
        if declared_path.is_absolute() and (
            declared_path.resolve() != repo_root.resolve()
        ):
            add_error(
                errors,
                'task.repository_mismatch',
                'task.repository',
                'Manifest repository does not match --repo-root.',
            )

    claim = manifest.get('claim', {})
    claim_verified = claim.get('status') == VERIFIED_STATUS
    manifest_dir = manifest_path.parent
    task_id = task.get('id')
    if task_id:
        expected_manifest = (
            repo_root
            / 'output-tdd'
            / 'figma-audits'
            / str(task_id)
            / 'visual-evidence.json'
        ).resolve()
        if manifest_path.resolve() != expected_manifest:
            add_error(
                errors,
                'manifest.location',
                str(manifest_path),
                f'Manifest must be stored at {expected_manifest}.',
            )
    frames = manifest.get('frames', [])
    sections = manifest.get('sections', [])
    frame_ids = validate_frames(
        errors,
        frames,
        claim_verified,
        manifest_dir,
        repo_root,
    )
    (
        _section_ids,
        ranking_ids,
        motion_ids,
        correction_refs,
    ) = validate_sections(
        errors,
        sections,
        frame_ids,
        claim_verified,
        manifest_dir,
        repo_root,
    )
    validate_responsive(
        errors,
        manifest.get('responsive_matrix', []),
        manifest.get('required_viewports', []),
        claim_verified,
        manifest_dir,
        repo_root,
    )
    validate_tables(
        errors,
        manifest.get('table_checks', []),
        ranking_ids,
        claim_verified,
        manifest_dir,
        repo_root,
    )
    validate_motion(
        errors,
        manifest.get('motion_checks', []),
        motion_ids,
        claim_verified,
        manifest_dir,
        repo_root,
    )
    validate_corrections(
        errors,
        manifest.get('corrections', []),
        correction_refs,
        claim_verified,
        manifest_dir,
        repo_root,
    )
    validate_asset_conversions(
        errors,
        manifest.get('asset_conversions', []),
        manifest_dir,
        repo_root,
    )

    api_statuses = {
        contract.get('status')
        for contract in manifest.get('api_contracts', [])
        if isinstance(contract, dict)
    }
    if (
        claim.get('level') in FULL_CLAIMS
        and api_statuses.intersection(UNRESOLVED_API)
    ):
        add_error(
            errors,
            'claim.api_unresolved',
            'claim.level',
            'A full-function claim is forbidden while an API is unresolved.',
        )
    return errors


def emit_result(result, as_json):
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result['valid']:
        print('Visual evidence is valid.')
        return
    print('Visual evidence is invalid:')
    for error in result['errors']:
        print(
            f"- [{error['code']}] {error['path']}: {error['message']}"
        )


def main():
    args = parse_args()
    manifest_path = args.manifest.expanduser().resolve()
    repo_root = args.repo_root.expanduser().resolve()
    errors = []
    if not manifest_path.is_file():
        add_error(
            errors,
            'manifest.not_found',
            str(manifest_path),
            'Manifest file does not exist.',
        )
        manifest = {}
    elif not repo_root.is_dir():
        add_error(
            errors,
            'repo.not_found',
            str(repo_root),
            'Repository root does not exist.',
        )
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            add_error(
                errors,
                'manifest.invalid_json',
                str(manifest_path),
                str(exc),
            )
            manifest = {}
    if not errors:
        if not isinstance(manifest, dict):
            add_error(
                errors,
                'manifest.invalid',
                str(manifest_path),
                'Manifest root must be an object.',
            )
        else:
            errors.extend(
                validate_manifest(manifest, manifest_path, repo_root)
            )
    result = {
        'valid': not errors,
        'manifest': str(manifest_path),
        'errors': errors,
    }
    emit_result(result, args.json)
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
