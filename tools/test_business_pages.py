import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BusinessPagesTests(unittest.TestCase):
    # Boundaries: Covers on lines 1 through 6; first Covers wins; patterns;
    # exact and nested paths;
    # 0, 1 and repeated statuses; old and new rename paths; absent drafts.
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='zindle-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.repo = self.root / 'floop'
        self.repo.mkdir()
        self.out = self.root / 'plim'
        self.drafts = self.root / 'glorp'
        self.drafts.mkdir()
        self.script = Path(__file__).with_name('business_pages.py')
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM='1', PYTHONDONTWRITEBYTECODE='1')
        self.git('init', '-b', 'trunk')
        self.base = self.commit()
        self.default = self.base

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

    def page(self, area, contents):
        self.write('docs/business-rules/' + area + '.md', contents)

    def commit(self):
        self.git('add', '-A')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.com',
                 'commit', '--allow-empty', '-m', 'glorp')
        return self.git('rev-parse', 'HEAD')

    def run_cli(self, head, *extra):
        return subprocess.run([sys.executable, str(self.script), '--repo', str(self.repo),
                               '--base', self.base, '--head', head,
                               '--default-ref', self.default, '--out', str(self.out),
                               *map(str, extra)], capture_output=True, text=True,
                              encoding='utf-8', env=self.env)

    def packet(self, head, *extra):
        run = self.run_cli(head, *extra)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        report = json.loads((self.out / 'runs/business-map.json').read_text(encoding='utf-8'))
        self.assertEqual(run.stdout, f'business_pages: {len(report["areas"])} touched areas, '
                         f'{len(report["no_area_found"])} files with no area found\n')
        return report

    def test_covers_position_controls_mapping(self):
        pages = {
            'zindle': 'Covers: `app/Vault.php`, , `app/Loans/`\nChecked at: glorp\n',
            'floop': '# Floop\r\nCovers: app/Loans\r\n',
            'plim': '# Plim\n\nCovers: app/Loans/\n',
            'glorp': 'Glorp\nCovers: app/Loans/\n',
            'snorf': '# Snorf\nR1. **match**\n',
            'twib': 'Covers: app/Untouched/\n',
            'blim': '# Blim\n\nGlorp\nCovers: app/Loans/\n',
            'flim': '# Flim\n\nGlorp\nPlim\nCovers: app/Loans/\n',
            'grib': '# Grib\n\nGlorp\nPlim\nFloop\nCovers: app/Loans/\n',
        }
        for area, contents in pages.items():
            self.page(area, contents)
        self.default = self.base = self.commit()
        self.write('app/Loans/LoanPolicy.php', 'zindle\n')
        report = self.packet(self.commit())
        self.assertEqual(report['files'], [dict(path='app/Loans/LoanPolicy.php',
                         old_path=None, status='A',
                         areas=['blim', 'flim', 'floop', 'glorp', 'plim', 'zindle'])])
        self.assertEqual(report['pages_without_covers'], ['grib', 'snorf'])
        areas = {area['area']: area for area in report['areas']}
        self.assertEqual(areas['zindle']['covers'], ['app/Loans/', 'app/Vault.php'])
        self.assertEqual(areas['plim']['covers'], ['app/Loans/'])
        self.assertTrue(report['areas'][0]['covers_ok'])
        self.assertEqual(areas['zindle']['checked_at'], 'glorp')
        self.assertIsNone(report['areas'][0]['checked_at'])
        self.assertFalse(areas['plim']['area_incomplete'])

    def test_first_covers_line_wins(self):
        self.page('zindle', '# Zindle\n\nCovers: src/Glorp.php\nCovers: src/Plim.php\n')
        self.default = self.base = self.commit()
        for path in ('src/Glorp.php', 'src/Plim.php'):
            self.write(path, 'floop\n')
        report = self.packet(self.commit())
        self.assertEqual(report['areas'][0]['covers'], ['src/Glorp.php'])
        self.assertEqual(report['areas'][0]['files'], ['src/Glorp.php'])
        self.assertEqual(report['no_area_found'], [dict(path='src/Plim.php', old_path=None)])

    def test_covers_patterns_are_reported_and_plain_entries_still_map(self):
        patterns = ['src/}glorp.php', 'src/{glorp.php', 'src/]glorp.php',
                    'src/[glorp.php', 'src/?.php', 'src/*.php']
        self.page('zindle', 'Covers: ' + ', '.join(patterns + ['src/Plim.php', 'lib/']) + '\n')
        self.default = self.base = self.commit()
        for path in ('src/Glorp.php', 'src/Plim.php', 'lib/Floop.php'):
            self.write(path, 'floop\n')
        report = self.packet(self.commit())
        area = report['areas'][0]
        self.assertEqual(area['covers'], ['lib/', 'src/Plim.php'])
        self.assertEqual(area['covers_patterns'], sorted(patterns))
        self.assertEqual(area['not_checked'], ['Covers entry is a pattern'])
        self.assertTrue(area['covers_ok'])
        self.assertTrue(area['area_incomplete'])
        self.assertEqual(area['files'], ['lib/Floop.php', 'src/Plim.php'])
        self.assertEqual(report['no_area_found'], [dict(path='src/Glorp.php', old_path=None)])

    def test_path_boundaries_and_overlapping_pages(self):
        self.page('zindle', 'Covers: app/Loans, docs/, app/Vault.php\n')
        self.page('floop', 'Covers: app/Loans/\n')
        self.page('plim', 'Covers: doc\n')
        self.page('snorf', 'Covers: app/*\n')
        self.default = self.base = self.commit()
        paths = ['app/Loans/LoanPolicy.php', 'app/LoansExtra/Loan.php', 'app/Vault.php',
                 'app/Vault.phpx', 'docs/Glorp.md', 'doc/Plim.md', 'glorp.txt']
        for path in paths:
            self.write(path, path + '\n')
        report = self.packet(self.commit())
        mapped = {row['path']: row['areas'] for row in report['files']}
        self.assertEqual(mapped, {
            paths[0]: ['floop', 'zindle'], paths[1]: [], paths[2]: ['zindle'],
            paths[3]: [], paths[4]: ['zindle'], paths[5]: ['plim'], paths[6]: []})
        self.assertEqual(report['no_area_found'], [dict(path=path, old_path=None)
                         for path in sorted([paths[1], paths[3], paths[6]])])
        self.assertEqual(report['areas'][2]['files'], sorted([paths[0], paths[2], paths[4]]))

    def test_renames_map_both_sides_and_deletion_maps(self):
        self.page('lending-and-returns', 'Covers: app/Loans/\n')
        self.write('app/Loans/Out.php', 'zindle\n' * 8)
        self.write('app/Glorp/In.php', 'floop\n' * 8)
        self.write('app/Loans/Gone.php', 'plim\n' * 8)
        self.default = self.base = self.commit()
        (self.repo / 'app/Loans/Out.php').rename(self.repo / 'app/Glorp/Out.php')
        (self.repo / 'app/Glorp/In.php').rename(self.repo / 'app/Loans/In.php')
        (self.repo / 'app/Loans/Gone.php').unlink()
        report = self.packet(self.commit())
        self.assertEqual(report['files'], [
            dict(path='app/Glorp/Out.php', old_path='app/Loans/Out.php', status='R100',
                 areas=['lending-and-returns']),
            dict(path='app/Loans/Gone.php', old_path=None, status='D',
                 areas=['lending-and-returns']),
            dict(path='app/Loans/In.php', old_path='app/Glorp/In.php', status='R100',
                 areas=['lending-and-returns'])])
        self.assertEqual(report['no_area_found'], [])

    def test_draft_hash_default_precedence_and_saved_bytes(self):
        default_bytes = b'Covers: app/Loans/\r\nR1. **match**\r\n'
        draft_bytes = b'Covers: app/Vault/\r\nR21. **owner**\r\n'
        self.page('zindle', default_bytes)
        self.default = self.base = self.commit()
        (self.drafts / 'zindle.md').write_text('Covers: app/Glorp/\n', encoding='utf-8')
        (self.drafts / 'floop.md').write_bytes(draft_bytes)
        self.write('app/Loans/LoanPolicy.php', 'zindle\n')
        self.write('app/Vault/VaultPolicy.php', 'floop\n')
        self.write('app/Glorp/GlorpPolicy.php', 'plim\n')
        head = self.commit()
        before = {path.name: path.read_bytes() for path in self.drafts.iterdir()}
        report = self.packet(head, '--drafts', self.drafts)
        draft, default = report['areas']
        self.assertEqual(draft, dict(area='floop', source='draft',
                         page=str(self.drafts / 'floop.md'),
                         commit='sha256:' + hashlib.sha256(draft_bytes).hexdigest(),
                         checked_at=None, covers=['app/Vault/'], covers_ok=True,
                         covers_patterns=[], not_checked=[], area_incomplete=False,
                         draft_also_exists=False, rules=[dict(id='R21', status='owner')],
                         files=['app/Vault/VaultPolicy.php']))
        self.assertEqual(default['source'], 'default')
        self.assertEqual(default['commit'], self.default)
        self.assertTrue(default['draft_also_exists'])
        self.assertEqual(default['page'], 'docs/business-rules/zindle.md')
        self.assertEqual(report['default_commit'], self.default)
        self.assertEqual((report['base'], report['head'], report['default_ref']),
                         (self.base, head, self.default))
        for area, contents in [('zindle', default_bytes), ('floop', draft_bytes)]:
            self.assertEqual((self.out / f'runs/rules-page-{area}.md').read_bytes(), contents)
        manifest = json.loads((self.out / 'rules-pages.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest, {'areas': [dict(area=area['area'], page=area['page'],
                         commit=area['commit'], rules=area['rules']) for area in [draft, default]]})
        self.assertEqual({path.name: path.read_bytes() for path in self.drafts.iterdir()}, before)

    def test_status_words_are_counted_without_glossary_words(self):
        self.page('zindle', 'Covers: app/Loans/\nChecked at: floop\nChecked at: plim\n'
                  'R31. **MATCH** **glorp**\nR32. **match** **gap**\n'
                  'R33. **open** **open**\nR34. **glorp**\nR35. plim\n'
                  'R36. **gap**\nR37. **owner**\nR38. **open**\n R39. **match**\n')
        self.default = self.base = self.commit()
        self.write('app/Loans/Loan.php', 'zindle\n')
        area = self.packet(self.commit())['areas'][0]
        self.assertEqual(area['checked_at'], 'floop')
        self.assertEqual(area['rules'], [dict(id=rule_id, status=status) for rule_id, status in zip(
                         ['R31', 'R32', 'R33', 'R34', 'R35', 'R36', 'R37', 'R38'],
                         ['match', 'multiple', 'multiple', 'none', 'none', 'gap', 'owner', 'open'])])
        self.assertEqual(area['not_checked'], ['rule R32 has 2 statuses',
                         'rule R33 has 2 statuses', 'rule R34 has no status',
                         'rule R35 has no status'])
        self.assertTrue(area['area_incomplete'])

    def test_git_objects_ignore_working_tree_and_output_is_stable(self):
        self.page('zindle', 'Covers: app/Loans/\n')
        self.write('app/Loans/Loan.php', 'zindle\n')
        self.default = self.base = self.commit()
        self.write('app/Loans/Loan.php', 'floop\n')
        self.write('app/Loans/Glorp [Plim].php', 'plim\n')
        head = self.commit()
        self.page('zindle', 'Covers: nowhere/\n')
        self.write('app/Loans/Untracked.php', 'plim\n')
        (self.repo / 'app/Loans/Loan.php').unlink()
        self.default = 'trunk'
        report = self.packet(head)
        self.assertEqual([row['path'] for row in report['files']],
                         ['app/Loans/Glorp [Plim].php', 'app/Loans/Loan.php'])
        self.assertEqual(report['files'][1]['status'], 'M')
        self.assertEqual(report['areas'][0]['files'],
                         ['app/Loans/Glorp [Plim].php', 'app/Loans/Loan.php'])
        before = {str(path.relative_to(self.out)): path.read_bytes()
                  for path in self.out.rglob('*') if path.is_file()}
        self.packet(head)
        self.assertEqual({str(path.relative_to(self.out)): path.read_bytes()
                         for path in self.out.rglob('*') if path.is_file()}, before)
        self.assertEqual(report['default_commit'], head)

    def test_no_default_folder_and_empty_diff(self):
        report = self.packet(self.base)
        self.assertEqual(report['files'], [])
        self.assertEqual(report['areas'], [])
        self.assertEqual(report['pages_without_covers'], [])
        self.write('glorp.php', 'plim\n')
        report = self.packet(self.commit())
        self.assertEqual(report['no_area_found'], [dict(path='glorp.php', old_path=None)])

    def test_bad_refs_fail_without_output(self):
        self.env['PYTHONIOENCODING'] = 'ascii'
        for flag, ref in [('--base', 'zindle-missing'), ('--head', 'zindle-missing'),
                          ('--default-ref', 'zindle-missing'), ('--base', 'žindle-missing')]:
            with self.subTest(flag=flag, ref=ref):
                run = self.run_cli(self.base, flag, ref)
                self.assertEqual(run.returncode, 1, run.stderr)
                self.assertEqual(run.stdout, '')
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
                self.assertTrue(run.stderr.startswith('business_pages: error: '))
                self.assertFalse(self.out.exists())

    def test_bad_arguments_are_rejected(self):
        run = self.run_cli(self.base, '--drafts', self.root / 'missing')
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(run.stdout, '')


if __name__ == '__main__':
    unittest.main()
