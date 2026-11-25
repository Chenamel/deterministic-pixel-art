from pathlib import Path
import tempfile
import unittest

from tools.self_check import compare_readmes, references, resolve_reference, skill_reference_graph


class DocumentAuditTests(unittest.TestCase):
    def test_distribution_asset_link_resolves_in_mirrored_reference_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'skill-content/references/pixel-art.md'
            source.parent.mkdir(parents=True)
            source.write_text('[Study](../assets/studies/art.png)', encoding='utf-8')
            asset = root / 'skill/deterministic-pixel-art/assets/studies/art.png'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b'fixture')
            result = resolve_reference(root, source, '../assets/studies/art.png', 'markdown')
            self.assertEqual(result['status'], 'exists')
            self.assertEqual(result['resolved'], 'skill/deterministic-pixel-art/assets/studies/art.png')

    def test_missing_explicit_link_stays_broken_even_for_familiar_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = resolve_reference(root, root / 'docs/entry.md', 'missing.md#details', 'markdown')
            self.assertEqual(result['status'], 'broken')
            self.assertFalse(result['exists'])

    def test_absolute_url_is_not_reinterpreted_as_relative_file(self):
        values = list(references('Fetch https://example.com/path/file.zip then read `inputs/icon.json`.'))
        self.assertEqual([r[1] for r in values], ['inputs/icon.json'])

    def test_bilingual_structure_detects_missing_command_and_table_row(self):
        with tempfile.TemporaryDirectory() as temporary:
            left, right = [Path(temporary) / name for name in ('en.md', 'cn.md')]
            left.write_text('# App\n## Start\n```sh\npython render.py\n```\n| A |\n|---|\n| x |\n| y |\n', encoding='utf-8')
            right.write_text('# 应用\n## 开始\n```sh\npython inspect.py\n```\n| A |\n|---|\n| x |\n', encoding='utf-8')
            result = compare_readmes(left, right)
            self.assertFalse(result['structural_matches'])
            self.assertFalse(result['sections'][1]['code_matches'])
            self.assertEqual(result['sections'][1]['english']['tables'], [2])
            self.assertEqual(result['sections'][1]['chinese']['tables'], [1])

    def test_graph_reports_orphan_and_missing_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'references').mkdir()
            (root / 'SKILL.md').write_text('[A](references/a.md) [Missing](references/missing.md)', encoding='utf-8')
            (root / 'references/a.md').write_text('[B](b.md#example)', encoding='utf-8')
            (root / 'references/b.md').write_text('# Example', encoding='utf-8')
            (root / 'references/orphan.md').write_text('# Unused', encoding='utf-8')
            result = skill_reference_graph(root)
            self.assertEqual(result['missing'], ['references/missing.md'])
            self.assertEqual(result['unreachable'], ['references/orphan.md'])
            self.assertIn('references/b.md', result['not_directly_referenced'])

    def test_historical_lt06_archive_citation_is_not_marked_broken(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'docs/self-check-logo-assets-20261031.md'
            result = resolve_reference(root, source, 'src/gen_chest.py', 'file-reference')
            self.assertEqual(result['status'], 'absent-generated-or-local-evidence')
            self.assertFalse(result['exists'])

    def test_other_missing_src_paths_and_markdown_links_stay_broken(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'docs/lt06-results-20261030.zh-CN.md'
            md_link = resolve_reference(root, archive, 'src/gen_chest.py', 'markdown')
            self.assertEqual(md_link['status'], 'broken')
            other_src = resolve_reference(root, archive, 'src/missing_helper.py', 'file-reference')
            self.assertEqual(other_src['status'], 'broken')
