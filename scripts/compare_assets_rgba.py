#!/usr/bin/env python3
"""Decode two images and compare their real RGBA pixels."""

import argparse
import binascii
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib


try:
    import PIL
    from PIL import Image as PIL_IMAGE
except ImportError:
    PIL = None
    PIL_IMAGE = None


PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
SIPS_PATH = Path('/usr/bin/sips')
TOOL_NAME = 'compare-assets-rgba'
TOOL_VERSION = '2.0'
POLICY = 'lossless-exact'


class RgbaComparisonError(ValueError):
    """Raised when real RGBA pixels cannot be decoded safely."""


def parse_args():
    parser = argparse.ArgumentParser(
        description='Compare decoded image pixels using exact RGBA.',
    )
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--json', action='store_true')
    return parser.parse_args()


def paeth_predictor(left, up, upper_left):
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def unfilter_row(filter_type, encoded, previous, bytes_per_pixel):
    decoded = bytearray(len(encoded))
    for index, value in enumerate(encoded):
        left = (
            decoded[index - bytes_per_pixel]
            if index >= bytes_per_pixel
            else 0
        )
        up = previous[index] if previous is not None else 0
        upper_left = (
            previous[index - bytes_per_pixel]
            if previous is not None and index >= bytes_per_pixel
            else 0
        )
        if filter_type == 0:
            prediction = 0
        elif filter_type == 1:
            prediction = left
        elif filter_type == 2:
            prediction = up
        elif filter_type == 3:
            prediction = (left + up) // 2
        elif filter_type == 4:
            prediction = paeth_predictor(left, up, upper_left)
        else:
            raise RgbaComparisonError(
                f'Unsupported PNG filter type: {filter_type}'
            )
        decoded[index] = (value + prediction) & 0xFF
    return bytes(decoded)


def read_png_chunks(data):
    if not data.startswith(PNG_SIGNATURE):
        raise RgbaComparisonError('Decoded output is not a PNG image.')
    offset = len(PNG_SIGNATURE)
    chunks = []
    while offset + 12 <= len(data):
        length = struct.unpack('>I', data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise RgbaComparisonError('PNG chunk is truncated.')
        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack('>I', data[payload_end:crc_end])[0]
        actual_crc = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise RgbaComparisonError('PNG chunk CRC is invalid.')
        chunks.append((chunk_type, payload))
        offset = crc_end
        if chunk_type == b'IEND':
            break
    if not chunks or chunks[-1][0] != b'IEND':
        raise RgbaComparisonError('PNG is missing a complete IEND chunk.')
    return chunks


def decode_png(data):
    chunks = read_png_chunks(data)
    ihdr = next(
        (payload for kind, payload in chunks if kind == b'IHDR'),
        None,
    )
    if ihdr is None or len(ihdr) != 13:
        raise RgbaComparisonError('PNG IHDR is missing or invalid.')
    (
        width,
        height,
        bit_depth,
        color_type,
        compression,
        filter_method,
        interlace,
    ) = struct.unpack('>IIBBBBB', ihdr)
    if (
        not width
        or not height
        or bit_depth != 8
        or compression != 0
        or filter_method != 0
        or interlace != 0
    ):
        raise RgbaComparisonError(
            'Only non-interlaced 8-bit PNG output is supported.'
        )
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise RgbaComparisonError(
            f'Unsupported PNG color type: {color_type}'
        )
    compressed = b''.join(
        payload for kind, payload in chunks if kind == b'IDAT'
    )
    if not compressed:
        raise RgbaComparisonError('PNG contains no pixel data.')
    try:
        scanlines = zlib.decompress(compressed)
    except zlib.error as exc:
        raise RgbaComparisonError('PNG pixel data is invalid.') from exc
    stride = width * channels
    expected_bytes = height * (stride + 1)
    if len(scanlines) != expected_bytes:
        raise RgbaComparisonError('PNG scanline length is invalid.')
    palette = next(
        (payload for kind, payload in chunks if kind == b'PLTE'),
        b'',
    )
    transparency = next(
        (payload for kind, payload in chunks if kind == b'tRNS'),
        b'',
    )
    rows = []
    previous = None
    offset = 0
    for _ in range(height):
        filter_type = scanlines[offset]
        encoded = scanlines[offset + 1 : offset + 1 + stride]
        decoded = unfilter_row(
            filter_type,
            encoded,
            previous,
            channels,
        )
        rows.append(decoded)
        previous = decoded
        offset += stride + 1

    rgba = bytearray()
    for row in rows:
        for offset in range(0, len(row), channels):
            pixel = row[offset : offset + channels]
            if color_type == 0:
                rgba.extend((pixel[0], pixel[0], pixel[0], 255))
            elif color_type == 2:
                rgba.extend((pixel[0], pixel[1], pixel[2], 255))
            elif color_type == 3:
                palette_index = pixel[0]
                palette_offset = palette_index * 3
                if palette_offset + 3 > len(palette):
                    raise RgbaComparisonError(
                        'PNG palette index is out of range.'
                    )
                alpha = (
                    transparency[palette_index]
                    if palette_index < len(transparency)
                    else 255
                )
                rgba.extend(
                    (
                        palette[palette_offset],
                        palette[palette_offset + 1],
                        palette[palette_offset + 2],
                        alpha,
                    )
                )
            elif color_type == 4:
                rgba.extend((pixel[0], pixel[0], pixel[0], pixel[1]))
            else:
                rgba.extend(pixel)
    return {
        'width': width,
        'height': height,
        'rgba': bytes(rgba),
    }


def decode_with_pillow(path):
    try:
        with PIL_IMAGE.open(path) as image:
            rgba = image.convert('RGBA')
            return {
                'width': rgba.width,
                'height': rgba.height,
                'rgba': rgba.tobytes(),
            }
    except Exception as exc:
        raise RgbaComparisonError(
            f'Pillow could not decode {path.name}: {exc}'
        ) from exc


@lru_cache(maxsize=1)
def sips_version():
    result = subprocess.run(
        [str(SIPS_PATH), '--version'],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return 'unknown'
    return result.stdout.strip() or result.stderr.strip() or 'unknown'


def decode_with_sips(path):
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / 'decoded.png'
        result = subprocess.run(
            [
                str(SIPS_PATH),
                '-s',
                'format',
                'png',
                str(path),
                '--out',
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode or not output.is_file():
            message = result.stderr.strip() or result.stdout.strip()
            raise RgbaComparisonError(
                f'sips could not decode {path.name}: {message}'
            )
        return decode_png(output.read_bytes())


def decoder_candidates():
    candidates = []
    if PIL_IMAGE is not None:
        candidates.append(
            (
                decode_with_pillow,
                {'name': 'pillow', 'version': PIL.__version__},
            )
        )
    if SIPS_PATH.is_file():
        candidates.append(
            (
                decode_with_sips,
                {'name': 'sips', 'version': sips_version()},
            )
        )
    if not candidates:
        raise RgbaComparisonError(
            'No RGBA decoder is available; install Pillow with WebP '
            'support or run on macOS with /usr/bin/sips.'
        )
    return candidates


def decode_pair(source, candidate):
    failures = []
    for decoder, metadata in decoder_candidates():
        try:
            return decoder(source), decoder(candidate), metadata
        except (OSError, RgbaComparisonError) as exc:
            failures.append(f'{metadata["name"]}: {exc}')
    raise RgbaComparisonError(
        'No available decoder could read both assets: '
        + '; '.join(failures)
    )


def decode_asset(path):
    failures = []
    for decoder, metadata in decoder_candidates():
        try:
            return decoder(path), metadata
        except (OSError, RgbaComparisonError) as exc:
            failures.append(f'{metadata["name"]}: {exc}')
    raise RgbaComparisonError(
        'No available decoder could read the asset: '
        + '; '.join(failures)
    )


def alpha_statistics(rgba, width, height):
    transparent_pixels = 0
    partial_alpha_pixels = 0
    min_x = width
    min_y = height
    max_x = -1
    max_y = -1
    for index in range(width * height):
        alpha = rgba[(index * 4) + 3]
        if alpha < 255:
            x = index % width
            y = index // width
            transparent_pixels += 1
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        if 0 < alpha < 255:
            partial_alpha_pixels += 1
    if transparent_pixels:
        bounds = {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x + 1,
            'height': max_y - min_y + 1,
        }
    else:
        bounds = None
    return {
        'mode': 'transparent' if transparent_pixels else 'opaque',
        'transparent_pixels': transparent_pixels,
        'partial_alpha_pixels': partial_alpha_pixels,
        'bounds': bounds,
    }


def compare_assets(source, candidate):
    source = Path(source)
    candidate = Path(candidate)
    if not source.is_file() or not candidate.is_file():
        raise RgbaComparisonError('Both comparison assets must exist.')
    (
        source_decoded,
        candidate_decoded,
        decoder_metadata,
    ) = decode_pair(source, candidate)
    source_dimensions = {
        'width': source_decoded['width'],
        'height': source_decoded['height'],
    }
    candidate_dimensions = {
        'width': candidate_decoded['width'],
        'height': candidate_decoded['height'],
    }
    dimensions_match = source_dimensions == candidate_dimensions
    pixels_compared = (
        source_decoded['width'] * source_decoded['height']
        if dimensions_match
        else 0
    )
    different_pixels = 0
    max_channel_delta = 0
    total_channel_delta = 0
    alpha_different_pixels = 0
    max_alpha_delta = 0
    if dimensions_match:
        source_rgba = source_decoded['rgba']
        candidate_rgba = candidate_decoded['rgba']
        for offset in range(0, len(source_rgba), 4):
            source_pixel = source_rgba[offset : offset + 4]
            candidate_pixel = candidate_rgba[offset : offset + 4]
            deltas = [
                abs(left - right)
                for left, right in zip(source_pixel, candidate_pixel)
            ]
            if any(deltas):
                different_pixels += 1
            max_channel_delta = max(max_channel_delta, *deltas)
            total_channel_delta += sum(deltas)
            if deltas[3]:
                alpha_different_pixels += 1
                max_alpha_delta = max(max_alpha_delta, deltas[3])
    status = (
        'passed'
        if dimensions_match and different_pixels == 0
        else 'failed'
    )
    denominator = pixels_compared * 4
    return {
        'source_sha256': hashlib.sha256(
            source.read_bytes()
        ).hexdigest(),
        'candidate_sha256': hashlib.sha256(
            candidate.read_bytes()
        ).hexdigest(),
        'tool': TOOL_NAME,
        'tool_version': TOOL_VERSION,
        'decoder': decoder_metadata,
        'status': status,
        'policy': POLICY,
        'metric': 'rgba',
        'source_dimensions': source_dimensions,
        'candidate_dimensions': candidate_dimensions,
        'pixels_compared': pixels_compared,
        'different_pixels': different_pixels,
        'max_channel_delta': max_channel_delta,
        'total_channel_delta': total_channel_delta,
        'mean_channel_delta': (
            round(total_channel_delta / denominator, 6)
            if denominator
            else None
        ),
        'alpha_different_pixels': alpha_different_pixels,
        'max_alpha_delta': max_alpha_delta,
        'alpha': {
            'source': alpha_statistics(
                source_decoded['rgba'],
                source_decoded['width'],
                source_decoded['height'],
            ),
            'candidate': alpha_statistics(
                candidate_decoded['rgba'],
                candidate_decoded['width'],
                candidate_decoded['height'],
            ),
        },
    }


def emit_payload(payload, output):
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    if output is None:
        print(serialized, end='')
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f'.{output.name}.tmp')
    temporary.write_text(serialized)
    temporary.replace(output)


def main():
    args = parse_args()
    try:
        payload = compare_assets(args.source, args.candidate)
    except (OSError, RgbaComparisonError) as exc:
        payload = {
            'status': 'failed',
            'error': {
                'code': 'rgba.decode_failed',
                'message': str(exc),
            },
        }
        emit_payload(payload, args.output)
        return 1
    emit_payload(payload, args.output)
    return 0 if payload['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
