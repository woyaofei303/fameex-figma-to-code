import binascii
import base64
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import compare_assets_rgba
from compare_assets_rgba import (
    RgbaComparisonError,
    compare_assets,
)


def png_chunk(kind, payload):
    return (
        struct.pack('>I', len(payload))
        + kind
        + payload
        + struct.pack('>I', binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path, width, height, pixels, padding=0):
    rows = []
    for y in range(height):
        row = b''.join(
            bytes(pixels[(y * width) + x])
            for x in range(width)
        )
        rows.append(b'\x00' + row)
    payload = (
        b'\x89PNG\r\n\x1a\n'
        + png_chunk(
            b'IHDR',
            struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0),
        )
    )
    if padding:
        payload += png_chunk(b'tEXt', b'padding\x00' + (b'x' * padding))
    payload += png_chunk(b'IDAT', zlib.compress(b''.join(rows)))
    payload += png_chunk(b'IEND', b'')
    path.write_bytes(payload)


class CompareAssetsRgbaTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.asset_dir = Path(self.temp_dir.name)

    def write_png(self, name, pixels, width=2, height=2):
        path = self.asset_dir / name
        write_rgba_png(path, width, height, pixels)
        return path

    def test_identical_decoded_pixels_pass_lossless_exact_policy(self):
        pixels = [(32, 64, 96, 255)] * 4
        source = self.write_png('source.png', pixels)
        candidate = self.write_png('candidate.png', pixels)

        result = compare_assets(source, candidate)

        self.assertEqual('passed', result['status'])
        self.assertEqual('lossless-exact', result['policy'])
        self.assertEqual(4, result['pixels_compared'])
        self.assertEqual(0, result['different_pixels'])
        self.assertEqual(0, result['max_channel_delta'])
        self.assertEqual(0, result['alpha_different_pixels'])
        self.assertEqual('opaque', result['alpha']['source']['mode'])
        self.assertEqual('opaque', result['alpha']['candidate']['mode'])

    def test_one_rgb_pixel_difference_fails(self):
        source = self.write_png(
            'source.png',
            [(32, 64, 96, 255)] * 4,
        )
        candidate_pixels = [(32, 64, 96, 255)] * 4
        candidate_pixels[2] = (33, 64, 96, 255)
        candidate = self.write_png('candidate.png', candidate_pixels)

        result = compare_assets(source, candidate)

        self.assertEqual('failed', result['status'])
        self.assertEqual(1, result['different_pixels'])
        self.assertEqual(1, result['max_channel_delta'])
        self.assertEqual(0, result['alpha_different_pixels'])

    def test_one_alpha_pixel_difference_fails(self):
        source = self.write_png(
            'source.png',
            [(32, 64, 96, 255)] * 4,
        )
        candidate_pixels = [(32, 64, 96, 255)] * 4
        candidate_pixels[1] = (32, 64, 96, 128)
        candidate = self.write_png('candidate.png', candidate_pixels)

        result = compare_assets(source, candidate)

        self.assertEqual('failed', result['status'])
        self.assertEqual(1, result['different_pixels'])
        self.assertEqual(1, result['alpha_different_pixels'])
        self.assertEqual(127, result['max_alpha_delta'])
        self.assertEqual(
            'transparent',
            result['alpha']['candidate']['mode'],
        )

    def test_transparency_is_derived_from_decoded_alpha_pixels(self):
        pixels = [
            (10, 20, 30, 255),
            (10, 20, 30, 128),
            (10, 20, 30, 0),
            (10, 20, 30, 255),
        ]
        source = self.write_png('source.png', pixels)

        result = compare_assets(source, source)

        alpha = result['alpha']['source']
        self.assertEqual('transparent', alpha['mode'])
        self.assertEqual(2, alpha['transparent_pixels'])
        self.assertEqual(1, alpha['partial_alpha_pixels'])
        self.assertEqual(
            {'x': 0, 'y': 0, 'width': 2, 'height': 2},
            alpha['bounds'],
        )

    def test_large_transparent_image_uses_bounded_statistics(self):
        width = 1024
        height = 1024
        rgba = b'\x00\x00\x00\x00' * (width * height)

        alpha = compare_assets_rgba.alpha_statistics(
            rgba,
            width,
            height,
        )

        self.assertEqual(width * height, alpha['transparent_pixels'])
        self.assertEqual(0, alpha['partial_alpha_pixels'])
        self.assertEqual(
            {'x': 0, 'y': 0, 'width': width, 'height': height},
            alpha['bounds'],
        )

    def test_malformed_header_only_assets_cannot_be_compared(self):
        source = self.asset_dir / 'source.png'
        source.write_bytes(b'\x89PNG\r\n\x1a\n')
        candidate = self.asset_dir / 'candidate.webp'
        candidate.write_bytes(b'RIFF\x00\x00\x00\x00WEBP')

        with self.assertRaises(RgbaComparisonError):
            compare_assets(source, candidate)

    def test_missing_decoder_fails_closed(self):
        source = self.write_png(
            'source.png',
            [(32, 64, 96, 255)] * 4,
        )
        candidate = self.asset_dir / 'candidate.webp'
        candidate.write_bytes(b'not-a-webp')

        with (
            mock.patch.object(compare_assets_rgba, 'PIL_IMAGE', None),
            mock.patch.object(
                compare_assets_rgba,
                'SIPS_PATH',
                Path('/missing/sips'),
            ),
        ):
            with self.assertRaisesRegex(
                RgbaComparisonError,
                'No RGBA decoder',
            ):
                compare_assets(source, candidate)

    @unittest.skipUnless(
        shutil.which('sips'),
        'macOS sips is required for the WebP integration fixture',
    )
    def test_real_webp_is_decoded_before_comparison(self):
        candidate = self.asset_dir / 'candidate.webp'
        candidate.write_bytes(
            base64.b64decode(
                'UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEAAUAm'
                'JaQAA3AA/vuUAAA='
            )
        )
        source = self.asset_dir / 'source.png'
        subprocess.run(
            [
                '/usr/bin/sips',
                '-s',
                'format',
                'png',
                str(candidate),
                '--out',
                str(source),
            ],
            check=True,
            capture_output=True,
        )

        result = compare_assets(source, candidate)

        self.assertEqual('passed', result['status'], result)
        self.assertIn(result['decoder']['name'], {'pillow', 'sips'})
        self.assertEqual(0, result['different_pixels'])

    @unittest.skipUnless(
        shutil.which('sips'),
        'macOS sips is required for the decoder fallback fixture',
    )
    def test_pillow_decode_failure_falls_back_to_sips(self):
        candidate = self.asset_dir / 'candidate.webp'
        candidate.write_bytes(
            base64.b64decode(
                'UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEAAUAm'
                'JaQAA3AA/vuUAAA='
            )
        )
        source = self.asset_dir / 'source.png'
        subprocess.run(
            [
                '/usr/bin/sips',
                '-s',
                'format',
                'png',
                str(candidate),
                '--out',
                str(source),
            ],
            check=True,
            capture_output=True,
        )

        with (
            mock.patch.object(compare_assets_rgba, 'PIL_IMAGE', object()),
            mock.patch.object(
                compare_assets_rgba,
                'PIL',
                type('PillowFixture', (), {'__version__': 'no-webp'})(),
            ),
            mock.patch.object(
                compare_assets_rgba,
                'decode_with_pillow',
                side_effect=RgbaComparisonError(
                    'Pillow WebP decoder unavailable'
                ),
            ),
        ):
            result = compare_assets(source, candidate)

        self.assertEqual('passed', result['status'], result)
        self.assertEqual('sips', result['decoder']['name'])


if __name__ == '__main__':
    unittest.main()
