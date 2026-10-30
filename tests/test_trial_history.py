"""Audit actual before/after mutation boundaries without retroactive trial rules."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_trial_history import analyze_history, audit

A = hashlib.sha256(b'old').hexdigest()
B = hashlib.sha256(b'new').hexdigest()


class TrialHistoryTests(unittest.TestCase):
    def test_detects_delete_recreate_and_source_edits_between_commands(self):
        records = [
            dict(outputs_before={}, outputs_after={'v1/a.png': A, 'author.py': A}),
            dict(outputs_before={'author.py': B}, outputs_after={'v1/a.png': B, 'author.py': B}),
        ]
        result = analyze_history(records, {'v1/a.png': B, 'author.py': B})
        self.assertEqual(result['mutations'], 2)
        self.assertEqual(result['removed_paths'], ['v1/a.png'])
        self.assertEqual(result['replaced_paths'], ['author.py'])
        self.assertTrue(all(e['phase'] == 'between_commands' and e['record'] == 2 for e in result['events']))

    def test_in_command_and_final_mutations_distinguished_from_new_candidates(self):
        records = [dict(outputs_before={'v1/a.png': A},
                        outputs_after={'v1/a.png': B, 'v2/a.png': A})]
        result = analyze_history(records, {'v1/a.png': B, 'feedback.md': A})
        self.assertEqual([(e['phase'], e['path']) for e in result['events']],
                         [('within_command', 'v1/a.png'), ('after_last_command', 'v2/a.png')])
        preserved = analyze_history([dict(outputs_before={'v1/a.png': A},
                                         outputs_after={'v1/a.png': A, 'v2/a.png': B})])
        self.assertEqual(preserved['mutations'], 0)

    def test_bad_snapshots_are_explicit_errors(self):
        for snapshot in (None, {'../asset.png': A}, {'C:/a.png': A}, {'a\\b.png': A},
                         {'a.png': 'not-a-digest'}):
            with self.subTest(snapshot=snapshot), self.assertRaises(ValueError):
                analyze_history([dict(outputs_before=snapshot, outputs_after={})])

    def test_disk_audit_preserves_files_and_ignores_recorder_outputs(self):
        with tempfile.TemporaryDirectory(prefix='history 中文 space ') as temporary:
            root = Path(temporary)
            (root / 'v1').mkdir()
            (root / 'v1/a.png').write_bytes(b'new')
            log = root / 'commands.jsonl'
            log.write_text(json.dumps(dict(outputs_before={}, outputs_after={'v1/a.png': A})) + '\n', encoding='utf-8')
            (root / 'checks.json').write_text('{}', encoding='utf-8')
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result = audit(root)
            self.assertEqual(result['events'][0]['phase'], 'after_last_command')
            self.assertEqual(result['events'][0]['after'], B)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
