#!/usr/bin/env python3
"""Validate canonical FameEX visual evidence without third-party packages."""

import argparse
import json
import math
from pathlib import Path
import re
import sys

from audit_assets import inspect_asset
from compare_assets_rgba import (
    POLICY as RGBA_POLICY,
    TOOL_NAME as RGBA_TOOL,
    RgbaComparisonError,
    compare_assets,
    decode_asset,
)
from visual_evidence_provenance import (
    SnapshotError,
    build_receipt,
    read_receipt,
    validate_receipt,
    write_receipt,
)


VERIFIED_STATUS = 'verified'
SUPPORTED_SCHEMA_VERSION = '2.0'
TASK_MODES = {
    'exact-node-implementation',
    'feature-delivery',
    'slice-implementation',
    'audit-existing',
}
CLAIM_STATUSES = {'pending', 'verified', 'blocked'}
VISUAL_CLAIMS = {'presentation-slice-verified'}
EVIDENCE_STATUSES = {'pending', 'passed', 'failed'}
MEASUREMENT_FIELDS = ('start', 'width', 'center')
MAX_VIEWPORT_DIMENSION = 100_000
REQUIRED_COLLECTIONS = (
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
TASK_ID_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')


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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--draft',
        action='store_true',
        help='Validate an unfinished manifest without making a claim.',
    )
    mode.add_argument(
        '--require-claim',
        choices=sorted(VISUAL_CLAIMS),
        help='Require this exact verified visual claim level.',
    )
    parser.add_argument(
        '--write-receipt',
        action='store_true',
        help='Write a fresh validation receipt after the claim passes.',
    )
    args = parser.parse_args()
    if args.draft and args.write_receipt:
        parser.error('--write-receipt cannot be used with --draft')
    return args


def add_error(errors, code, path, message):
    errors.append({'code': code, 'path': path, 'message': message})


def is_number(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value)


def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def is_placeholder(value):
    return (
        isinstance(value, str)
        and re.fullmatch(r'<[^<>]+>', value.strip()) is not None
    )


def find_placeholders(value, path=''):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f'{path}.{key}' if path else str(key)
            found.extend(find_placeholders(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_placeholders(child, f'{path}[{index}]'))
    elif is_placeholder(value):
        found.append(path)
    return found


def validate_object(
    errors,
    value,
    path,
    allowed=None,
    required=None,
):
    if not isinstance(value, dict):
        add_error(
            errors,
            'schema.object_type',
            path,
            'Value must be an object.',
        )
        return False
    if allowed is not None:
        for field in sorted(set(value) - set(allowed)):
            add_error(
                errors,
                'schema.unknown_field',
                f'{path}.{field}',
                'Unknown schema field.',
            )
    if required is not None:
        for field in sorted(set(required) - set(value)):
            add_error(
                errors,
                'schema.required',
                f'{path}.{field}',
                'Required schema field is missing.',
            )
    return True


def validate_string(errors, value, path, allowed=None):
    if not is_nonempty_string(value):
        add_error(
            errors,
            'schema.string_type',
            path,
            'Value must be a non-empty string.',
        )
        return False
    if allowed is not None and value not in allowed:
        add_error(
            errors,
            'schema.enum',
            path,
            f'Value must be one of: {", ".join(sorted(allowed))}.',
        )
        return False
    return True


def validate_string_array(errors, value, path):
    if not isinstance(value, list):
        return
    for index, entry in enumerate(value):
        validate_string(errors, entry, f'{path}[{index}]')


def validate_boolean(errors, value, path):
    if not isinstance(value, bool):
        add_error(
            errors,
            'schema.boolean',
            path,
            'Value must be a boolean.',
        )
        return False
    return True


def validate_number(
    errors,
    value,
    path,
    minimum=None,
    maximum=None,
):
    if not is_number(value) or (
        minimum is not None and value < minimum
    ) or (
        maximum is not None and value > maximum
    ):
        add_error(
            errors,
            'schema.number',
            path,
            'Value must be a finite number in the allowed range.',
        )
        return False
    return True


def validate_object_array(
    errors,
    value,
    path,
    allowed=None,
    required=None,
):
    if not isinstance(value, list):
        return
    for index, entry in enumerate(value):
        validate_object(
            errors,
            entry,
            f'{path}[{index}]',
            allowed,
            required,
        )


def validate_evidence_object(errors, value, path):
    if not validate_object(
        errors,
        value,
        path,
        {'status', 'artifact'},
        {'status', 'artifact'},
    ):
        return
    validate_string(
        errors,
        value.get('status'),
        f'{path}.status',
        EVIDENCE_STATUSES,
    )
    validate_string(errors, value.get('artifact'), f'{path}.artifact')


def validate_viewport(errors, value, path, allow_short_height=False):
    allowed = {'kind', 'width', 'height'}
    if allow_short_height:
        allowed.add('short_height')
    if not validate_object(
        errors,
        value,
        path,
        allowed,
        {'kind', 'width', 'height'},
    ):
        return
    validate_string(
        errors,
        value.get('kind'),
        f'{path}.kind',
        {'desktop', 'h5'},
    )
    for field in ('width', 'height'):
        dimension = value.get(field)
        if (
            not is_number(dimension)
            or dimension <= 0
            or dimension > MAX_VIEWPORT_DIMENSION
        ):
            add_error(
                errors,
                'schema.viewport_dimension',
                f'{path}.{field}',
                'Viewport dimensions must be positive finite numbers '
                f'at most {MAX_VIEWPORT_DIMENSION}.',
            )
    if (
        allow_short_height
        and 'short_height' in value
        and not isinstance(value.get('short_height'), bool)
    ):
        add_error(
            errors,
            'schema.boolean',
            f'{path}.short_height',
            'short_height must be a boolean.',
        )


def validate_manifest_structure(errors, manifest):
    top_level = {
        'schema_version',
        'task',
        'claim',
        *REQUIRED_COLLECTIONS,
    }
    validate_object(errors, manifest, 'manifest', top_level)
    validate_object(
        errors,
        manifest.get('task'),
        'task',
        {
            'id',
            'repository',
            'mode',
            'route',
            'branch',
            'locale',
            'target_paths',
        },
    )
    validate_object(
        errors,
        manifest.get('claim'),
        'claim',
        {'status', 'level'},
    )

    required_viewports = manifest.get('required_viewports')
    validate_object_array(
        errors,
        required_viewports,
        'required_viewports',
        {
            'id',
            'kind',
            'width',
            'height',
            'full_interaction',
            'source',
        },
    )
    if isinstance(required_viewports, list):
        for index, viewport in enumerate(required_viewports):
            if not isinstance(viewport, dict):
                continue
            path = f'required_viewports[{index}]'
            validate_string(errors, viewport.get('id'), f'{path}.id')
            validate_string(
                errors,
                viewport.get('source'),
                f'{path}.source',
            )
            validate_viewport(
                errors,
                {
                    key: viewport.get(key)
                    for key in ('kind', 'width', 'height')
                },
                path,
            )
            if not isinstance(viewport.get('full_interaction'), bool):
                add_error(
                    errors,
                    'schema.boolean',
                    f'{path}.full_interaction',
                    'full_interaction must be a boolean.',
                )

    frames = manifest.get('frames')
    validate_object_array(
        errors,
        frames,
        'frames',
        {
            'id',
            'file_key',
            'node_id',
            'state',
            'viewport',
            'structured_context',
            'same_node_screenshot',
        },
    )
    if isinstance(frames, list):
        for index, frame in enumerate(frames):
            if not isinstance(frame, dict):
                continue
            path = f'frames[{index}]'
            for field in ('id', 'file_key', 'node_id', 'state'):
                validate_string(
                    errors,
                    frame.get(field),
                    f'{path}.{field}',
                )
            validate_viewport(
                errors,
                frame.get('viewport'),
                f'{path}.viewport',
            )
            validate_evidence_object(
                errors,
                frame.get('structured_context'),
                f'{path}.structured_context',
            )
            validate_evidence_object(
                errors,
                frame.get('same_node_screenshot'),
                f'{path}.same_node_screenshot',
            )

    sections = manifest.get('sections')
    validate_object_array(
        errors,
        sections,
        'sections',
        {
            'id',
            'kind',
            'frame_id',
            'sizing',
            'geometry',
            'style',
            'implementation',
            'mismatch',
            'visual_layers',
            'motion_required',
            'correction_ids',
        },
    )
    if isinstance(sections, list):
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            path = f'sections[{index}]'
            validate_string(errors, section.get('id'), f'{path}.id')
            validate_string(
                errors,
                section.get('kind'),
                f'{path}.kind',
                {'content', 'ranking', 'table', 'motion'},
            )
            validate_string(
                errors,
                section.get('frame_id'),
                f'{path}.frame_id',
            )
            sizing = section.get('sizing')
            validate_object_array(
                errors,
                sizing,
                f'{path}.sizing',
                {
                    'target',
                    'source',
                    'expected',
                    'actual',
                    'tailwind',
                    'computed',
                    'status',
                },
                {
                    'target',
                    'source',
                    'expected',
                    'actual',
                    'tailwind',
                    'computed',
                    'status',
                },
            )
            if not isinstance(sizing, list):
                add_error(
                    errors,
                    'manifest.nested_collection_type',
                    f'{path}.sizing',
                    'sizing must be an array.',
                )
            else:
                for child_index, row in enumerate(sizing):
                    if not isinstance(row, dict):
                        continue
                    row_path = f'{path}.sizing[{child_index}]'
                    for field in ('target', 'source', 'tailwind'):
                        validate_string(
                            errors,
                            row.get(field),
                            f'{row_path}.{field}',
                        )
                    for field in ('expected', 'actual'):
                        constraint = row.get(field)
                        constraint_path = f'{row_path}.{field}'
                        if not validate_object(
                            errors,
                            constraint,
                            constraint_path,
                            {'intent', 'distribution', 'gap_px'},
                            {'intent', 'distribution', 'gap_px'},
                        ):
                            continue
                        validate_string(
                            errors,
                            constraint.get('intent'),
                            f'{constraint_path}.intent',
                            {
                                'fixed',
                                'fluid',
                                'intrinsic',
                                'anchored',
                                'scroll',
                                'clipped',
                            },
                        )
                        validate_string(
                            errors,
                            constraint.get('distribution'),
                            f'{constraint_path}.distribution',
                            {
                                'start',
                                'center',
                                'end',
                                'gap',
                                'justify-between',
                                'equal-tracks',
                                'grid',
                            },
                        )
                        validate_number(
                            errors,
                            constraint.get('gap_px'),
                            f'{constraint_path}.gap_px',
                            minimum=0,
                        )
                    computed = row.get('computed')
                    computed_path = f'{row_path}.computed'
                    if validate_object(
                        errors,
                        computed,
                        computed_path,
                        {'display', 'column_gap'},
                        {'display', 'column_gap'},
                    ):
                        validate_string(
                            errors,
                            computed.get('display'),
                            f'{computed_path}.display',
                        )
                        validate_number(
                            errors,
                            computed.get('column_gap'),
                            f'{computed_path}.column_gap',
                            minimum=0,
                        )
                    validate_string(
                        errors,
                        row.get('status'),
                        f'{row_path}.status',
                        EVIDENCE_STATUSES,
                    )
            validate_evidence_object(
                errors,
                section.get('geometry'),
                f'{path}.geometry',
            )
            style = section.get('style')
            if validate_object(
                errors,
                style,
                f'{path}.style',
                {
                    'tailwind_status',
                    'computed_style_status',
                    'artifact',
                },
                {
                    'tailwind_status',
                    'computed_style_status',
                    'artifact',
                },
            ):
                for field in (
                    'tailwind_status',
                    'computed_style_status',
                ):
                    validate_string(
                        errors,
                        style.get(field),
                        f'{path}.style.{field}',
                        EVIDENCE_STATUSES,
                    )
                validate_string(
                    errors,
                    style.get('artifact'),
                    f'{path}.style.artifact',
                )
            implementation = section.get('implementation')
            if validate_object(
                errors,
                implementation,
                f'{path}.implementation',
                {'crop', 'comparison'},
                {'crop', 'comparison'},
            ):
                for field in ('crop', 'comparison'):
                    validate_string(
                        errors,
                        implementation.get(field),
                        f'{path}.implementation.{field}',
                    )
            mismatch = section.get('mismatch')
            if validate_object(
                errors,
                mismatch,
                f'{path}.mismatch',
                {'salience', 'status'},
                {'salience', 'status'},
            ):
                validate_string(
                    errors,
                    mismatch.get('salience'),
                    f'{path}.mismatch.salience',
                    {'none', 'low', 'medium', 'high'},
                )
                validate_string(
                    errors,
                    mismatch.get('status'),
                    f'{path}.mismatch.status',
                    {'open', 'blocked', 'closed'},
                )
            layers = section.get('visual_layers')
            validate_object_array(
                errors,
                layers,
                f'{path}.visual_layers',
                {
                    'id',
                    'kind',
                    'visible',
                    'source',
                    'composition',
                },
            )
            if not isinstance(layers, list):
                add_error(
                    errors,
                    'manifest.nested_collection_type',
                    f'{path}.visual_layers',
                    'visual_layers must be an array.',
                )
            else:
                for layer_index, layer in enumerate(layers):
                    if not isinstance(layer, dict):
                        continue
                    layer_path = (
                        f'{path}.visual_layers[{layer_index}]'
                    )
                    validate_string(
                        errors,
                        layer.get('id'),
                        f'{layer_path}.id',
                    )
                    validate_string(
                        errors,
                        layer.get('kind'),
                        f'{layer_path}.kind',
                        {
                            'asset',
                            'icon',
                            'mask',
                            'gradient',
                            'glow',
                            'shadow',
                            'pseudo-element',
                        },
                    )
                    validate_boolean(
                        errors,
                        layer.get('visible'),
                        f'{layer_path}.visible',
                    )
                    source = layer.get('source')
                    if validate_object(
                        errors,
                        source,
                        f'{layer_path}.source',
                        {'status', 'locator'},
                        {'status', 'locator'},
                    ):
                        validate_string(
                            errors,
                            source.get('status'),
                            f'{layer_path}.source.status',
                            {'pending', 'resolved', 'failed'},
                        )
                        validate_string(
                            errors,
                            source.get('locator'),
                            f'{layer_path}.source.locator',
                        )
                    validate_evidence_object(
                        errors,
                        layer.get('composition'),
                        f'{layer_path}.composition',
                    )
            if not isinstance(section.get('correction_ids'), list):
                add_error(
                    errors,
                    'manifest.nested_collection_type',
                    f'{path}.correction_ids',
                    'correction_ids must be an array.',
                )
            else:
                validate_string_array(
                    errors,
                    section.get('correction_ids'),
                    f'{path}.correction_ids',
                )
            if not isinstance(section.get('motion_required'), bool):
                add_error(
                    errors,
                    'schema.boolean',
                    f'{path}.motion_required',
                    'motion_required must be a boolean.',
                )

    responsive_rows = manifest.get('responsive_matrix')
    validate_object_array(
        errors,
        responsive_rows,
        'responsive_matrix',
        {'id', 'viewport', 'full_interaction'},
    )
    if isinstance(responsive_rows, list):
        for index, row in enumerate(responsive_rows):
            if not isinstance(row, dict):
                continue
            path = f'responsive_matrix[{index}]'
            validate_string(errors, row.get('id'), f'{path}.id')
            validate_viewport(
                errors,
                row.get('viewport'),
                f'{path}.viewport',
                allow_short_height=True,
            )
            interaction = row.get('full_interaction')
            interaction_fields = {
                'status',
                'trigger',
                'scroll_owner',
                'close_control',
                'final_action',
                'safe_area',
                'horizontal_scroll',
                'artifact',
            }
            if validate_object(
                errors,
                interaction,
                f'{path}.full_interaction',
                interaction_fields,
                interaction_fields,
            ):
                validate_string(
                    errors,
                    interaction.get('status'),
                    f'{path}.full_interaction.status',
                    EVIDENCE_STATUSES,
                )
                for field in (
                    'trigger',
                    'scroll_owner',
                    'close_control',
                    'final_action',
                    'safe_area',
                ):
                    validate_boolean(
                        errors,
                        interaction.get(field),
                        f'{path}.full_interaction.{field}',
                    )
                horizontal_scroll = interaction.get('horizontal_scroll')
                if not (
                    isinstance(horizontal_scroll, bool)
                    or horizontal_scroll == 'not-applicable'
                ):
                    add_error(
                        errors,
                        'schema.horizontal_scroll',
                        f'{path}.full_interaction.horizontal_scroll',
                        'horizontal_scroll must be a boolean or '
                        '"not-applicable".',
                    )
                validate_string(
                    errors,
                    interaction.get('artifact'),
                    f'{path}.full_interaction.artifact',
                )

    table_checks = manifest.get('table_checks')
    validate_object_array(
        errors,
        table_checks,
        'table_checks',
        {
            'id',
            'section_id',
            'status',
            'artifact',
            'first_column_edge',
            'last_column_edge',
            'scroll_width',
            'client_width',
            'columns',
        },
    )
    if isinstance(table_checks, list):
        for index, check in enumerate(table_checks):
            if not isinstance(check, dict):
                continue
            path = f'table_checks[{index}]'
            validate_string(errors, check.get('id'), f'{path}.id')
            validate_string(
                errors,
                check.get('section_id'),
                f'{path}.section_id',
            )
            validate_string(
                errors,
                check.get('status'),
                f'{path}.status',
                EVIDENCE_STATUSES,
            )
            validate_string(
                errors,
                check.get('artifact'),
                f'{path}.artifact',
            )
            for field in (
                'first_column_edge',
                'last_column_edge',
                'scroll_width',
                'client_width',
            ):
                validate_number(
                    errors,
                    check.get(field),
                    f'{path}.{field}',
                    minimum=0,
                )
            columns = check.get('columns')
            validate_object_array(
                errors,
                columns,
                f'{path}.columns',
                {'id', 'th', 'td'},
            )
            if not isinstance(columns, list):
                add_error(
                    errors,
                    'manifest.nested_collection_type',
                    f'{path}.columns',
                    'columns must be an array.',
                )
                continue
            for column_index, column in enumerate(columns):
                if not isinstance(column, dict):
                    continue
                column_path = f'{path}.columns[{column_index}]'
                validate_string(
                    errors,
                    column.get('id'),
                    f'{column_path}.id',
                )
                header = column.get('th')
                if validate_object(
                    errors,
                    header,
                    f'{column_path}.th',
                    set(MEASUREMENT_FIELDS),
                    set(MEASUREMENT_FIELDS),
                ):
                    for field in MEASUREMENT_FIELDS:
                        validate_number(
                            errors,
                            header.get(field),
                            f'{column_path}.th.{field}',
                        )
                cells = column.get('td')
                validate_object_array(
                    errors,
                    cells,
                    f'{column_path}.td',
                    {'row', *MEASUREMENT_FIELDS},
                )
                if not isinstance(cells, list):
                    add_error(
                        errors,
                        'manifest.nested_collection_type',
                        f'{column_path}.td',
                        'td must be an array.',
                    )
                else:
                    for cell_index, cell in enumerate(cells):
                        if not isinstance(cell, dict):
                            continue
                        cell_path = (
                            f'{column_path}.td[{cell_index}]'
                        )
                        validate_string(
                            errors,
                            cell.get('row'),
                            f'{cell_path}.row',
                            {'first', 'last', 'content-extreme'},
                        )
                        for field in MEASUREMENT_FIELDS:
                            validate_number(
                                errors,
                                cell.get(field),
                                f'{cell_path}.{field}',
                            )

    motion_checks = manifest.get('motion_checks')
    validate_object_array(
        errors,
        motion_checks,
        'motion_checks',
        {
            'id',
            'section_id',
            'kind',
            'status',
            'trigger',
            'order',
            'input_lock',
            'completion',
            'unmount',
            'artifact',
            'observer',
        },
    )
    if isinstance(motion_checks, list):
        for index, check in enumerate(motion_checks):
            if not isinstance(check, dict):
                continue
            path = f'motion_checks[{index}]'
            validate_string(errors, check.get('id'), f'{path}.id')
            validate_string(
                errors,
                check.get('section_id'),
                f'{path}.section_id',
            )
            validate_string(
                errors,
                check.get('kind'),
                f'{path}.kind',
                {
                    'interaction',
                    'intersection-observer',
                    'animation',
                },
            )
            validate_string(
                errors,
                check.get('status'),
                f'{path}.status',
                EVIDENCE_STATUSES,
            )
            for field in (
                'trigger',
                'order',
                'input_lock',
                'completion',
                'unmount',
            ):
                validate_boolean(
                    errors,
                    check.get(field),
                    f'{path}.{field}',
                )
            validate_string(
                errors,
                check.get('artifact'),
                f'{path}.artifact',
            )
            observer = check.get('observer')
            if observer is not None:
                observer_fields = {
                    'scroll_root',
                    'overflow_owner',
                    'root',
                    'root_margin',
                    'threshold',
                    'initially_visible',
                    'downward_entry_verified',
                    'upward_entry_verified',
                    'exit_verified',
                    'reentry_policy',
                    'reentry_verified',
                    'responsive_root_change_verified',
                    'opacity_transform_verified',
                    'unobserve_verified',
                    'disconnect_verified',
                    'reduced_motion_verified',
                    'unsupported_observer_verified',
                }
                observer_path = f'{path}.observer'
                if validate_object(
                    errors,
                    observer,
                    observer_path,
                    observer_fields,
                    observer_fields,
                ):
                    for field in (
                        'scroll_root',
                        'overflow_owner',
                        'root',
                        'root_margin',
                    ):
                        validate_string(
                            errors,
                            observer.get(field),
                            f'{observer_path}.{field}',
                        )
                    validate_number(
                        errors,
                        observer.get('threshold'),
                        f'{observer_path}.threshold',
                        minimum=0,
                        maximum=1,
                    )
                    validate_string(
                        errors,
                        observer.get('reentry_policy'),
                        f'{observer_path}.reentry_policy',
                        {'once', 'repeat'},
                    )
                    for field in (
                        'initially_visible',
                        'downward_entry_verified',
                        'upward_entry_verified',
                        'exit_verified',
                        'reentry_verified',
                        'responsive_root_change_verified',
                        'opacity_transform_verified',
                        'unobserve_verified',
                        'disconnect_verified',
                        'reduced_motion_verified',
                        'unsupported_observer_verified',
                    ):
                        validate_boolean(
                            errors,
                            observer.get(field),
                            f'{observer_path}.{field}',
                        )
            elif check.get('kind') == 'intersection-observer':
                add_error(
                    errors,
                    'schema.required',
                    f'{path}.observer',
                    'IntersectionObserver evidence is required.',
                )

    historical_reuse = manifest.get('historical_reuse')
    validate_object_array(
        errors,
        historical_reuse,
        'historical_reuse',
        {
            'route',
            'viewport',
            'state',
            'source_component',
            'source_capability',
            'source_asset',
            'requested_part',
            'decision',
            'evidence',
        },
    )
    if isinstance(historical_reuse, list):
        for index, entry in enumerate(historical_reuse):
            if not isinstance(entry, dict):
                continue
            path = f'historical_reuse[{index}]'
            for field in (
                'route',
                'state',
                'source_component',
                'source_capability',
                'source_asset',
                'requested_part',
                'evidence',
            ):
                validate_string(
                    errors,
                    entry.get(field),
                    f'{path}.{field}',
                )
            validate_viewport(
                errors,
                entry.get('viewport'),
                f'{path}.viewport',
            )
            validate_string(
                errors,
                entry.get('decision'),
                f'{path}.decision',
                {'reuse', 'adapt', 'promote', 'reject'},
            )

    entry_surfaces = manifest.get('entry_surfaces')
    validate_object_array(
        errors,
        entry_surfaces,
        'entry_surfaces',
        {
            'kind',
            'owner',
            'source',
            'configuration_location',
            'status',
            'evidence',
        },
    )
    if isinstance(entry_surfaces, list):
        for index, entry in enumerate(entry_surfaces):
            if not isinstance(entry, dict):
                continue
            path = f'entry_surfaces[{index}]'
            for field in (
                'owner',
                'source',
                'configuration_location',
                'evidence',
            ):
                validate_string(
                    errors,
                    entry.get(field),
                    f'{path}.{field}',
                )
            validate_string(
                errors,
                entry.get('kind'),
                f'{path}.kind',
                {
                    'canonical-route',
                    'operational-exposure',
                    'app-webview',
                    'page-cta',
                    'share-destination',
                },
            )
            validate_string(
                errors,
                entry.get('status'),
                f'{path}.status',
                {'pending', 'verified', 'unresolved'},
            )

    conversions = manifest.get('asset_conversions')
    validate_object_array(
        errors,
        conversions,
        'asset_conversions',
        {
            'source',
            'candidate',
            'target_format',
            'decision',
            'before_bytes',
            'after_bytes',
            'source_dimensions',
            'candidate_dimensions',
            'alpha',
            'visual_comparison',
        },
    )
    if isinstance(conversions, list):
        for index, conversion in enumerate(conversions):
            if not isinstance(conversion, dict):
                continue
            path = f'asset_conversions[{index}]'
            for field in (
                'source',
                'candidate',
            ):
                validate_string(
                    errors,
                    conversion.get(field),
                    f'{path}.{field}',
                )
            validate_string(
                errors,
                conversion.get('target_format'),
                f'{path}.target_format',
                {'webp'},
            )
            validate_string(
                errors,
                conversion.get('decision'),
                f'{path}.decision',
                {'unverified', 'accepted', 'rejected'},
            )
            for field in ('before_bytes', 'after_bytes'):
                value = conversion.get(field)
                if (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value < 0
                ):
                    add_error(
                        errors,
                        'schema.byte_count',
                        f'{path}.{field}',
                        'Asset byte counts must be non-negative integers.',
                    )
            for field in ('source_dimensions', 'candidate_dimensions'):
                dimensions = conversion.get(field)
                if validate_object(
                    errors,
                    dimensions,
                    f'{path}.{field}',
                    {'width', 'height'},
                    {'width', 'height'},
                ):
                    for dimension in ('width', 'height'):
                        validate_number(
                            errors,
                            dimensions.get(dimension),
                            f'{path}.{field}.{dimension}',
                            minimum=0,
                        )
            alpha = conversion.get('alpha')
            if validate_object(
                errors,
                alpha,
                f'{path}.alpha',
                {'source', 'candidate'},
                {'source', 'candidate'},
            ):
                for field in ('source', 'candidate'):
                    validate_string(
                        errors,
                        alpha.get(field),
                        f'{path}.alpha.{field}',
                        {'opaque', 'transparent'},
                    )
            comparison = conversion.get('visual_comparison')
            comparison_fields = {
                'status',
                'tool',
                'artifact',
                'policy',
                'required_artifact_fields',
            }
            if validate_object(
                errors,
                comparison,
                f'{path}.visual_comparison',
                comparison_fields,
                {'status', 'tool', 'artifact', 'policy'},
            ):
                validate_string(
                    errors,
                    comparison.get('status'),
                    f'{path}.visual_comparison.status',
                    {'unverified', 'passed', 'failed'},
                )
                validate_string(
                    errors,
                    comparison.get('tool'),
                    f'{path}.visual_comparison.tool',
                    {RGBA_TOOL},
                )
                validate_string(
                    errors,
                    comparison.get('policy'),
                    f'{path}.visual_comparison.policy',
                    {RGBA_POLICY},
                )
                validate_string(
                    errors,
                    comparison.get('artifact'),
                    f'{path}.visual_comparison.artifact',
                )
                required_fields = comparison.get(
                    'required_artifact_fields'
                )
                if (
                    required_fields is not None
                    and (
                        not isinstance(required_fields, list)
                        or not required_fields
                    )
                ):
                    add_error(
                        errors,
                        'schema.required_artifact_fields',
                        (
                            f'{path}.visual_comparison.'
                            'required_artifact_fields'
                        ),
                        'Comparison artifact fields must be a non-empty array.',
                    )
                elif required_fields is not None:
                    validate_string_array(
                        errors,
                        required_fields,
                        (
                            f'{path}.visual_comparison.'
                            'required_artifact_fields'
                        ),
                    )

    corrections = manifest.get('corrections')
    validate_object_array(
        errors,
        corrections,
        'corrections',
        {
            'id',
            'source',
            'affected_rows',
            'status',
            'reverification',
        },
    )
    if isinstance(corrections, list):
        for index, correction in enumerate(corrections):
            if not isinstance(correction, dict):
                continue
            path = f'corrections[{index}]'
            validate_string(
                errors,
                correction.get('id'),
                f'{path}.id',
            )
            validate_string(
                errors,
                correction.get('status'),
                f'{path}.status',
                {'open', 'blocked', 'closed'},
            )
            source = correction.get('source')
            if validate_object(
                errors,
                source,
                f'{path}.source',
                {'kind', 'locator'},
                {'kind', 'locator'},
            ):
                validate_string(
                    errors,
                    source.get('kind'),
                    f'{path}.source.kind',
                    {
                        'user-feedback',
                        'product-update',
                        'design-update',
                    },
                )
                validate_string(
                    errors,
                    source.get('locator'),
                    f'{path}.source.locator',
                )
            if not isinstance(correction.get('affected_rows'), list):
                add_error(
                    errors,
                    'manifest.nested_collection_type',
                    f'{path}.affected_rows',
                    'affected_rows must be an array.',
                )
            else:
                validate_string_array(
                    errors,
                    correction.get('affected_rows'),
                    f'{path}.affected_rows',
                )
            validate_evidence_object(
                errors,
                correction.get('reverification'),
                f'{path}.reverification',
            )

    api_contracts = manifest.get('api_contracts')
    validate_object_array(
        errors,
        api_contracts,
        'api_contracts',
        {'id', 'status'},
    )
    if isinstance(api_contracts, list):
        for index, contract in enumerate(api_contracts):
            if not isinstance(contract, dict):
                continue
            path = f'api_contracts[{index}]'
            validate_string(errors, contract.get('id'), f'{path}.id')
            validate_string(
                errors,
                contract.get('status'),
                f'{path}.status',
                {
                    'not-required',
                    'waiting',
                    'documented',
                    'integrated',
                    'verified',
                    'unresolved',
                },
            )


def validate_schema(manifest, repo_root):
    errors = []
    required = (
        'schema_version',
        'task',
        'claim',
        *REQUIRED_COLLECTIONS,
    )
    for key in required:
        if key not in manifest:
            add_error(
                errors,
                'manifest.required',
                key,
                f'Missing required top-level key: {key}',
            )
    if errors:
        return errors

    if manifest.get('schema_version') != SUPPORTED_SCHEMA_VERSION:
        add_error(
            errors,
            'schema.version',
            'schema_version',
            f'Schema version must be {SUPPORTED_SCHEMA_VERSION}. Copy '
            'assets/templates/visual-evidence.json, recapture typed '
            'artifacts, and generate a new receipt; do not promote a v1 '
            'claim in place.',
        )

    task = manifest.get('task')
    if not isinstance(task, dict):
        add_error(
            errors,
            'task.type',
            'task',
            'Task must be an object.',
        )
    else:
        required_task_fields = (
            'id',
            'repository',
            'mode',
            'route',
            'branch',
            'locale',
            'target_paths',
        )
        for field in required_task_fields:
            if field not in task:
                add_error(
                    errors,
                    'task.required',
                    f'task.{field}',
                    f'Task {field} is required.',
                )
        task_id = task.get('id')
        if (
            not is_nonempty_string(task_id)
            or TASK_ID_PATTERN.fullmatch(task_id) is None
        ):
            add_error(
                errors,
                'task.id',
                'task.id',
                'Task id must be a safe slug.',
            )
        repository = task.get('repository')
        if not is_nonempty_string(repository):
            add_error(
                errors,
                'task.repository',
                'task.repository',
                'Repository is required.',
            )
        else:
            declared_path = Path(repository).expanduser()
            if (
                not declared_path.is_absolute()
                or declared_path.resolve() != repo_root.resolve()
            ):
                add_error(
                    errors,
                    'task.repository_mismatch',
                    'task.repository',
                    'Manifest repository must match --repo-root.',
                )
        if (
            not is_nonempty_string(task.get('mode'))
            or task.get('mode') not in TASK_MODES
        ):
            add_error(
                errors,
                'task.mode',
                'task.mode',
                'Task mode is not supported by visual evidence.',
            )
        route = task.get('route')
        if not is_nonempty_string(route) or not route.startswith('/'):
            add_error(
                errors,
                'task.route',
                'task.route',
                'Canonical route must start with "/".',
            )
        for field in ('branch', 'locale'):
            if not is_nonempty_string(task.get(field)):
                add_error(
                    errors,
                    f'task.{field}',
                    f'task.{field}',
                    f'Task {field} must be a non-empty string.',
                )
        target_paths = task.get('target_paths')
        if not isinstance(target_paths, list) or not target_paths:
            add_error(
                errors,
                'task.target_paths',
                'task.target_paths',
                'At least one repository-relative target path is required.',
            )
        else:
            for index, target in enumerate(target_paths):
                target_path = Path(target) if is_nonempty_string(target) else None
                if (
                    target_path is None
                    or target_path.is_absolute()
                    or '..' in target_path.parts
                ):
                    add_error(
                        errors,
                        'task.target_path',
                        f'task.target_paths[{index}]',
                        'Target paths must be safe repository-relative paths.',
                    )

    claim = manifest.get('claim')
    if not isinstance(claim, dict):
        add_error(
            errors,
            'claim.type',
            'claim',
            'Claim must be an object.',
        )
    else:
        if (
            not is_nonempty_string(claim.get('status'))
            or claim.get('status') not in CLAIM_STATUSES
        ):
            add_error(
                errors,
                'claim.status',
                'claim.status',
                'Claim status must be pending, blocked, or verified.',
            )
        if (
            not is_nonempty_string(claim.get('level'))
            or claim.get('level') not in VISUAL_CLAIMS
        ):
            add_error(
                errors,
                'claim.level',
                'claim.level',
                'Visual evidence supports only a verified presentation '
                'slice. Feature regression requires a separate aggregate '
                'gate.',
            )

    for collection in REQUIRED_COLLECTIONS:
        if not isinstance(manifest.get(collection), list):
            add_error(
                errors,
                'manifest.collection_type',
                collection,
                f'{collection} must be an array.',
            )
    validate_manifest_structure(errors, manifest)

    for path in find_placeholders(manifest):
        add_error(
            errors,
            'manifest.placeholder',
            path,
            'Template placeholders must be replaced before validation.',
        )
    return errors


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


def collect_evidence_artifacts(manifest, manifest_dir, repo_root):
    artifacts = set()

    def add(value):
        resolved = resolve_artifact(value, manifest_dir, repo_root)
        if (
            resolved is not None
            and is_within(resolved, manifest_dir.resolve())
        ):
            artifacts.add(resolved)

    for frame in manifest.get('frames', []):
        add(frame.get('structured_context', {}).get('artifact'))
        add(frame.get('same_node_screenshot', {}).get('artifact'))
    for section in manifest.get('sections', []):
        add(section.get('geometry', {}).get('artifact'))
        add(section.get('style', {}).get('artifact'))
        implementation = section.get('implementation', {})
        add(implementation.get('crop'))
        add(implementation.get('comparison'))
        for layer in section.get('visual_layers', []):
            add(layer.get('composition', {}).get('artifact'))
    for row in manifest.get('responsive_matrix', []):
        add(row.get('full_interaction', {}).get('artifact'))
    for collection in ('table_checks', 'motion_checks'):
        for entry in manifest.get(collection, []):
            add(entry.get('artifact'))
    for entry in manifest.get('historical_reuse', []):
        add(entry.get('evidence'))
    for entry in manifest.get('entry_surfaces', []):
        add(entry.get('evidence'))
    for conversion in manifest.get('asset_conversions', []):
        add(conversion.get('visual_comparison', {}).get('artifact'))
    for correction in manifest.get('corrections', []):
        add(correction.get('reverification', {}).get('artifact'))
    return artifacts


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


def require_json_evidence(
    errors,
    evidence,
    path,
    code,
    manifest_dir,
    repo_root,
    expected_sources,
):
    artifact = require_artifact(
        errors,
        evidence,
        path,
        code,
        manifest_dir,
        repo_root,
    )
    payload = read_json_artifact(artifact)
    if (
        payload is None
        or payload.get('status') != 'passed'
        or payload.get('source') not in expected_sources
    ):
        add_error(
            errors,
            'artifact.json_evidence',
            f'{path}.artifact',
            'JSON evidence must identify an allowed source and passed '
            'status.',
        )
        return None
    return payload


def require_raster_evidence(
    errors,
    evidence,
    path,
    code,
    manifest_dir,
    repo_root,
):
    artifact = require_artifact(
        errors,
        evidence,
        path,
        code,
        manifest_dir,
        repo_root,
    )
    if artifact is None:
        return None
    try:
        audited = inspect_asset(artifact)
        decoded, _decoder = decode_asset(artifact)
    except (OSError, ValueError) as exc:
        add_error(
            errors,
            'artifact.image_invalid',
            f'{path}.artifact',
            f'Raster evidence is not a valid image: {exc}',
        )
        return None
    dimensions = audited.get('intrinsic_dimensions', {})
    if (
        audited.get('format') not in {'png', 'jpeg', 'webp'}
        or not is_number(dimensions.get('width'))
        or not is_number(dimensions.get('height'))
        or dimensions.get('width') <= 0
        or dimensions.get('height') <= 0
        or decoded.get('width') != dimensions.get('width')
        or decoded.get('height') != dimensions.get('height')
        or len(decoded.get('rgba', b''))
        != dimensions.get('width') * dimensions.get('height') * 4
    ):
        add_error(
            errors,
            'artifact.image_invalid',
            f'{path}.artifact',
            'Raster evidence must be a PNG, JPEG, or WebP with positive '
            'intrinsic dimensions.',
        )
        return None
    return artifact


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
            payload = require_json_evidence(
                errors,
                context,
                f'{path}.structured_context',
                'frame.context',
                manifest_dir,
                repo_root,
                {'figma-mcp'},
            )
            if payload is not None and (
                payload.get('file_key') != frame.get('file_key')
                or payload.get('node_id') != frame.get('node_id')
            ):
                add_error(
                    errors,
                    'frame.context_identity',
                    f'{path}.structured_context.artifact',
                    'Figma context evidence must match this exact file '
                    'and node.',
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
            require_raster_evidence(
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
            payload = require_json_evidence(
                errors,
                geometry,
                f'{path}.geometry',
                'section.geometry',
                manifest_dir,
                repo_root,
                {'playwright'},
            )
            if payload is not None and (
                section_id not in payload.get('section_ids', [])
                or not payload.get('measurements')
            ):
                add_error(
                    errors,
                    'section.geometry_payload',
                    f'{path}.geometry.artifact',
                    'Geometry evidence must contain this section and '
                    'non-empty measurements.',
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
            payload = require_json_evidence(
                errors,
                style,
                f'{path}.style',
                'section.style',
                manifest_dir,
                repo_root,
                {'playwright'},
            )
            if payload is not None and (
                section_id not in payload.get('section_ids', [])
                or not payload.get('computed_styles')
            ):
                add_error(
                    errors,
                    'section.style_payload',
                    f'{path}.style.artifact',
                    'Style evidence must contain this section and '
                    'non-empty computed styles.',
                )

        implementation = section.get('implementation', {})
        for field in ('crop', 'comparison'):
            require_raster_evidence(
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
                payload = require_json_evidence(
                    errors,
                    composition,
                    f'{layer_path}.composition',
                    'layer.composition',
                    manifest_dir,
                    repo_root,
                    {'figma-mcp', 'playwright'},
                )
                if payload is not None and (
                    layer.get('id')
                    not in payload.get('layer_ids', [])
                ):
                    add_error(
                        errors,
                        'layer.composition_payload',
                        f'{layer_path}.composition.artifact',
                        'Composition evidence must identify this layer.',
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
                    'Sizing target, source, Tailwind, computed values, and '
                    'passed status are required.',
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
            'Interaction artifact must be machine-readable Playwright '
            'evidence for the same viewport and steps.',
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
        payload = require_json_evidence(
            errors,
            check,
            path,
            'table.artifact',
            manifest_dir,
            repo_root,
            {'playwright'},
        )
        columns = check.get('columns', [])
        metrics = {
            field: check.get(field)
            for field in (
                'first_column_edge',
                'last_column_edge',
                'scroll_width',
                'client_width',
            )
        }
        if payload is not None and (
            payload.get('section_id') != check.get('section_id')
            or payload.get('columns') != columns
            or payload.get('metrics') != metrics
        ):
            add_error(
                errors,
                'table.artifact_payload',
                f'{path}.artifact',
                'Table artifact must match the section, columns, and '
                'container metrics in the manifest.',
            )
        if check.get('scroll_width') < check.get('client_width'):
            add_error(
                errors,
                'table.scroll_metrics',
                path,
                'scroll_width must be greater than or equal to '
                'client_width.',
            )
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
            represented_rows = {
                cell.get('row')
                for cell in cells
                if isinstance(cell, dict)
            }
            required_rows = {'first', 'last', 'content-extreme'}
            if not required_rows.issubset(represented_rows):
                add_error(
                    errors,
                    'table.representative_rows',
                    f'{column_path}.td',
                    'Each column requires first, last, and content-extreme '
                    'measurements.',
                )
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
        if check.get('kind') == 'intersection-observer':
            observer = check.get('observer', {})
            observer_checks = (
                'initially_visible',
                'downward_entry_verified',
                'upward_entry_verified',
                'exit_verified',
                'reentry_verified',
                'responsive_root_change_verified',
                'opacity_transform_verified',
                'unobserve_verified',
                'disconnect_verified',
                'reduced_motion_verified',
                'unsupported_observer_verified',
            )
            if not all(
                observer.get(field) is True
                for field in observer_checks
            ):
                add_error(
                    errors,
                    'motion.observer',
                    f'{path}.observer',
                    'IntersectionObserver lifecycle, fallback, and '
                    'responsive evidence must pass.',
                )
        payload = require_json_evidence(
            errors,
            check,
            path,
            'motion.artifact',
            manifest_dir,
            repo_root,
            {'playwright'},
        )
        expected_checks = {
            field: check.get(field)
            for field in fields
        }
        if payload is not None and (
            payload.get('section_id') != check.get('section_id')
            or payload.get('kind') != check.get('kind')
            or payload.get('checks') != expected_checks
            or (
                check.get('kind') == 'intersection-observer'
                and payload.get('observer') != check.get('observer')
            )
        ):
            add_error(
                errors,
                'motion.artifact_payload',
                f'{path}.artifact',
                'Motion artifact must match the section, kind, lifecycle '
                'checks, and observer evidence.',
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
            require_raster_evidence(
                errors,
                reverify,
                f'{path}.reverification',
                'correction.reverification',
                manifest_dir,
                repo_root,
            )


def validate_declared_evidence(
    errors,
    entries,
    collection,
    code,
    manifest_dir,
    repo_root,
):
    for index, entry in enumerate(entries):
        payload = require_json_evidence(
            errors,
            {'artifact': entry.get('evidence')},
            f'{collection}[{index}].evidence',
            code,
            manifest_dir,
            repo_root,
            {
                'figma-mcp',
                'playwright',
                'repository-audit',
                'product-document',
                'app-config',
            },
        )
        if payload is not None and payload.get('kind') != collection:
            add_error(
                errors,
                'artifact.declared_evidence',
                f'{collection}[{index}].evidence',
                'Declared evidence must identify its manifest collection.',
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
        try:
            computed_comparison = compare_assets(
                source_path,
                candidate_path,
            )
        except (OSError, RgbaComparisonError) as exc:
            add_error(
                errors,
                'asset.rgba_decode',
                path,
                f'Accepted WebP requires decoded RGBA evidence: {exc}',
            )
            continue
        decoded_dimensions_match = (
            computed_comparison['source_dimensions']
            == computed_comparison['candidate_dimensions']
            == conversion.get('source_dimensions')
            == conversion.get('candidate_dimensions')
        )
        decoded_alpha = {
            'source': computed_comparison['alpha']['source']['mode'],
            'candidate': computed_comparison['alpha']['candidate'][
                'mode'
            ],
        }
        alpha_match = (
            conversion.get('alpha') == decoded_alpha
            and decoded_alpha['source'] == decoded_alpha['candidate']
            and candidate_audit['format'] == 'webp'
        )
        comparison_artifact = resolve_artifact(
            comparison.get('artifact'),
            manifest_dir,
            repo_root,
        )
        comparison_payload = read_json_artifact(comparison_artifact)
        comparison_valid = (
            comparison.get('status') == 'passed'
            and comparison.get('tool') == RGBA_TOOL
            and comparison.get('policy') == RGBA_POLICY
            and comparison_artifact is not None
            and is_within(
                comparison_artifact,
                manifest_dir.resolve(),
            )
            and comparison_payload is not None
            and computed_comparison.get('status') == 'passed'
            and computed_comparison.get('different_pixels') == 0
            and computed_comparison.get('max_channel_delta') == 0
            and computed_comparison.get('alpha_different_pixels') == 0
            and comparison_payload == computed_comparison
        )
        if not (
            recorded_dimensions_match
            and audited_dimensions_match
            and decoded_dimensions_match
            and bytes_valid
            and alpha_match
            and comparison_valid
        ):
            add_error(
                errors,
                'asset.webp_comparison',
                path,
                'Accepted WebP requires size, dimension, alpha, and visual '
                'comparison evidence.',
            )


def validate_manifest(manifest, manifest_path, repo_root):
    errors = []
    task = manifest.get('task', {})
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
    validate_declared_evidence(
        errors,
        manifest.get('historical_reuse', []),
        'historical_reuse',
        'historical_reuse.evidence',
        manifest_dir,
        repo_root,
    )
    validate_declared_evidence(
        errors,
        manifest.get('entry_surfaces', []),
        'entry_surfaces',
        'entry_surface.evidence',
        manifest_dir,
        repo_root,
    )
    validate_asset_conversions(
        errors,
        manifest.get('asset_conversions', []),
        manifest_dir,
        repo_root,
    )

    return errors


def emit_result(result, as_json):
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result['valid']:
        if result['claim_ready']:
            print('Visual evidence claim is ready.')
        else:
            print('Visual evidence draft schema is valid.')
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
    schema_errors = []
    claim_errors = []
    if not manifest_path.is_file():
        add_error(
            schema_errors,
            'manifest.not_found',
            str(manifest_path),
            'Manifest file does not exist.',
        )
        manifest = {}
    elif not repo_root.is_dir():
        add_error(
            schema_errors,
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
                schema_errors,
                'manifest.invalid_json',
                str(manifest_path),
                str(exc),
            )
            manifest = {}
    if not schema_errors:
        if not isinstance(manifest, dict):
            add_error(
                schema_errors,
                'manifest.invalid',
                str(manifest_path),
                'Manifest root must be an object.',
            )
        else:
            schema_errors.extend(validate_schema(manifest, repo_root))

    schema_valid = not schema_errors
    claim_ready = False
    receipt_path = manifest_path.parent / 'validation-receipt.json'
    if schema_valid:
        claim = manifest['claim']
        if args.draft:
            if claim.get('status') == VERIFIED_STATUS:
                add_error(
                    claim_errors,
                    'claim.draft_status',
                    'claim.status',
                    'Draft mode cannot validate a verified claim.',
                )
        elif claim.get('status') != VERIFIED_STATUS:
            add_error(
                claim_errors,
                'claim.not_verified',
                'claim.status',
                'Completion validation requires claim.status=verified.',
            )
        else:
            claim_errors.extend(
                validate_manifest(manifest, manifest_path, repo_root)
            )
            if (
                args.require_claim
                and claim.get('level') != args.require_claim
            ):
                add_error(
                    claim_errors,
                    'claim.level_mismatch',
                    'claim.level',
                    f'Expected claim level {args.require_claim}.',
                )
            artifacts = collect_evidence_artifacts(
                manifest,
                manifest_path.parent,
                repo_root,
            )
            if args.write_receipt:
                if not claim_errors:
                    try:
                        receipt = build_receipt(
                            manifest_path=manifest_path,
                            repo_root=repo_root,
                            target_paths=manifest['task'][
                                'target_paths'
                            ],
                            artifacts=artifacts,
                            claim=claim,
                        )
                        write_receipt(receipt_path, receipt)
                    except (OSError, SnapshotError) as exc:
                        add_error(
                            claim_errors,
                            'receipt.snapshot_failed',
                            str(receipt_path),
                            str(exc),
                        )
            elif not receipt_path.is_file():
                add_error(
                    claim_errors,
                    'receipt.missing',
                    str(receipt_path),
                    'A fresh validation receipt is required.',
                )
            else:
                try:
                    receipt = read_receipt(receipt_path)
                    claim_errors.extend(
                        validate_receipt(
                            receipt=receipt,
                            manifest_path=manifest_path,
                            repo_root=repo_root,
                            target_paths=manifest['task'][
                                'target_paths'
                            ],
                            artifacts=artifacts,
                            claim=claim,
                        )
                    )
                except SnapshotError as exc:
                    add_error(
                        claim_errors,
                        'receipt.invalid',
                        str(receipt_path),
                        str(exc),
                    )
            claim_ready = not claim_errors

    valid = (
        schema_valid
        and (
            (args.draft and not claim_errors)
            or (not args.draft and claim_ready)
        )
    )
    errors = [*schema_errors, *claim_errors]
    result = {
        'valid': valid,
        'schema_valid': schema_valid,
        'claim_ready': claim_ready,
        'manifest': str(manifest_path),
        'receipt': str(receipt_path),
        'errors': errors,
        'schema_errors': schema_errors,
        'claim_errors': claim_errors,
    }
    emit_result(result, args.json)
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
