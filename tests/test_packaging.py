from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import package_skill
from tools.test_skill import nonportable_host_path, validate_local_references
from tools.validate_skill import validate


class PortableCitationTests(unittest.TestCase):
    def test_external_sources_are_not_host_paths(self):
        self.assertFalse(nonportable_host_path('[Forge](https://docs.minecraftforge.net/en/1.20.1/gui/screens/)'))
        self.assertFalse(nonportable_host_path('Use assets/quality/ui-panel.json'))
        for value in ('C:/Users/name/file.png',r'D:\work\scene.json','/home/name/file','/Users/name/file'):
            with self.subTest(value=value):self.assertTrue(nonportable_host_path(value))


class SkillReferenceTests(unittest.TestCase):
    def check_reference(self, target, exists, valid):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / 'test-skill'
            skill.mkdir()
            (skill / 'SKILL.md').write_text(
                '---\nname: test-skill\ndescription: Check local links\n---\n'
                f'# Entry\n[Review]({target})\n', encoding='utf-8')
            if exists:
                (skill / 'references').mkdir()
                (skill / 'references/review.md').write_text('# Interpretation\n', encoding='utf-8')
            for checker, error in ((validate_local_references, RuntimeError), (validate, ValueError)):
                with self.subTest(checker=checker.__name__):
                    if valid:
                        checker(skill)
                    else:
                        with self.assertRaisesRegex(error, 'Broken skill reference'):
                            checker(skill)

    def test_existing_file_accepts_markdown_fragment(self):
        self.check_reference('references/review.md#interpretation', exists=True, valid=True)

    def test_missing_file_with_fragment_is_still_rejected(self):
        self.check_reference('references/missing.md#interpretation', exists=True, valid=False)

    def test_document_fragment_needs_no_separate_file(self):
        self.check_reference('#entry', exists=False, valid=True)

    def test_links_inside_reference_pages(self):
        cases = (
            ('other.md#details', True, True),
            ('missing.md#details', False, False),
            ('#local-section', False, True),
            ('https://example.com/guide#details', False, True),
        )
        for target, exists, valid in cases:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                skill = Path(directory) / 'test-skill'
                references = skill / 'references'
                references.mkdir(parents=True)
                (skill / 'SKILL.md').write_text('[Review](references/review.md)\n', encoding='utf-8')
                (references / 'review.md').write_text(
                    f'# Local section\n[Details]({target})\n', encoding='utf-8')
                if exists:
                    (references / 'other.md').write_text('# Details\n', encoding='utf-8')
                if valid:
                    validate_local_references(skill)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'Broken skill reference'):
                        validate_local_references(skill)


class CleanPackageTests(unittest.TestCase):
    """Small isolated synthetic inputs; gate records are fixtures, not release evidence."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='package space ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        inputs = {
            'skill-content/SKILL.md': b'---\nname: test-skill\ndescription: Test fixture\n---\n',
            'skill-content/references/guide.md': b'Authoritative guide\n',
            'skill-content/agents/openai.yaml': b'interface: {}\n',
            'skill-content/assets/brand/icon.png': b'synthetic icon bytes',
            'requirements.txt': b'Pillow>=10.4,<13\n',
            'LICENSE': b'Synthetic license fixture\n',
            'src/pixel_art.py': b'print("fixture")\n',
            'src/pixelart/__init__.py': b"__version__ = '1.2.2'\n",
            'src/pixelart/helper.py': b'VALUE = 1\n',
            'recipes/sample.py': b'# recipe fixture\n',
            'examples/sample.json': b'{"kind":"fixture"}\n',
            'examples/sample.png': b'synthetic example bytes',
            'docs/quality/review.png': b'synthetic review bytes',
        }
        for name, data in inputs.items():
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.expected = {
            'SKILL.md': inputs['skill-content/SKILL.md'],
            'references/guide.md': inputs['skill-content/references/guide.md'],
            'agents/openai.yaml': inputs['skill-content/agents/openai.yaml'],
            'assets/brand/icon.png': inputs['skill-content/assets/brand/icon.png'],
            'requirements.txt': inputs['requirements.txt'],
            'LICENSE': inputs['LICENSE'],
            'scripts/pixel_art.py': inputs['src/pixel_art.py'],
            'scripts/pixelart/__init__.py': inputs['src/pixelart/__init__.py'],
            'scripts/pixelart/helper.py': inputs['src/pixelart/helper.py'],
            'scripts/recipes/sample.py': inputs['recipes/sample.py'],
            'assets/sample.json': inputs['examples/sample.json'],
            'assets/sample.png': inputs['examples/sample.png'],
            'assets/studies/review.png': inputs['docs/quality/review.png'],
        }
        (self.root/'evaluation').mkdir()
        self.refresh_gate()
        self.skill = self.root/'skill/deterministic-pixel-art'
        self.archive = self.root/'deterministic-pixel-art.zip'
        self.manifest = self.root/'evaluation/package-manifest.json'

    def refresh_gate(self):
        runtime = {path.relative_to(self.root/'src').as_posix():
                   hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted((self.root/'src').rglob('*.py'))}
        (self.root/'evaluation/metrics.json').write_text(json.dumps(dict(
            quality_gate_passed=True, fixtures_unchanged=True, runtime_sha256=runtime)))
        (self.root/'evaluation/quality-results.json').write_text(json.dumps(dict(
            agent_review_passed=True, stable_outputs_unchanged=43, cases=[])))

    def build(self):
        output = io.StringIO()
        with patch.object(package_skill, 'ROOT', self.root), redirect_stdout(output):
            package_skill.main()
        return json.loads(output.getvalue())

    def tree(self, folder):
        return {path.relative_to(folder).as_posix(): path.read_bytes()
                for path in folder.rglob('*') if path.is_file()}

    def outputs(self):
        return dict(skill=self.tree(self.skill),
                    archive=self.archive.read_bytes(), manifest=self.manifest.read_bytes())

    def sources(self):
        return {name: self.tree(self.root/name)
                for name in ('src', 'recipes', 'skill-content', 'examples', 'docs')}

    def assert_package(self, expected):
        self.assertEqual(self.tree(self.skill), expected)
        with zipfile.ZipFile(self.archive) as bundle:
            self.assertIsNone(bundle.testzip())
            files = {name.removeprefix('deterministic-pixel-art/'): bundle.read(name)
                     for name in bundle.namelist()}
        self.assertEqual(files, expected)
        self.assertEqual(json.loads(self.manifest.read_text()),
                         {name: hashlib.sha256(data).hexdigest()
                          for name, data in expected.items()})

    def test_removed_and_renamed_inputs_leave_no_residue(self):
        self.build()
        (self.root/'skill-content/references/guide.md').rename(
            self.root/'skill-content/references/renamed.md')
        (self.root/'src/pixelart/helper.py').unlink()
        self.refresh_gate()
        expected = dict(self.expected)
        expected['references/renamed.md'] = expected.pop('references/guide.md')
        del expected['scripts/pixelart/helper.py']
        before = self.sources()
        self.build()
        self.assert_package(expected)
        self.assertEqual(self.sources(), before)

    def test_dirty_generated_tree_matches_clean_build_and_retains_previous(self):
        self.build()
        clean = self.outputs()
        for name in ('AGENTS.md', '.private', 'references/old.md',
                     'scripts/pixelart/retired.py', 'scripts/pixelart/__pycache__/old.pyc'):
            path = self.skill/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'Previous hand-edited or obsolete generated file')
        previous = self.outputs()
        before = self.sources()
        result = self.build()
        self.assert_package(self.expected)
        self.assertEqual(self.outputs(), clean)
        backups = {Path(item['path']): Path(item['backup'])
                   for item in result['previous_outputs']}
        self.assertEqual(self.tree(backups[self.skill.resolve()]), previous['skill'])
        self.assertEqual(self.sources(), before)

    def assert_work_files_cleaned(self):
        self.assertFalse(list((self.root/'evaluation').glob('package-stage-*')))
        self.assertFalse((self.root/'evaluation/.package_skill.lock').exists())

    def change_guide(self):
        (self.root/'skill-content/references/guide.md').write_bytes(b'Updated authoritative guide\n')
        return self.sources()

    def test_unchanged_build_is_reproducible_without_extra_backups(self):
        self.build()
        before = self.outputs()
        result = self.build()
        self.assertEqual(self.outputs(), before)
        self.assertEqual(result['previous_outputs'], [])
        self.assert_work_files_cleaned()

    def test_private_inputs_are_excluded_without_deleting_them(self):
        for name in ('AGENTS.md', 'skill-content/AGENTS.md', 'skill-content/references/AGENTS.md',
                     'skill-content/.private/note.md', 'skill-content/references/__pycache__/note.pyc'):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'Private fixture; retain outside delivery')
        before = self.sources()
        self.build()
        self.assert_package(self.expected)
        self.assertEqual(self.sources(), before)

    def test_copy_failure_preserves_sources_and_previous_delivery(self):
        self.build()
        previous = self.outputs()
        before = self.change_guide()
        copyfile = shutil.copyfile

        def fail_copy(source, target):
            if Path(source).name == 'guide.md':
                raise OSError('injected copy failure')
            return copyfile(source, target)

        with patch('tools.package_skill.shutil.copyfile', side_effect=fail_copy):
            with self.assertRaisesRegex(OSError, 'injected copy failure'):
                self.build()
        self.assertEqual(self.outputs(), previous)
        self.assertEqual(self.sources(), before)
        self.assert_work_files_cleaned()

    def test_archive_failure_preserves_sources_and_previous_delivery(self):
        self.build()
        previous = self.outputs()
        before = self.change_guide()
        with patch('tools.package_skill.zipfile.ZipFile.writestr', side_effect=OSError('injected ZIP failure')):
            with self.assertRaisesRegex(OSError, 'injected ZIP failure'):
                self.build()
        self.assertEqual(self.outputs(), previous)
        self.assertEqual(self.sources(), before)
        self.assert_work_files_cleaned()

    def test_publication_failure_restores_all_previous_outputs(self):
        self.build()
        previous = self.outputs()
        before = self.change_guide()
        replace = os.replace

        def fail_archive(source, target):
            if Path(source).name == 'package.zip' and Path(target) == self.archive.resolve():
                raise OSError('injected publication failure')
            return replace(source, target)

        with patch('tools.package_skill.os.replace', side_effect=fail_archive):
            with self.assertRaisesRegex(RuntimeError, 'Package publication failed') as raised:
                self.build()
        detail = json.loads(str(raised.exception).split(': ', 1)[1])
        self.assertEqual(detail['rollback_errors'], [])
        self.assertEqual(detail['recovery_backups'], [])
        self.assertEqual(self.outputs(), previous)
        self.assertEqual(self.sources(), before)
        self.assert_work_files_cleaned()

    def test_restore_failure_retains_and_identifies_previous_skill(self):
        self.build()
        previous = self.outputs()
        before = self.change_guide()
        replace = os.replace

        def fail_publish_and_restore(source, target):
            source, target = Path(source), Path(target)
            if source.name == 'package.zip' and target == self.archive.resolve():
                raise OSError('injected publication failure')
            if target == self.skill.resolve() and source.parent.parent.name.startswith('package-backup-'):
                raise OSError('injected recovery failure')
            return replace(source, target)

        with patch('tools.package_skill.os.replace', side_effect=fail_publish_and_restore):
            with self.assertRaisesRegex(RuntimeError, 'Package publication failed') as raised:
                self.build()
        detail = json.loads(str(raised.exception).split(': ', 1)[1])
        self.assertEqual(len(detail['recovery_backups']), 1)
        recovery = detail['recovery_backups'][0]
        self.assertEqual(Path(recovery['path']), self.skill.resolve())
        self.assertEqual(self.tree(Path(recovery['backup'])), previous['skill'])
        self.assertFalse(self.skill.exists())
        self.assertEqual(self.archive.read_bytes(), previous['archive'])
        self.assertEqual(self.manifest.read_bytes(), previous['manifest'])
        self.assertEqual(self.sources(), before)
        self.assert_work_files_cleaned()

    def test_external_generated_edit_is_preserved_with_its_old_backup(self):
        self.build()
        previous = self.outputs()
        before = self.change_guide()
        replace = os.replace

        def change_generated_then_fail(source, target):
            if Path(source).name == 'package.zip' and Path(target) == self.archive.resolve():
                (self.skill/'references/guide.md').write_bytes(b'External generated edit')
                raise OSError('injected publication failure')
            return replace(source, target)

        with patch('tools.package_skill.os.replace', side_effect=change_generated_then_fail):
            with self.assertRaisesRegex(RuntimeError, 'Package publication failed') as raised:
                self.build()
        detail = json.loads(str(raised.exception).split(': ', 1)[1])
        self.assertEqual((self.skill/'references/guide.md').read_bytes(), b'External generated edit')
        self.assertEqual(self.tree(Path(detail['recovery_backups'][0]['backup'])), previous['skill'])
        self.assertEqual(self.sources(), before)
        self.assert_work_files_cleaned()

    def test_source_changes_during_build_abort_before_publication(self):
        self.build()
        previous = self.outputs()
        write = zipfile.ZipFile.writestr
        changed = False

        def change_source(bundle, *args, **kwargs):
            nonlocal changed
            if not changed:
                (self.root/'skill-content/references/guide.md').write_bytes(b'Concurrent source edit')
                changed = True
            return write(bundle, *args, **kwargs)

        with patch('tools.package_skill.zipfile.ZipFile.writestr', new=change_source):
            with self.assertRaisesRegex(RuntimeError, 'inputs changed during the build'):
                self.build()
        self.assertEqual(self.outputs(), previous)
        self.assertEqual((self.root/'skill-content/references/guide.md').read_bytes(), b'Concurrent source edit')
        self.assert_work_files_cleaned()

    def test_runtime_changed_after_initial_gate_is_not_published(self):
        self.build()
        previous = self.outputs()
        sources = package_skill._sources
        changed = False

        def change_runtime(root):
            nonlocal changed
            if not changed:
                (self.root/'src/pixelart/helper.py').write_bytes(b'VALUE = 2\n')
                changed = True
            return sources(root)

        with patch('tools.package_skill._sources', side_effect=change_runtime):
            with self.assertRaisesRegex(RuntimeError, 'Runtime changed since evaluation'):
                self.build()
        self.assertEqual(self.outputs(), previous)
        self.assert_work_files_cleaned()

    def test_missing_required_input_and_colliding_input_preserve_delivery(self):
        self.build()
        previous = self.outputs()
        entry = self.root/'skill-content/SKILL.md'
        original = entry.read_bytes()
        entry.unlink()
        with self.assertRaisesRegex(RuntimeError, 'Missing required package inputs'):
            self.build()
        self.assertEqual(self.outputs(), previous)
        entry.write_bytes(original)
        duplicate = self.root/'examples/studies/review.png'
        duplicate.parent.mkdir()
        duplicate.write_bytes(b'Conflicting source fixture')
        with self.assertRaisesRegex(RuntimeError, 'inputs collide'):
            self.build()
        self.assertEqual(self.outputs(), previous)
        self.assert_work_files_cleaned()

    def test_quality_gate_and_another_packager_prevent_writes(self):
        self.build()
        previous = self.outputs()
        metrics = self.root/'evaluation/metrics.json'
        data = json.loads(metrics.read_text())
        data['quality_gate_passed'] = False
        metrics.write_text(json.dumps(data))
        with self.assertRaisesRegex(RuntimeError, 'passing quality gate'):
            self.build()
        self.assertEqual(self.outputs(), previous)
        self.refresh_gate()
        lock = self.root/'evaluation/.package_skill.lock'
        lock.write_bytes(b'Another active packager fixture')
        with self.assertRaisesRegex(RuntimeError, 'Another packager holds'):
            self.build()
        self.assertEqual(lock.read_bytes(), b'Another active packager fixture')
        self.assertEqual(self.outputs(), previous)
