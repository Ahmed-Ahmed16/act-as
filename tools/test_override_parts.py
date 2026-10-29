import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

if __package__:
    from . import override_parts
    from .test_short_packet import ShortPacketBase
else:
    import override_parts
    from test_short_packet import ShortPacketBase


class OverridePartsTests(ShortPacketBase):
    # Cases: 0, 1, 2 placeholders, padded lines, stale plans, and refused text.
    def prepare_override(self):
        self.prepare()
        saved = self.read('runs/size-count.json')
        text = '\n'.join([
            '# Review packet', "reviewed over the cap, on Ahmed's word",
            f'identity: repo=example/garden; pr=17; mode=full; head={self.head}; '
            f'base={self.base}; default=main@{self.base}; date=2026-10-28',
            'size: ' + saved['size_line'], 'business: not checked: rules page unavailable',
            'security: pass', 'health: pass', 'money: no money code found by reading; not proof',
            'Laravel: project 11.54.0, card docs 12.x', '',
            '## Behaviour changed', 'Plant seeds.', 'no translation files changed', '',
            '## Files that matter most', 'app/Seed.py plants seeds.', '',
            '## Tests run', f'CI run 5 on {self.head}: pass', '',
            '## Not checked', 'Business rules: rules page unavailable.', '',
            '## Known risks', 'none', '', '## Pointers', 'none', '',
            '## Split plan', '@@split-field@@', '',
            '## Drafts, not sent', 'Finding: no finding found by reading.', '@@split-draft@@', '',
        ])
        (self.packet / 'packet.md').write_bytes(text.encode())
        entries = []
        for mode, keys in [('security', [*(f'S{n}' for n in range(1, 23)), 'L1', 'L5']),
                           ('health', [*(f'H{n}' for n in range(1, 12)), *(f'T{n}' for n in range(1, 9))])]:
            entries += [dict(id=key, mode=mode, kind='check', area='', tool_result='No issue found.',
                             reading_result='Read the seed change.', word='none', reason='', base_read='', head_read='')
                        for key in keys]
        self.save('check-record.json', dict(required_ids=[], entries=entries))
        self.save('rules-pages.json', dict(areas=[]))

    def snapshot(self):
        return {p.relative_to(self.packet): p.read_bytes() for p in self.packet.rglob('*') if p.is_file()}

    def assert_refused(self, *args):
        before = self.snapshot()
        run = self.run_tool('override_parts.py', *args)
        self.assertEqual((run.returncode, run.stdout), (2, ''), run.stderr)
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        self.assertTrue(run.stderr.startswith('override_parts: '), run.stderr)
        self.assertEqual(self.snapshot(), before)
        return run

    def test_P1_P6_P8_full_override_passes_and_preserves_other_lines(self):
        self.prepare_override()
        path = self.packet / 'packet.md'
        original = path.read_bytes()
        before = self.snapshot()
        for ending in [b'\n', b'', b'\r\n']:
            with self.subTest(ending=ending):
                contents = original.rstrip(b'\n') + ending
                if ending == b'\r\n':
                    contents = contents.replace(b'\n', b'\r\n').replace(b'\r\r\n', b'\r\n')
                path.write_bytes(contents)
                run = self.passed(self.run_tool('override_parts.py', self.packet))
                self.assertEqual(run.stdout, 'override_parts: filled\n')
                filled = path.read_bytes()
                self.assertNotIn(b'\r', filled)
                self.assertEqual(filled.endswith(b'\n'), bool(ending))
                text = filled.decode()
                self.assertNotIn('@@', text)
                for phrase in ['not reviewed past size', 'safe to merge', 'not checked: PR over the cap']:
                    self.assertNotIn(phrase, text)
                opening = 'This PR is 321 counted lines; the cap is 300. It was reviewed over the cap, on request.'
                self.assertIn('Finding: no finding found by reading.\n' + opening + '\ngroup: plant, 160 counted lines', text)
                cursor = 0
                lines = text.split('\n')
                for line in contents.decode().replace('\r\n', '\n').split('\n'):
                    if line not in ('@@split-field@@', '@@split-draft@@'):
                        cursor = lines.index(line, cursor) + 1
                self.assertEqual(self.passed(self.check()).stdout, 'packet_check: pass\n')
                after = self.snapshot()
                self.assertEqual(set(after), set(before))
                self.assertEqual({k: v for k, v in after.items() if str(k) != 'packet.md'},
                                 {k: v for k, v in before.items() if str(k) != 'packet.md'})

    def test_P2_P2b_P3_P3b_bad_placeholders_leave_packet_unchanged(self):
        self.prepare_override()
        original = self.packet_text()
        for marker in ['@@split-field@@', '@@split-draft@@']:
            for replacement in ['', marker + '\n' + marker, marker + ' ', 'prefix ' + marker]:
                with self.subTest(marker=marker, replacement=replacement):
                    (self.packet / 'packet.md').write_bytes(original.replace(marker, replacement).encode())
                    self.assert_refused(self.packet)

    def test_P4_stale_input_leaves_packet_unchanged(self):
        self.prepare_override()
        path = self.packet / 'split-input.json'
        path.write_bytes(path.read_bytes() + b' ')
        self.assertIn('stale', self.assert_refused(self.packet).stderr)

    def test_P5_passing_size_leaves_packet_unchanged(self):
        self.prepare_override()
        self.save('runs/size-count.json', dict(self.read('runs/size-count.json'), verdict='pass'))
        self.assert_refused(self.packet)

    def test_P7_usage_and_missing_packet_have_1_error_line(self):
        self.packet.mkdir()
        for args in [(), (self.packet, self.packet), (self.packet,), (self.repo / 'old.py',),
                     (self.root / 'orchard',)]:
            with self.subTest(args=args):
                self.assert_refused(*args)

    def test_P9_forbidden_rendered_text_leaves_packet_unchanged(self):
        self.prepare_override()
        plan = self.read('split-plan.json')
        for phrase in ['not reviewed past size', 'safe to merge', 'not checked: PR over the cap']:
            with self.subTest(phrase=phrase):
                self.save('split-plan.json', dict(plan, main=dict(state='not established', evidence=phrase)))
                self.assert_refused(self.packet)

    def test_invalid_inputs_and_render_errors_leave_packet_unchanged(self):
        self.prepare_override()
        path = self.packet / 'split-plan.json'
        original = path.read_bytes()
        for contents in [None, b'{bad json', b'null', b'{}', b'\xff']:
            with self.subTest(contents=contents):
                path.unlink(missing_ok=True)
                if contents is not None:
                    path.write_bytes(contents)
                self.assert_refused(self.packet)
        path.write_bytes(original)
        plan = self.read('split-plan.json')
        self.save('split-plan.json', dict(plan, ci=dict(state='read', workflows=[dict(path='ci.yml', on_text=None)])))
        self.assert_refused(self.packet)

    def test_write_error_keeps_original_packet_and_removes_staged_file(self):
        self.prepare_override()
        before = self.snapshot()
        stdout, stderr = io.StringIO(), io.StringIO()
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=self.packet, delete=False) as output:
            staged = Path(output.name)
            self.addCleanup(staged.unlink, missing_ok=True)
            with patch.object(override_parts.tempfile, 'NamedTemporaryFile', return_value=output), \
                    patch.object(output, 'write', side_effect=OSError('garden disk full')), \
                    redirect_stdout(stdout), redirect_stderr(stderr):
                code = override_parts.main([str(self.packet)])
        self.assertEqual((code, stdout.getvalue()), (2, ''))
        self.assertEqual(stderr.getvalue(), 'override_parts: garden disk full\n')
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
