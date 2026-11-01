from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import yaml

from tools import package_skillhub
from tools.package_skillhub import package, package_bytes

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skill/deterministic-pixel-art'
COMMIT = 'a' * 40


def source_files(folder):
    return {path.relative_to(folder).as_posix(): path.read_bytes()
            for path in folder.rglob('*') if path.is_file() and '__pycache__' not in path.parts}


class SkillHubPackageTests(unittest.TestCase):
    def test_default_provenance_rejects_files_absent_from_committed_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / 'skill/deterministic-pixel-art'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('committed content\n', encoding='utf-8')
            (root / '.gitignore').write_text('*.ignored\n', encoding='utf-8')
            for args in (['init', '-q'], ['add', '.'],
                         ['-c', 'user.name=Package test', '-c', 'user.email=package-test@example.invalid',
                          'commit', '-qm', 'Test snapshot']):
                subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
            expected = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
            with patch.multiple(package_skillhub, ROOT=root, SKILL=skill):
                self.assertEqual(package_skillhub.current_commit(), expected)
                for name in ('extra.txt', 'extra.ignored'):
                    extra = skill / name
                    extra.write_text('not in the declared source commit', encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'must match HEAD'):
                        package_skillhub.current_commit()
                    extra.unlink()
                (skill / 'SKILL.md').write_text('uncommitted content\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Commit tracked changes'):
                    package_skillhub.current_commit()

    def test_platform_zip_keeps_runtime_and_generic_source_exact(self):
        before = source_files(SKILL)
        data, manifest, version = package_bytes(SKILL, COMMIT)
        self.assertEqual(data, package_bytes(SKILL, COMMIT)[0])
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertIsNone(archive.testzip())
            files = {name: archive.read(name) for name in archive.namelist()}
        self.assertEqual(set(files) - set(before), {'DISTRIBUTION.json'})
        for name in before:
            if name != 'SKILL.md':
                self.assertEqual(files[name], before[name], name)
        generic_front, generic_body = before['SKILL.md'].decode().split('---', 2)[1:]
        hub_front, hub_body = files['SKILL.md'].decode().split('---', 2)[1:]
        self.assertEqual(hub_body, generic_body)
        original, adapted = yaml.safe_load(generic_front), yaml.safe_load(hub_front)
        self.assertTrue(all(adapted[key] == value for key, value in original.items()))
        self.assertEqual(adapted['version'], version)
        self.assertEqual(adapted['slug'], 'deterministic-pixel-art')
        self.assertEqual(json.loads(files['DISTRIBUTION.json'])['source_commit'], COMMIT)
        self.assertEqual(manifest, {name: hashlib.sha256(value).hexdigest() for name, value in files.items()})
        self.assertEqual(source_files(SKILL), before)

    def test_incomplete_authoring_source_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'delivery'
            with self.assertRaisesRegex(ValueError, 'complete generated Skill'):
                package(ROOT / 'skill-content', out, COMMIT)
            self.assertFalse(out.exists())

    def test_previous_delivery_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            marker = out / 'keep.txt'
            marker.write_text('previous delivery', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                package(SKILL, out, COMMIT)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'previous delivery')
            self.assertEqual(list(out.iterdir()), [marker])

    def test_bad_provenance_or_double_adaptation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'full lowercase Git SHA-1'):
            package_bytes(SKILL, 'main')
        with tempfile.TemporaryDirectory() as directory:
            adapted = Path(directory) / 'skill'
            shutil.copytree(SKILL, adapted, ignore=shutil.ignore_patterns('__pycache__'))
            entry = adapted / 'SKILL.md'
            entry.write_text(entry.read_text(encoding='utf-8').replace('---\n', '---\nslug: existing-adapter\n', 1), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'already adapted'):
                package_bytes(adapted, COMMIT)
