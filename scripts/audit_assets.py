#!/usr/bin/env python3
"""Report image metadata for visual intake without converting assets."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET


PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
JPEG_SOF = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Audit image assets without conversion dependencies.',
    )
    parser.add_argument(
        '--asset',
        action='append',
        required=True,
        type=Path,
        help='Asset path; repeat as needed.',
    )
    parser.add_argument('--json', action='store_true')
    return parser.parse_args()


def clean_svg_dimension(value):
    if not value:
        return None
    match = re.fullmatch(
        r'\s*([0-9]+(?:\.[0-9]+)?)(?:px)?\s*',
        value,
    )
    if not match:
        return None
    number = float(match.group(1))
    return int(number) if number.is_integer() else number


def parse_png(data):
    if len(data) < 29 or not data.startswith(PNG_SIGNATURE):
        return None
    if data[12:16] != b'IHDR':
        return None
    width, height = struct.unpack('>II', data[16:24])
    color_type = data[25]
    alpha_capable = color_type in (4, 6) or b'tRNS' in data
    return 'png', width, height, alpha_capable, None


def parse_jpeg(data):
    if len(data) < 4 or not data.startswith(b'\xff\xd8'):
        return None
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        segment_length = struct.unpack('>H', data[offset : offset + 2])[0]
        if (
            marker in JPEG_SOF
            and segment_length >= 7
            and offset + 7 <= len(data)
        ):
            height, width = struct.unpack(
                '>HH',
                data[offset + 3 : offset + 7],
            )
            return 'jpeg', width, height, False, None
        if segment_length < 2:
            break
        offset += segment_length
    return None


def parse_webp(data):
    if (
        len(data) < 16
        or data[:4] != b'RIFF'
        or data[8:12] != b'WEBP'
    ):
        return None
    chunk = data[12:16]
    payload = data[20:]
    if chunk == b'VP8X' and len(payload) >= 10:
        flags = payload[0]
        width = int.from_bytes(payload[4:7], 'little') + 1
        height = int.from_bytes(payload[7:10], 'little') + 1
        return 'webp', width, height, bool(flags & 0x10), None
    if chunk == b'VP8L' and len(payload) >= 5 and payload[0] == 0x2F:
        bits = int.from_bytes(payload[1:5], 'little')
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return 'webp', width, height, bool((bits >> 28) & 1), None
    if chunk == b'VP8 ' and len(payload) >= 10:
        marker = payload.find(b'\x9d\x01\x2a')
        if marker >= 0 and marker + 7 <= len(payload):
            width, height = struct.unpack(
                '<HH',
                payload[marker + 3 : marker + 7],
            )
            return (
                'webp',
                width & 0x3FFF,
                height & 0x3FFF,
                False,
                None,
            )
    return None


def parse_gif(data):
    if len(data) < 10 or data[:6] not in (b'GIF87a', b'GIF89a'):
        return None
    width, height = struct.unpack('<HH', data[6:10])
    return 'gif', width, height, True, None


def parse_svg(data):
    prefix = data[:4096].lstrip()
    if not (
        prefix.startswith(b'<svg')
        or prefix.startswith(b'<?xml')
        or b'<svg' in prefix
    ):
        return None
    try:
        root = ET.fromstring(data.decode('utf-8-sig'))
    except (UnicodeDecodeError, ET.ParseError):
        return None
    if root.tag.split('}')[-1] != 'svg':
        return None
    width = clean_svg_dimension(root.attrib.get('width'))
    height = clean_svg_dimension(root.attrib.get('height'))
    view_box = root.attrib.get('viewBox')
    if (width is None or height is None) and view_box:
        parts = view_box.replace(',', ' ').split()
        if len(parts) == 4:
            try:
                view_width = float(parts[2])
                view_height = float(parts[3])
                width = width or (
                    int(view_width)
                    if view_width.is_integer()
                    else view_width
                )
                height = height or (
                    int(view_height)
                    if view_height.is_integer()
                    else view_height
                )
            except ValueError:
                pass
    return 'svg', width, height, True, view_box


def inspect_asset(path):
    data = path.read_bytes()
    metadata = (
        parse_png(data)
        or parse_jpeg(data)
        or parse_webp(data)
        or parse_gif(data)
        or parse_svg(data)
    )
    if metadata is None:
        raise ValueError('Unsupported or malformed image format.')
    format_name, width, height, alpha_capable, view_box = metadata
    return {
        'path': str(path.resolve()),
        'format': format_name,
        'sha256': hashlib.sha256(data).hexdigest(),
        'bytes': len(data),
        'intrinsic_dimensions': {
            'width': width,
            'height': height,
        },
        'view_box': view_box,
        'alpha_capable': alpha_capable,
        'pixel_rgba_verified': False,
        'conversion_decision': 'unverified',
    }


def emit_text(assets, errors):
    for asset in assets:
        dimensions = asset['intrinsic_dimensions']
        print(
            f"{asset['path']}: {asset['format']} "
            f"{dimensions['width']}x{dimensions['height']} "
            f"{asset['bytes']} bytes sha256={asset['sha256']}"
        )
        print(
            '  conversion_decision=unverified '
            'pixel_rgba_verified=false'
        )
    for error in errors:
        print(
            f"[{error['code']}] {error['path']}: {error['message']}",
            file=sys.stderr,
        )


def main():
    args = parse_args()
    assets = []
    errors = []
    for supplied_path in args.asset:
        path = supplied_path.expanduser()
        if not path.is_file():
            errors.append(
                {
                    'code': 'asset.not_found',
                    'path': str(path),
                    'message': 'Asset file does not exist.',
                }
            )
            continue
        try:
            assets.append(inspect_asset(path))
        except (OSError, ValueError) as exc:
            errors.append(
                {
                    'code': 'asset.unsupported',
                    'path': str(path),
                    'message': str(exc),
                }
            )
    payload = {'assets': assets, 'errors': errors}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        emit_text(assets, errors)
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
