import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/search_codex_history.py'


class SearchCodexHistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.history_root = Path(self.temp_dir.name)

    def write_session(self, name, timestamp, messages):
        path = self.history_root / f'{name}.jsonl'
        rows = [
            {
                'timestamp': timestamp,
                'type': 'session_meta',
                'payload': {'id': name},
            },
        ]
        rows.extend(
            {
                'timestamp': message_timestamp,
                'type': 'response_item',
                'payload': {
                    'type': 'message',
                    'role': 'user',
                    'content': [
                        {'type': 'input_text', 'text': text},
                    ],
                },
            }
            for message_timestamp, text in messages
        )
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
        return path

    def run_search(self, *args):
        return subprocess.run(
            [
                '/usr/bin/python3',
                str(SCRIPT),
                '--root',
                str(self.history_root),
                '--json',
                *args,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_search_returns_only_bounded_direct_user_messages(self):
        real_message = (
            'PR-02107 的 /contract-carnival 排名列需要均匀分布，'
            '并重新验证 H5。' + ('视觉反馈。' * 100)
        )
        self.write_session(
            'current',
            '2026-07-18T10:00:00Z',
            [
                (
                    '2026-07-18T10:01:00Z',
                    '# AGENTS.md instructions for /tmp\n'
                    'PR-02107 /contract-carnival',
                ),
                (
                    '2026-07-18T10:02:00Z',
                    '<environment_context>PR-02107 /contract-carnival',
                ),
                ('2026-07-18T10:03:00Z', real_message),
            ],
        )
        self.write_session(
            'duplicate',
            '2026-07-18T11:00:00Z',
            [('2026-07-18T10:03:00Z', real_message)],
        )
        self.write_session(
            'old',
            '2026-05-01T10:00:00Z',
            [
                (
                    '2026-05-01T10:01:00Z',
                    'PR-02107 的 /contract-carnival 旧反馈',
                ),
            ],
        )

        result = self.run_search(
            '--ticket',
            'PR-02107',
            '--route',
            '/contract-carnival',
            '--since',
            '2026-06-01',
            '--limit',
            '50',
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(1, len(payload['matches']))
        match = payload['matches'][0]
        self.assertIn('排名列需要均匀分布', match['excerpt'])
        self.assertNotIn('AGENTS.md', match['excerpt'])
        self.assertLessEqual(len(match['excerpt']), 280)
        self.assertEqual(
            {'ticket': 'PR-02107', 'route': '/contract-carnival'},
            match['matched'],
        )

    def test_limit_is_enforced_without_writing_an_output_file(self):
        self.write_session(
            'bounded',
            '2026-07-18T10:00:00Z',
            [
                (
                    f'2026-07-18T10:0{index}:00Z',
                    f'PR-02107 message {index}',
                )
                for index in range(1, 4)
            ],
        )
        before = sorted(self.history_root.rglob('*'))

        result = self.run_search('--ticket', 'PR-02107', '--limit', '2')

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(2, len(payload['matches']))
        self.assertEqual(before, sorted(self.history_root.rglob('*')))

    def test_missing_timestamps_sort_after_dated_matches_without_crashing(self):
        self.write_session(
            'mixed-timestamps',
            '2026-07-18T10:00:00Z',
            [
                (None, 'PR-02107 message without timestamp'),
                (
                    '2026-07-18T10:01:00Z',
                    'PR-02107 message with timestamp',
                ),
            ],
        )

        result = self.run_search('--ticket', 'PR-02107', '--limit', '2')

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [
                '2026-07-18T10:01:00Z',
                None,
            ],
            [match['timestamp'] for match in payload['matches']],
        )


if __name__ == '__main__':
    unittest.main()
