import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/audit_assets.py'


class AuditAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.asset_dir = Path(self.temp_dir.name)

    def run_audit(self, *paths):
        command = ['/usr/bin/python3', str(SCRIPT)]
        for path in paths:
            command.extend(['--asset', str(path)])
        command.append('--json')
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_png_svg_and_webp_metadata_are_reported_without_conversion(self):
        png = self.asset_dir / 'alpha.png'
        png.write_bytes(
            b'\x89PNG\r\n\x1a\n'
            + struct.pack('>I', 13)
            + b'IHDR'
            + struct.pack('>IIBBBBB', 326, 260, 8, 6, 0, 0, 0)
            + b'\x00\x00\x00\x00'
        )
        svg = self.asset_dir / 'icon.svg'
        svg.write_text(
            '<svg width="32" height="32" viewBox="0 0 32 32" '
            'xmlns="http://www.w3.org/2000/svg"></svg>'
        )
        webp = self.asset_dir / 'hero.webp'
        vp8x = (
            bytes([0x10, 0, 0, 0])
            + (598).to_bytes(3, 'little')
            + (399).to_bytes(3, 'little')
        )
        webp.write_bytes(
            b'RIFF'
            + struct.pack('<I', 4 + 8 + len(vp8x))
            + b'WEBP'
            + b'VP8X'
            + struct.pack('<I', len(vp8x))
            + vp8x
        )

        result = self.run_audit(png, svg, webp)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        by_format = {item['format']: item for item in payload['assets']}
        self.assertEqual(
            {'width': 326, 'height': 260},
            by_format['png']['intrinsic_dimensions'],
        )
        self.assertTrue(by_format['png']['alpha_encoding_signaled'])
        self.assertNotIn('alpha_capable', by_format['png'])
        self.assertEqual('0 0 32 32', by_format['svg']['view_box'])
        self.assertEqual(
            {'width': 599, 'height': 400},
            by_format['webp']['intrinsic_dimensions'],
        )
        self.assertTrue(by_format['webp']['alpha_encoding_signaled'])
        self.assertNotIn('alpha_capable', by_format['webp'])
        for item in payload['assets']:
            self.assertEqual(64, len(item['sha256']))
            self.assertGreater(item['bytes'], 0)
            self.assertFalse(item['pixel_rgba_verified'])
            self.assertEqual('unverified', item['conversion_decision'])

    def test_missing_assets_fail_with_a_machine_readable_error(self):
        result = self.run_audit(self.asset_dir / 'missing.png')

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual('asset.not_found', payload['errors'][0]['code'])


if __name__ == '__main__':
    unittest.main()
