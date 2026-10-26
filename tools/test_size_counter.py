import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

if __package__:
    from .test_packet_check import good_inputs, replace_body, replace_line, single_packet
else:
    from test_packet_check import good_inputs, replace_body, replace_line, single_packet


class SizeCounterTests(unittest.TestCase):
    # Cases: 0, 300, 301; added, changed, deleted; empty and binary files;
    # equal bytes, different bytes, both trees; bad arguments and failed git.
    # Wrong counts, kinds, comparison points, or hunk ids must fail these tests.
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='size-counter-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.repo = self.root / 'shop'
        self.repo.mkdir()
        self.script = Path(__file__).with_name('size_counter.py')
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM='1', PYTHONDONTWRITEBYTECODE='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Acme')
        self.git('config', 'user.email', 'dev@acme.invalid')
        self.base = self.commit()

    def git(self, *args):
        run = subprocess.run(['git', '-c', 'core.autocrlf=false',
                              '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args],
                             capture_output=True, env=self.env)
        self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', 'replace'))
        return run.stdout.decode('utf-8', 'surrogateescape').strip()

    def write(self, path, contents):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents.encode('utf-8') if isinstance(contents, str) else contents)

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '--allow-empty', '-m', 'Update orchard')
        return self.git('rev-parse', 'HEAD')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8', env=self.env)

    def count(self, head, *extra):
        run = self.run_cli('--repo', self.repo, '--base', self.base, '--head', head, *extra)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertEqual(len(run.stdout.splitlines()), 1)
        return json.loads(run.stdout)

    def file_rows(self, folder):
        document = json.loads((folder / 'files.json').read_text(encoding='utf-8'))
        self.assertEqual(set(document), {'files'})
        return document['files']

    def test_300_passes_and_301_fails(self):
        for lines, verdict in [(300, 'pass'), (301, 'fail')]:
            with self.subTest(lines=lines):
                self.write('orchard.py', 'fruit\n' * lines)
                head = self.commit()
                report = self.count(head)
                self.assertEqual(report['counted_total'], lines)
                self.assertEqual(report['verdict'], verdict)
                self.assertEqual(report['cap'], 300)

    def test_each_left_out_kind_has_its_own_lines_and_files(self):
        for path, lines in [('tests/orchard.py', 2), ('composer.lock', 3),
                            ('public/build/orchard.js', 4), ('orchard.md', 5)]:
            self.write(path, 'fruit\n' * lines)
        head = self.commit()
        report = self.count(head)
        self.assertEqual(report['left_out'], {
            'tests': {'lines': 2, 'files': 1}, 'lock files': {'lines': 3, 'files': 1},
            'generated': {'lines': 4, 'files': 1}, 'docs': {'lines': 5, 'files': 1}})
        self.assertEqual((report['files'], report['added'], report['deleted'],
                          report['total_lines'], report['counted_total']), (4, 14, 0, 14, 0))

    def test_exact_public_copy_is_generated_but_1_byte_change_is_counted(self):
        self.write('resources/orchard.js', b'fruit\n')
        self.base = self.commit()
        self.write('public/orchard.js', b'fruit\n')
        self.write('public/grove.js', b'fruits\n')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        rows = {row['path']: row for row in self.file_rows(folder)}
        self.assertEqual(rows['public/orchard.js']['kind'], 'generated')
        self.assertEqual(rows['public/grove.js']['kind'], 'counted')
        self.assertEqual(report['counted_total'], 1)

    def test_storage_and_its_gitignore_are_generated(self):
        self.write('storage/orchard.txt', 'fruit\nfruit\n')
        self.write('storage/app/.gitignore', '*\n!.gitignore\n')
        report = self.count(self.commit())
        self.assertEqual(report['left_out']['generated'], {'lines': 4, 'files': 2})
        self.assertEqual(report['counted_total'], 0)

    def test_missing_base_fails_without_json_or_files(self):
        self.write('orchard.py', 'fruit\n')
        head = self.commit()
        folder = self.root / 'packet'
        run = self.run_cli('--repo', self.repo, '--base', 'f' * 40, '--head', head,
                           '--out', folder)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stdout, '')
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        self.assertIn('git', run.stderr)
        self.assertFalse((folder / 'files.json').exists())

    def test_crlf_and_lf_are_different_blobs(self):
        self.write('resources/orchard.js', b'fruit\r\n')
        self.base = self.commit()
        self.write('public/orchard.js', b'fruit\n')
        report = self.count(self.commit())
        self.assertEqual(report['counted_total'], 1)
        self.assertEqual(report['left_out']['generated'], {'lines': 0, 'files': 0})

    def test_binary_has_0_lines_and_no_hunks(self):
        self.write('orchard.bin', b'\0fruit\xff')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        self.assertEqual((report['files'], report['total_lines'], report['counted_total']),
                         (1, 0, 0))
        self.assertEqual(self.file_rows(folder), [dict(path='orchard.bin', old_path='',
                         status='added', kind='counted', counted_lines=0, hunks=[])])

    def test_merged_without_base_prints_exact_reason(self):
        run = self.run_cli('--repo', self.repo, '--head', self.base, '--merged')
        self.assertEqual(run.returncode, 3)
        self.assertEqual(run.stdout, 'not checked: PR already merged, base not proved\n')
        self.assertEqual(run.stderr, '')

    def test_merged_base_rule_can_be_called(self):
        self.assertTrue(self.script.is_file(), 'size_counter.py has not been built')
        spec = importlib.util.spec_from_file_location('size_counter', self.script)
        counter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(counter)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = counter.main(['--repo', str(self.repo), '--head', self.base, '--merged'])
        self.assertEqual(code, 3)
        self.assertEqual(output.getvalue(), 'not checked: PR already merged, base not proved\n')

    def test_merged_with_proved_base_counts(self):
        self.write('orchard.py', 'fruit\n')
        report = self.count(self.commit(), '--merged')
        self.assertEqual(report['counted_total'], 1)

    def test_three_dots_count_only_branch_changes(self):
        self.git('checkout', '-b', 'orchard')
        self.write('orchard.py', 'branch fruit\n')
        head = self.commit()
        self.git('checkout', 'main')
        self.write('grove.py', 'main fruit\n' * 8)
        self.base = self.commit()
        report = self.count(head)
        self.assertEqual((report['files'], report['added'], report['deleted'],
                          report['counted_total']), (1, 1, 0, 1))
        self.assertEqual((report['base'], report['head']), (self.base, head))

    def test_files_shape_hunk_sums_and_exact_size_line(self):
        self.write('orchard.py', ''.join(f'fruit {n}\n' for n in range(12)))
        self.write('removed.py', 'old fruit\nold tree\n')
        self.base = self.commit()
        self.write('orchard.py', 'pear\n' + ''.join(f'fruit {n}\n' for n in range(1, 11))
                   + 'plum\n')
        (self.repo / 'removed.py').unlink()
        self.write('added.py', 'fruit\n')
        self.write('tests/orchard.py', 'check fruit\ncheck tree\ncheck leaf\n')
        folder = self.root / 'runs' / 'packet'
        head = self.commit()
        report = self.count(head, '--out', folder)
        self.assertEqual(set(report), {'base', 'head', 'files', 'added', 'deleted',
                         'total_lines', 'counted_total', 'cap', 'verdict', 'left_out', 'size_line'})
        self.assertEqual((report['base'], report['head'], report['files'], report['added'],
                          report['deleted'], report['total_lines']),
                         (self.base, head, 4, 6, 4, 10))
        rows = self.file_rows(folder)
        self.assertEqual([row['path'] for row in rows],
                         ['added.py', 'orchard.py', 'removed.py', 'tests/orchard.py'])
        self.assertEqual([row['status'] for row in rows],
                         ['added', 'modified', 'deleted', 'added'])
        self.assertEqual([row['counted_lines'] for row in rows], [1, 4, 2, 0])
        self.assertEqual([row['hunks'] for row in rows], [
            [{'id': 'f1h1', 'counted_lines': 1}],
            [{'id': 'f2h1', 'counted_lines': 2}, {'id': 'f2h2', 'counted_lines': 2}],
            [{'id': 'f3h1', 'counted_lines': 2}],
            [{'id': 'f4h1', 'counted_lines': 0}]])
        for row in rows:
            self.assertEqual(set(row), {'path', 'old_path', 'status', 'kind',
                                       'counted_lines', 'hunks'})
            self.assertEqual(row['old_path'], '')
            self.assertEqual(sum(hunk['counted_lines'] for hunk in row['hunks']),
                             row['counted_lines'])
        self.assertEqual(sum(row['counted_lines'] for row in rows), report['counted_total'])
        self.assertEqual(report['size_line'],
                         'pass, 7 counted lines, cap 300; left out: tests 3 (1 files), '
                         'lock files 0 (0 files), generated 0 (0 files), docs 0 (0 files)')

    def test_bad_arguments_have_1_stderr_line(self):
        for args in [(), ('--repo', self.repo),
                     ('--repo', self.repo, '--head', self.base),
                     ('--repo', self.repo, '--head', self.base, '--base'),
                     ('--repo', self.repo, '--head', self.base, '--base', self.base, '--unknown'),
                     ('--repo', self.root / 'absent', '--head', self.base, '--base', self.base)]:
            with self.subTest(args=args):
                run = self.run_cli(*args)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, '')
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)

    def test_size_packet_with_counter_files_passes_packet_check(self):
        self.write('orchard.py', 'fruit\nfruit\n')
        head = self.commit()
        folder = self.root / 'packet'
        report = self.count(head, '--out', folder)
        packet = single_packet('size').replace('a' * 40, head).replace('b' * 40, self.base)
        packet = replace_line(packet, 'size', report['size_line'])
        packet = replace_body(packet, 'Split plan', 'not needed: 2 counted lines, cap 300')
        (folder / 'packet.md').write_text(packet, encoding='utf-8')
        for filename, contents in good_inputs().items():
            if filename != 'files.json':
                (folder / filename).write_text(json.dumps(contents), encoding='utf-8')
        checker = Path(__file__).with_name('packet_check.py')
        run = subprocess.run([sys.executable, str(checker), str(folder)],
                             capture_output=True, text=True, env=self.env)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout, 'packet_check: pass\n')

    def test_kind_rules_and_first_match_order(self):
        cases = [('vendor/tests/orchard.md', 'generated'), ('tests/orchard.lock', 'lock'),
                 ('tests/orchard.md', 'test'), ('app/tests/orchard.py', 'test'),
                 ('app/OrchardTest.php', 'test'), ('tests/orchard.py', 'test'),
                 ('database/factories/OrchardFactory.php', 'counted'),
                 ('database/migrations/orchard.php', 'counted'), ('lang/en.json', 'counted'),
                 ('.github/workflows/orchard.yml', 'counted'), ('notes.txt', 'counted'),
                 ('orchard.MARKDOWN', 'docs'), ('package-lock.json', 'lock'),
                 ('yarn.lock', 'lock'), ('pnpm-lock.yaml', 'lock'), ('nested/orchard.lock', 'lock'),
                 ('node_modules/orchard.js', 'generated'), ('bootstrap/cache/orchard.php', 'generated'),
                 ('public/vendor/orchard.js', 'generated'), ('orchard.min.js', 'generated'),
                 ('orchard.min.css', 'generated'), ('orchard.map', 'generated'),
                 ('_ide_helper.php', 'generated'), ('_ide_helper_models.php', 'generated'),
                 ('.phpstorm.meta.php', 'generated')]
        for path, kind in cases:
            self.write(path, path + '\n')
        folder = self.root / 'packet'
        self.count(self.commit(), '--out', folder)
        rows = {row['path']: row for row in self.file_rows(folder)}
        for path, kind in cases:
            with self.subTest(path=path):
                self.assertEqual(rows[path]['kind'], kind)

    def test_deleted_public_copy_uses_base_and_modified_copy_uses_head(self):
        self.write('resources/orchard.js', 'fruit\n')
        self.write('public/removed.js', 'fruit\n')
        self.write('public/changed.js', 'old fruit\n')
        self.base = self.commit()
        (self.repo / 'public/removed.js').unlink()
        self.write('resources/orchard.js', 'new fruit\n')
        self.write('public/changed.js', 'new fruit\n')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        rows = {row['path']: row for row in self.file_rows(folder)}
        self.assertEqual(rows['public/removed.js']['kind'], 'generated')
        self.assertEqual(rows['public/changed.js']['kind'], 'generated')
        self.assertEqual(report['left_out']['generated'], {'lines': 3, 'files': 2})
        self.assertEqual(report['counted_total'], 2)

    def test_public_copy_requires_non_public_file_and_ignores_empty_blob(self):
        self.write('public/orchard.js', 'fruit\n')
        self.write('public/grove.js', 'fruit\n')
        self.write('resources/empty', b'')
        self.write('public/empty', b'')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        self.assertEqual(report['counted_total'], 2)
        self.assertEqual(report['left_out']['generated'], {'lines': 0, 'files': 0})
        self.assertTrue(all(row['kind'] == 'counted' for row in self.file_rows(folder)))

    # The old add plus delete rule was withdrawn: a move now uses Git's rename counts.
    # Controls: full add/delete breaks pure moves; dropping all moves breaks edited moves.
    # Using just 1 path's kind breaks a crossing; counting every move breaks tests to tests.
    def move_file(self, old_path, new_path, contents):
        self.write(old_path, ''.join(f'fruit {n}\n' for n in range(12)))
        self.base = self.commit()
        target = self.repo / new_path
        target.parent.mkdir(parents=True, exist_ok=True)
        (self.repo / old_path).rename(target)
        if contents is not None:
            self.write(new_path, contents)

    def test_pure_move_counts_0_and_keeps_both_paths(self):
        self.write('orchard.py', 'fruit\n')
        self.base = self.commit()
        (self.repo / 'orchard.py').rename(self.repo / 'grove.py')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        self.assertEqual([(row['path'], row['status'], row['old_path'])
                          for row in self.file_rows(folder)],
                         [('grove.py', 'renamed', 'orchard.py')])
        self.assertEqual(self.file_rows(folder)[0]['counted_lines'], 0)
        self.assertEqual(self.file_rows(folder)[0]['hunks'], [])
        self.assertEqual((report['files'], report['added'], report['deleted'],
                          report['total_lines'], report['counted_total']), (1, 0, 0, 0, 0))

    def test_edited_move_counts_3_and_hunks_match_the_row(self):
        contents = 'pear\n' + ''.join(f'fruit {n}\n' for n in range(1, 12)) + 'plum\n'
        self.move_file('app/fruit [1].php', 'app/grove [2].php', contents)
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        self.assertEqual((report['files'], report['added'], report['deleted'],
                          report['total_lines'], report['counted_total']), (1, 2, 1, 3, 3))
        row, = self.file_rows(folder)
        self.assertEqual((row['path'], row['old_path'], row['status'], row['kind']),
                         ('app/grove [2].php', 'app/fruit [1].php', 'renamed', 'counted'))
        self.assertEqual(row['counted_lines'], 3)
        self.assertEqual(row['hunks'], [{'id': 'f1h1', 'counted_lines': 2},
                                        {'id': 'f1h2', 'counted_lines': 1}])
        self.assertEqual(sum(hunk['counted_lines'] for hunk in row['hunks']),
                         row['counted_lines'])

    def test_move_plus_new_file_counts_only_new_lines(self):
        # Dropping the whole diff when it has a move loses these 2 new lines.
        self.move_file('app/fruit.php', 'app/grove.php', None)
        self.write('app/seed.php', 'seed\nsprout\n')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        self.assertEqual((report['files'], report['added'], report['deleted'],
                          report['counted_total']), (2, 2, 0, 2))
        self.assertEqual([(row['status'], row['counted_lines'], row['old_path'])
                          for row in self.file_rows(folder)],
                         [('renamed', 0, 'app/fruit.php'), ('added', 2, '')])

    def test_move_kind_counts_edits_when_either_path_is_counted(self):
        contents = 'pear\n' + ''.join(f'fruit {n}\n' for n in range(1, 12)) + 'plum\n'
        cases = [('app/fruit.php', 'tests/fruit.php', contents, 'counted', 3),
                 ('tests/seed.php', 'app/seed.php', contents, 'counted', 3),
                 ('tests/tree.php', 'tests/grove.php', contents, 'test', 0),
                 ('app/leaf.php', 'tests/leaf.php', None, 'counted', 0)]
        for old_path, new_path, edited, kind, counted in cases:
            with self.subTest(old_path=old_path, new_path=new_path):
                self.move_file(old_path, new_path, edited)
                folder = self.root / 'packet'
                report = self.count(self.commit(), '--out', folder)
                row, = self.file_rows(folder)
                self.assertEqual((row['path'], row['old_path'], row['status'], row['kind'],
                                  row['counted_lines']),
                                 (new_path, old_path, 'renamed', kind, counted))
                self.assertEqual(report['counted_total'], counted)
                self.assertEqual(report['left_out']['tests'],
                                 {'lines': 3, 'files': 1} if kind == 'test'
                                 else {'lines': 0, 'files': 0})

    def test_rename_records_reject_broken_shapes(self):
        # The subprocess boundary is mocked because real Git emits only valid records.
        spec = importlib.util.spec_from_file_location('size_counter', self.script)
        counter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(counter)
        metadata = b':100644 100644 ' + b'a' * 40 + b' ' + b'b' * 40 + b' R090\0'
        raw = metadata + b'app/fruit.php\0app/grove.php\0'
        numstat = b'2\t1\t\0app/fruit.php\0app/grove.php\0'
        with mock.patch.object(counter.subprocess, 'run', side_effect=[
                subprocess.CompletedProcess([], 0, raw, b''),
                subprocess.CompletedProcess([], 0, numstat, b'')]):
            file, = counter.changed_files(self.repo, self.base)
        self.assertEqual((file['path'], file['old_path'], file['added'], file['deleted']),
                         ('app/grove.php', 'app/fruit.php', 2, 1))
        cases = [(metadata + b'app/fruit.php\0', numstat),
                 (raw[:-1], numstat), (raw, numstat[:-1]),
                 (raw, b'2\t1\t\0app/fruit.php\0'),
                 (raw, b'2\t1\t\0\0app/grove.php\0'),
                 (raw, b'2\t1\t\0app/other.php\0app/grove.php\0'),
                 (raw, b'x\t1\t\0app/fruit.php\0app/grove.php\0'),
                 (raw, numstat + numstat), (raw, b'')]
        for raw_output, numstat_output in cases:
            with self.subTest(raw=raw_output, numstat=numstat_output):
                with mock.patch.object(counter.subprocess, 'run', side_effect=[
                        subprocess.CompletedProcess([], 0, raw_output, b''),
                        subprocess.CompletedProcess([], 0, numstat_output, b'')]):
                    with self.assertRaises(counter.GitError):
                        counter.changed_files(self.repo, self.base)

    def test_empty_diff_has_0_totals_and_no_files(self):
        folder = self.root / 'packet'
        report = self.count(self.base, '--out', folder)
        self.assertEqual((report['files'], report['total_lines'], report['counted_total']), (0, 0, 0))
        self.assertEqual(report['verdict'], 'pass')
        self.assertEqual(self.file_rows(folder), [])

    def test_paths_with_spaces_unicode_and_wildcards_keep_their_hunks(self):
        for path in ['fruit tree.py', 'grove/fruit [1].py', 'grove/é.py']:
            self.write(path, 'fruit')
        folder = self.root / 'packet'
        report = self.count(self.commit(), '--out', folder)
        rows = self.file_rows(folder)
        self.assertEqual({row['path'] for row in rows},
                         {'fruit tree.py', 'grove/fruit [1].py', 'grove/é.py'})
        self.assertEqual(report['counted_total'], 3)
        self.assertTrue(all(row['hunks'] == [{'id': f'f{index}h1', 'counted_lines': 1}]
                            for index, row in enumerate(rows, 1)))


if __name__ == '__main__':
    unittest.main()
