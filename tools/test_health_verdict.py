# Cases: pass with G4, fail, missing H11 or translation ids, unchecked ids,
# pointers, invalid records.
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class HealthVerdictTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='Acme')
        self.addCleanup(self.tree.cleanup)
        self.record = Path(self.tree.name) / 'shop.json'
        self.script = Path(__file__).with_name('health_verdict.py')
        self.entries = [dict(id=name, mode='health', tool_result='clean',
                             reading_result='clean', word='none', reason='Acme')
                        for name in [f'H{n}' for n in range(1, 12)] +
                                    [f'T{n}' for n in range(1, 9)] + ['G4']]

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def evaluate(self, required=None):
        self.record.write_text(json.dumps({'required_ids': required or [],
                                          'entries': self.entries}), encoding='utf-8')
        return self.run_cli('--record', self.record)

    def document(self, required=None):
        run = self.evaluate(required)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertEqual(len(run.stdout.splitlines()), 1)
        document = json.loads(run.stdout)
        self.assertIn(document['result'], ('finding', 'clean', 'not checked', 'does not apply'))
        self.assertTrue(document['reason'])
        return document

    def assert_bad(self, run, name):
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(run.stdout, '')
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        self.assertIn(name, run.stderr)

    def test_acme_findings_leads_and_none_pass(self):
        for index, word in enumerate(('finding', 'lead', 'none')):
            self.entries[index].update(word=word, tool_result='finding',
                                       reading_result='does not apply')
        document = self.document()
        self.assertEqual(document['verdict'], 'pass')
        self.assertEqual((document['missing'], document['reasons'], document['pointers']),
                         ([], [], 0))

    def test_t5_to_t8_and_g4_must_fix_are_refused(self):
        for name in ('T5', 'T6', 'T7', 'T8', 'G4'):
            with self.subTest(name=name):
                entry = dict(id=name, mode='health', kind='check', word='must fix',
                             tool_result='finding', reading_result='clean')
                original = self.entries
                self.entries = [row for row in original if row['id'] != name] + [entry]
                self.assert_bad(self.evaluate(), name)
                self.entries = original

    def test_missing_g4_makes_complete_health_record_incomplete(self):
        self.entries = [entry for entry in self.entries if entry['id'] != 'G4']
        document = self.document()
        self.assertEqual(document['verdict'], 'incomplete')
        self.assertEqual(document['missing'], ['G4'])

    def test_g4_none_or_finding_completes_health_record(self):
        self.entries = [entry for entry in self.entries if entry['id'] != 'G4']
        g4 = dict(id='G4', mode='health', word='none',
                  tool_result='clean', reading_result='clean')
        self.entries.append(g4)
        for word in ('none', 'finding'):
            with self.subTest(word=word):
                g4.update(word=word, tool_result='finding' if word == 'finding' else 'clean')
                document = self.document(['G4'])
                self.assertEqual(document['verdict'], 'pass')
                self.assertEqual(document['missing'], [])

    def test_acme_missing_default_and_added_ids_are_incomplete(self):
        self.entries = [entry for entry in self.entries if entry['id'] != 'H10']
        self.entries[0]['mode'] = 'Acme'
        document = self.document(['Card'])
        self.assertEqual(document['verdict'], 'incomplete')
        self.assertEqual(document['missing'], ['H1', 'H10', 'Card'])

    def test_acme_missing_h11_or_translation_is_incomplete(self):
        complete = self.entries
        for missing in ('H11', 'T1', 'T3', 'T8'):
            with self.subTest(missing=missing):
                self.entries = [entry for entry in complete if entry['id'] != missing]
                document = self.document()
                self.assertEqual(document['verdict'], 'incomplete')
                self.assertEqual(document['missing'], [missing])

    def test_acme_unchecked_tool_or_reading_is_incomplete(self):
        for field in ('tool_result', 'reading_result'):
            with self.subTest(field=field):
                self.entries[0][field] = 'not checked'
                document = self.document()
                self.assertEqual(document['verdict'], 'incomplete')
                self.assertTrue(any('H1' in reason for reason in document['reasons']))
                self.entries[0][field] = 'clean'

    def test_acme_must_fix_fails_and_retains_other_reasons(self):
        self.entries[0]['word'] = 'must fix'
        self.entries[1]['reading_result'] = 'not checked'
        self.entries = [entry for entry in self.entries if entry['id'] != 'H10']
        document = self.document()
        self.assertEqual(document['verdict'], 'fail')
        self.assertEqual(document['missing'], ['H10'])
        for name in ('H1', 'H2'):
            self.assertTrue(any(name in reason for reason in document['reasons']))

    def test_acme_pointer_unchecked_does_not_change_verdict(self):
        self.entries.append(dict(id='Card', mode='health', kind='pointer', word='lead',
                                 tool_result='not checked', reading_result='not checked'))
        self.entries.append(dict(id='shop', mode='Acme', word='must fix'))
        document = self.document()
        self.assertEqual((document['verdict'], document['pointers']), ('pass', 1))

    def test_acme_translation_and_pointer_must_fix_are_invalid(self):
        for changes in [dict(id=f'T{n}') for n in range(1, 5)] + [dict(kind='pointer')]:
            with self.subTest(changes=changes):
                entry = dict(self.entries[0], **changes)
                entry['word'] = 'must fix'
                original = self.entries[0]
                self.entries[0] = entry
                self.assert_bad(self.evaluate(), entry['id'])
                self.entries[0] = original

    def test_acme_invalid_words_results_and_missing_fields_name_id(self):
        for field in ('word', 'tool_result', 'reading_result'):
            for invalid in ('Acme', None, []):
                with self.subTest(field=field, invalid=invalid):
                    original = self.entries[0][field]
                    self.entries[0][field] = invalid
                    self.assert_bad(self.evaluate(), 'H1')
                    self.entries[0][field] = original

    def test_acme_bad_record_and_arguments_have_1_error_line(self):
        for raw in ('Acme', '[]', '{}', '{"entries":[null]}',
                    '{"entries":[],"required_ids":[2]}'):
            with self.subTest(raw=raw):
                self.record.write_text(raw, encoding='utf-8')
                self.assert_bad(self.run_cli('--record', self.record), '')
        self.assert_bad(self.run_cli('--record', self.record.parent / 'Card'), '')
        self.assert_bad(self.run_cli(), '')


if __name__ == '__main__':
    unittest.main()
