"""Behavioral checks for the offline tool, not tests of instruction wording."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parent
SCRIPT = ROOT / 'scripts/search_book.py'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('search_book', SCRIPT)
book = importlib.util.module_from_spec(spec)
spec.loader.exec_module(book)


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = book.manifest()
        cls.entries = book.all_entries(cls.data)
        cls.by_id = {e['id']: e for e in cls.entries}

    def cli(self, *args):
        return subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), *args],
                              cwd=BUILD, capture_output=True, encoding='utf-8')

    def test_snapshot_integrity(self):
        self.assertTrue(book.check(self.data)['ok'])
        self.assertEqual(len({e['chapter'] for e in self.entries}), 34)

    def test_all_source_boundaries_and_urls(self):
        for e in self.entries:
            with self.subTest(id=e['id']):
                path = book.REF / e['path']
                lines = path.read_text(encoding='utf-8-sig').splitlines()
                self.assertEqual(e['text'], '\n'.join(lines[e['line_start']-1:e['line_end']]).rstrip())
                self.assertIn(f'/blob/{self.data["commit"]}/{e["path"]}', unquote(urlparse(e['url']).path))
                self.assertIn('- 来源：', e['text'])
                self.assertIn('- 备注：', e['text'])

    def test_loan_search(self):
        matches = book.search(book.all_entries(self.data, 8), ['借条', '担保'])
        self.assertEqual(matches[0]['id'], '08:18')
        self.assertIn('第 45 条', matches[0]['text'])

    def test_training_search(self):
        matches = book.search(book.all_entries(self.data, 23), ['培训', '证书'])
        self.assertIn('23:8', [e['id'] for e in matches[:3]])

    def test_housing_search(self):
        matches = book.search(book.all_entries(self.data, 15), ['租房', '押金'])
        self.assertEqual(matches[0]['id'], '15:1')

    def test_condition_not_lost(self):
        e = book.search(self.entries, ['低钠盐'])[0]
        self.assertIn('肾功能', e['text'])
        self.assertIn('备注', e['text'])
        self.assertIn('争议', e['text'])

    def test_full_read_with_preamble_and_unicode_cwd(self):
        result = self.cli('read', '23:8', '08:18')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.by_id['23:8']['text'], result.stdout)
        self.assertIn(self.by_id['08:18']['text'], result.stdout)
        self.assertIn('具体某个工种一个月挣多少，本书不给数字', result.stdout)

    def test_search_does_not_expose_partial_evidence_as_full(self):
        result = self.cli('search', '押金', '--chapter', '15', '--limit', '1')
        data = json.loads(result.stdout)
        self.assertNotIn('text', data['results'][0])
        self.assertTrue(data['results'][0]['url'])

    def test_all_terms_mode(self):
        matches = book.search(self.entries, ['借条', '担保'], True)
        self.assertTrue(matches)
        self.assertTrue(all('借条' in e['text'] and '担保' in e['text'] for e in matches))

    def test_empty_query(self):
        result = self.cli('search', '   ')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('非空关键词', result.stderr)

    def test_no_matches(self):
        result = self.cli('search', 'unlikely_term_9f18bdc47')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['total_matches'], 0)

    def test_invalid_id_and_missing_entry(self):
        for value in ('../../README.md', '99:1', '23:99999'):
            with self.subTest(value=value):
                result = self.cli('read', value)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)

    def test_invalid_chapter_and_limit(self):
        for args in [('search', '培训', '--chapter', '99'), ('search', '培训', '--limit', '0')]:
            result = self.cli(*args)
            self.assertNotEqual(result.returncode, 0)

    def test_tampering_rejected_without_touching_source(self):
        e = self.entries[0]
        changed = dict(self.data)
        changed['files'] = dict(self.data['files'])
        changed['files'][e['path']] = '0'*64
        with self.assertRaisesRegex(ValueError, '校验失败'):
            book.verified_text(book.REF/e['path'], changed)
        self.assertFalse(book.check(changed)['ok'])

    def test_missing_file_report(self):
        changed = dict(self.data)
        changed['files'] = dict(self.data['files'])
        changed['files']['book/not-present.md'] = '0'*64
        result = book.check(changed)
        self.assertFalse(result['ok'])
        self.assertIn('文件缺失', result['errors'][0])

    def test_manifest_path_escape_rejected(self):
        changed = dict(self.data)
        changed['files'] = {'../outside.txt': '0'*64}
        self.assertIn('路径越界', book.check(changed)['errors'][0])

    def test_authored_relative_links(self):
        import re
        for relative in ['SKILL.md', 'references/decision-method.md', 'references/book-index.md', 'references/source-policy.md', 'ATTRIBUTION.md']:
            path = ROOT/relative
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((path.parent/link.split('#')[0]).is_file(), (relative, link))


if __name__ == '__main__':
    unittest.main(verbosity=2)
