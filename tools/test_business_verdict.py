import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BusinessVerdictTests(unittest.TestCase):
    # Boundaries: empty and malformed inputs; every state; duplicate suffixes;
    # same and moved heads; short packets; equal, changed and missing drafts.
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='glorp-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.script = Path(__file__).with_name('business_verdict.py')
        self.areas = self.root / 'zindle.json'
        self.head = 'a1' * 20
        self.base = 'b2' * 20
        self.default = 'c3' * 20
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8', env=self.env)

    def assert_ok(self, run, output):
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, output + '\n')
        self.assertEqual(run.stderr, '')

    def assert_bad(self, run):
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(run.stdout, '')
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        self.assertTrue(run.stderr.startswith('business_verdict: error: '))

    def verdict(self, rows):
        self.areas.write_text(json.dumps({'areas': rows}), encoding='utf-8')
        return self.run_cli('verdict', '--areas', self.areas)

    def test_area_states_set_verdict_and_failures_come_first(self):
        cases = [
            ([('zindle', 'pass')], 'business: pass, area zindle: every rule kept'),
            ([('zindle', 'pass'), ('floop', 'pass')],
             'business: pass, area zindle: every rule kept; area floop: every rule kept'),
            ([('zindle', 'incomplete'), ('floop', 'not checked'), ('plim', 'pass')],
             'business: incomplete, area zindle: glorp; area floop: glorp'),
            ([('zindle', 'not checked')], 'business: incomplete, area zindle: glorp'),
            ([('zindle', 'incomplete'), ('floop', 'fail'), ('plim', 'pass'),
              ('snorf', 'fail'), ('twib', 'not checked')],
             'business: fail, area floop: glorp; area snorf: glorp; '
             'area zindle: glorp; area twib: glorp'),
        ]
        for states, expected in cases:
            with self.subTest(states=states):
                self.assert_ok(self.verdict([dict(area=area, state=state, reason='glorp')
                                            for area, state in states]), expected)

    def test_bad_area_documents_never_pass(self):
        invalid = [None, [], {}, {'areas': []}, {'areas': 'glorp'}, {'areas': [None]},
                   {'areas': [dict(area='zindle', state='glorp', reason='floop')]},
                   {'areas': [dict(area=1, state='pass', reason='floop')]},
                   {'areas': [dict(area='zindle', state='pass')]},
                   {'areas': [dict(area='zindle', state='pass', reason=1)]},
                   {'areas': [dict(area='zindle', state='pass', reason='glorp\nfloop')]}]
        for document in invalid:
            with self.subTest(document=document):
                self.areas.write_text(json.dumps(document), encoding='utf-8')
                self.assert_bad(self.run_cli('verdict', '--areas', self.areas))
        self.areas.write_text('{', encoding='utf-8')
        self.assert_bad(self.run_cli('verdict', '--areas', self.areas))
        self.areas.unlink()
        self.assert_bad(self.run_cli('verdict', '--areas', self.areas))

    def test_zindle_text_survives_ascii_shell(self):
        self.env['PYTHONIOENCODING'] = 'ascii'
        self.areas.write_text(json.dumps({'areas': [dict(area='žindle', state='fail',
                                                        reason='fløøp')]}), encoding='utf-8')
        for args, expected in [
            (('verdict', '--areas', self.areas), 'business: fail, area žindle: fløøp'),
            (('security-line', '--line', 'security: pass, fløøp', '--area', 'žindle'),
             'security: incomplete, fløøp; merge only after: rerun security for žindle'),
        ]:
            with self.subTest(args=args):
                self.assert_ok(self.run_cli(*args), expected)

    def test_security_states_keep_reasons_and_required_reruns(self):
        cases = [
            ('security: pass', 'security: incomplete, merge only after: rerun security for zindle'),
            ('security: pass, glorp',
             'security: incomplete, glorp; merge only after: rerun security for zindle'),
            ('security: incomplete, glorp',
             'security: incomplete, glorp; also merge only after: rerun security for zindle'),
            ('security: fail, glorp', 'security: fail, glorp; also: rerun security for zindle'),
            ('security: not asked: glorp', 'security: not asked: glorp'),
            ('security: not checked: glorp', 'security: not checked: glorp'),
        ]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assert_ok(self.run_cli('security-line', '--line', line,
                                           '--area', 'zindle'), expected)
        for line in [cases[2][1], cases[3][1]]:
            self.assert_ok(self.run_cli('security-line', '--line', line, '--area', 'zindle'), line)
        line = 'security: fail, glorp; also: rerun security for zindlex'
        self.assert_ok(self.run_cli('security-line', '--line', line, '--area', 'zindle'),
                       line + '; also: rerun security for zindle')

    def test_bad_security_lines_are_rejected(self):
        for line in ['pass', 'business: pass', 'security: glorp', 'security: passing',
                     'security: ', 'security: pass\nfloop', 'security: pass\rfloop']:
            with self.subTest(line=line):
                self.assert_bad(self.run_cli('security-line', '--line', line, '--area', 'zindle'))

    def packet(self, *, head=None, size='pass, glorp', business='pass, glorp', areas=None):
        (self.root / 'packet.md').write_text(
            f'identity: pr=7; head={self.head if head is None else head}; '
            f'base={self.base}; default=trunk@{self.default}; mode=business\n'
            f'size: {size}\nbusiness: {business}\n', encoding='utf-8')
        (self.root / 'rules-pages.json').write_text(json.dumps({
            'areas': [] if areas is None else areas}), encoding='utf-8')

    def rerun(self, *extra):
        return self.run_cli('rerun-check', '--packet', self.root, '--head', self.head, *extra)

    def commits_output(self):
        return f'use base {self.base}\nuse default {self.default}\n'

    def test_rerun_keeps_original_commits_and_accepts_head_case(self):
        self.packet(head=self.head.upper())
        self.assert_ok(self.rerun(), self.commits_output() + 'rerun-check: ok')

    def test_moved_head_refuses_before_other_work(self):
        self.packet(head='d4' * 20)
        run = self.rerun()
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, 'refuse: PR head moved since the packet was written '
                         f'(packet d4d4d4d, now {self.head[:7]}); ask for a new full run\n')
        self.assertEqual(run.stderr, '')

    def test_short_packet_refusal_needs_both_conditions(self):
        for size, business, code in [
            ('fail, glorp', 'not checked: PR over the cap, glorp', 3),
            ('pass, glorp', 'not checked: PR over the cap', 0),
            ('fail, glorp', 'incomplete, glorp', 0),
        ]:
            with self.subTest(size=size, business=business):
                self.packet(size=size, business=business)
                run = self.rerun()
                self.assertEqual(run.returncode, code, run.stderr)
                expected = ('refuse: rerun on a short packet is not decided (O19); ask the user'
                            if code == 3 else self.commits_output() + 'rerun-check: ok')
                self.assertEqual(run.stdout, expected + '\n')
                self.assertEqual(run.stderr, '')

    def test_draft_changes_warn_and_missing_folder_refuses(self):
        contents = b'Covers: app/Loans/\r\nR1. **match**\r\n'
        digest = 'sha256:' + hashlib.sha256(contents).hexdigest()
        self.packet(areas=[dict(area='zindle', commit=digest),
                           dict(area='floop', commit=self.default)])
        run = self.rerun()
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, 'refuse: drafts folder needed for draft page zindle\n')
        drafts = self.root / 'glorp'
        drafts.mkdir()
        for payload, warning in [
            (contents, ''), (b'glorp\n', 'page changed since the first run: zindle\n'),
            (None, 'page changed since the first run: zindle (file missing)\n'),
        ]:
            with self.subTest(payload=payload):
                path = drafts / 'zindle.md'
                if payload is None:
                    path.unlink()
                else:
                    path.write_bytes(payload)
                self.assert_ok(self.rerun('--drafts', drafts), self.commits_output()
                               + warning + 'rerun-check: ok')

    def test_bad_packets_are_rejected(self):
        self.packet()
        packet = self.root / 'packet.md'
        original = packet.read_text(encoding='utf-8')
        for broken in [original.replace('identity:', 'glorp:'),
                       original.replace(f'head={self.head}', 'head=glorp'),
                       original.replace(f'base={self.base}', 'base=glorp'),
                       original.replace(f'default=trunk@{self.default}', 'default=trunk'),
                       original.replace('default=trunk@', 'default=@'),
                       original.replace('head=', 'old-head='),
                       original.replace('head=', f'head={"d4" * 20}; head='),
                       original.replace('size:', 'glorp:'),
                       original.replace('business:', 'glorp:')]:
            with self.subTest(broken=broken):
                packet.write_text(broken, encoding='utf-8')
                self.assert_bad(self.rerun())
        self.packet()
        for document in ['{', '{}', '{"areas":null}', '{"areas":[{}]}',
                         json.dumps({'areas': [dict(area='../zindle', commit='sha256:' + 'a' * 64)]})]:
            with self.subTest(document=document):
                (self.root / 'rules-pages.json').write_text(document, encoding='utf-8')
                self.assert_bad(self.rerun())
        self.packet()
        packet.unlink()
        self.assert_bad(self.rerun())
        self.assert_bad(self.run_cli('rerun-check', '--packet', self.root, '--head', 'glorp'))

    def test_bad_command_arguments_use_single_error_line(self):
        for args in [[], ['glorp'], ['verdict'], ['security-line', '--line', 'security: pass'],
                     ['rerun-check', '--packet', str(self.root)]]:
            with self.subTest(args=args):
                self.assert_bad(self.run_cli(*args))


if __name__ == '__main__':
    unittest.main()
