from pathlib import Path
import tempfile
import unittest

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
