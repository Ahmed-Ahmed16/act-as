# Cases: absent and installed skills, unknown and listed authors, clean and leftover folders.
# Boundaries: unset, missing, empty and comment lists; old and new entries; exit 0 and nonzero.
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import guard_run


class GuardRunTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='Zindle')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.skills = self.root / 'skills'
        self.skills.mkdir()
        self.tmp = self.root / 'scratch'
        self.tmp.mkdir()
        self.team = self.root / 'members.txt'
        self.team.write_text('  # members\n\n  acme-dev  \n zindle-dev \n', encoding='utf-8')
        self.pr = 'https://example.invalid/pulls/37'
        self.out = self.root / 'output'
        self.runner = Mock(return_value=subprocess.CompletedProcess([], 0, '', ''))
        self.env = dict(os.environ, ACT_AS_TEAM_LIST=str(self.team),
                        ACT_AS_SKILLS_DIR=str(self.skills), PYTHONDONTWRITEBYTECODE='1')

    def install(self, name='debate-review'):
        folder = self.skills / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'SKILL.md').write_text('', encoding='utf-8')
        return folder

    def debate(self, **overrides):
        options = dict(pr_url=self.pr, author='acme-dev', out_dir=self.out,
                       skills_dir=self.skills, list_path=self.team, env={},
                       runner=self.runner, tmp_dir=self.tmp)
        options.update(overrides)
        return guard_run.run_debate(**options)

    def run_cli(self, *args, env=None):
        script = Path(__file__).with_name('guard_run.py')
        return subprocess.run([sys.executable, '-B', str(script), *map(str, args)],
                              capture_output=True, text=True,
                              env=self.env if env is None else env)

    def test_missing_and_installed_skills_have_exact_status(self):
        for name in ('debate-review', 'clean-code-guard', 'test-guard', 'docs-guard'):
            with self.subTest(skill=name):
                (self.skills / name).mkdir()
                self.assertEqual(guard_run.skill_status(name, self.skills),
                                 f'not checked: {name} not installed')
                self.install(name)
                self.assertEqual(guard_run.skill_status(name, self.skills), 'installed')

    def test_skills_directory_uses_environment_then_home_default(self):
        self.install('zindle')
        with patch.dict(os.environ, {'ACT_AS_SKILLS_DIR': str(self.skills)}):
            self.assertEqual(guard_run.skill_status('zindle'), 'installed')
        home = self.root / 'home'
        default = home / '.claude' / 'skills' / 'zindle'
        default.mkdir(parents=True)
        (default / 'SKILL.md').touch()
        with patch.dict(os.environ, {}, clear=True), patch.object(Path, 'home', return_value=home):
            self.assertEqual(guard_run.skill_status('zindle'), 'installed')

    def test_blade_only_change_is_code(self):
        filename = 'views/zindle.blade.php'
        self.assertEqual(guard_run.guard_targets([filename]),
                         {'code': [filename], 'tests': [], 'docs': []})

    def test_test_paths_and_names_never_enter_code(self):
        paths = ['tests/Zindle.php', 'pkg/test/Floop.blade.php', 'pkg/tests/Zindle.php',
                 'src/ZindleTest.php', 'ui/zindle.test.js', 'ui/zindle.test.ts',
                 'ui/zindle.spec.js', 'ui/zindle.spec.ts', 'pkg/test_zindle.py',
                 'pkg/zindle_test.go', 'pkg\\tests\\Floop.php']
        self.assertEqual(guard_run.guard_targets(paths),
                         {'code': [], 'tests': paths, 'docs': []})

    def test_docs_and_regular_php_are_selected_without_near_matches(self):
        paths = ['app/Zindle.php', 'guide.md', 'guide.rst', 'docs/guide.txt',
                 'pkg/docs/image.svg', 'app/testing/Zindle.php', 'ui/zindle.js',
                 'app/testimony.php', 'guide.txt', 'ui/zindle.test.jsx']
        self.assertEqual(guard_run.guard_targets(paths), {
            'code': [paths[0], paths[5], paths[7]], 'tests': [], 'docs': paths[1:5]})
        self.assertEqual(guard_run.guard_targets([]), {'code': [], 'tests': [], 'docs': []})

    def test_team_matching_strips_whitespace_and_ignores_case(self):
        for author in ('acme-dev', 'ACME-DEV', '  AcMe-DeV  ', 'zindle-dev'):
            with self.subTest(author=author):
                self.assertEqual(guard_run.team_gate(author, self.team, env={}),
                                 (True, 'inside the team'))

    def test_unlisted_and_absent_authors_skip_without_running(self):
        self.install()
        for author in ('floop-dev', 'acme', '', '   ', None):
            with self.subTest(author=author):
                self.assertEqual(guard_run.team_gate(author, self.team, env={}),
                                 (False, 'not checked: debate-review skipped, PR from outside the team'))
                outcome = self.debate(author=author)
                self.assertEqual(outcome, dict(ran=False,
                    line='not checked: debate-review skipped, PR from outside the team',
                    command=None, worktree_removed=None))
        self.runner.assert_not_called()

    def test_missing_unset_and_empty_lists_never_allow_a_run(self):
        self.install()
        for contents in (None, '', ' \n\t\n', '# zindle\n  # acme-dev\n'):
            with self.subTest(contents=contents):
                path = self.root / 'absent.txt'
                if contents is not None:
                    path.write_text(contents, encoding='utf-8')
                self.assertEqual(guard_run.team_gate('acme-dev', path, env={}),
                                 (False, 'not checked: team list missing'))
                self.assertEqual(self.debate(list_path=path), dict(ran=False,
                    line='not checked: team list missing', command=None, worktree_removed=None))
        for env in ({}, {'ACT_AS_TEAM_LIST': ''}):
            with self.subTest(env=env):
                self.assertEqual(self.debate(list_path=None, env=env)['line'],
                                 'not checked: team list missing')
        self.runner.assert_not_called()

    def test_environment_list_is_used_and_explicit_list_wins(self):
        self.install()
        env = {'ACT_AS_TEAM_LIST': str(self.team)}
        self.assertEqual(guard_run.team_gate('ACME-DEV', env=env), (True, 'inside the team'))
        self.assertTrue(self.debate(list_path=None, env=env)['ran'])
        with patch.dict(os.environ, env):
            self.assertEqual(guard_run.team_gate('acme-dev'), (True, 'inside the team'))
            self.assertEqual(guard_run.team_gate('acme-dev', env={}),
                             (False, 'not checked: team list missing'))
        missing = self.root / 'missing.txt'
        self.assertEqual(guard_run.team_gate('acme-dev', missing, env=env),
                         (False, 'not checked: team list missing'))

    def test_command_is_exact_and_rejects_unsafe_extra_flags(self):
        folder = self.install()
        expected = ['node', str(folder / 'scripts' / 'review-pr.mjs'), self.pr,
                    '--dry-run', '--out-dir', str(self.out)]
        self.assertEqual(guard_run.build_debate_command(folder, self.pr, self.out), expected)
        self.assertEqual(guard_run.build_debate_command(folder, self.pr, self.out, []), expected)
        for flag in ('--post-draft', '--force', '--keep', '--local', '--check'):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                guard_run.build_debate_command(folder, self.pr, self.out, [flag])

    def test_missing_skill_is_checked_before_team_gate(self):
        self.assertEqual(self.debate(list_path=None), dict(ran=False,
            line='not checked: debate-review not installed', command=None, worktree_removed=None))
        self.runner.assert_not_called()

    def test_listed_author_runs_once_with_only_safe_command(self):
        folder = self.install()
        outcome = self.debate(author='ACME-DEV')
        expected = ['node', str(folder / 'scripts' / 'review-pr.mjs'), self.pr,
                    '--dry-run', '--out-dir', str(self.out)]
        self.assertEqual(outcome, dict(ran=True, line='ran: debate-review --dry-run',
                                      command=expected, worktree_removed=True, exit_code=0,
                                      stdout_path=str(self.out / 'debate-stdout.txt'),
                                      stderr_path=str(self.out / 'debate-stderr.txt')))
        self.runner.assert_called_once_with(expected, capture_output=True, text=True,
                                            encoding='utf-8', errors='replace')
        for call in self.runner.call_args_list:
            command = call.args[0]
            self.assertIn('--dry-run', command)
            self.assertTrue(set(command).isdisjoint(
                {'--post-draft', '--force', '--keep', '--local', '--check'}))

    def test_removed_and_leftover_new_worktrees_are_distinguished(self):
        self.install()
        old = self.tmp / 'debate-review-old'
        old.mkdir()
        for leave_behind in (False, True):
            with self.subTest(leave_behind=leave_behind):
                new = self.tmp / 'debate-review-x'

                def fake_runner(command, capture_output, text, encoding, errors):
                    self.assertIn('--dry-run', command)
                    new.mkdir()
                    if not leave_behind:
                        new.rmdir()
                    return subprocess.CompletedProcess(command, 0, '', '')

                outcome = self.debate(runner=fake_runner)
                self.assertTrue(outcome['ran'])
                self.assertIs(outcome['worktree_removed'], not leave_behind)
                self.assertEqual(outcome['line'],
                    'not checked: debate-review worktree left behind' if leave_behind
                    else 'ran: debate-review --dry-run')
                self.assertIs(new.exists(), leave_behind)
                self.assertTrue(old.is_dir())

    def test_nonzero_exit_and_leftover_take_distinct_statuses(self):
        self.install()
        for leave_behind in (False, True):
            with self.subTest(leave_behind=leave_behind):
                def fake_runner(command, capture_output, text, encoding, errors):
                    if leave_behind:
                        (self.tmp / 'debate-review-floop').touch()
                    return subprocess.CompletedProcess(command, 7, '', 'failed')

                outcome = self.debate(runner=fake_runner)
                self.assertTrue(outcome['ran'])
                self.assertIs(outcome['worktree_removed'], not leave_behind)
                self.assertEqual(outcome['line'],
                    'not checked: debate-review worktree left behind' if leave_behind
                    else 'not checked: debate-review failed, exit 7')

    # G35: success, failure with stderr, and empty streams must all leave evidence.
    def test_debate_streams_are_saved_and_returned_with_exit_code(self):
        scripts = self.install() / 'scripts'
        scripts.mkdir()
        fake_debate = scripts / 'review-pr.mjs'
        cases = [(0, 'review finished\n', 'warning\n'),
                 (7, 'review started\n', 'cannot load review module\n'), (0, '', '')]
        for index, (exit_code, stdout, stderr) in enumerate(cases):
            with self.subTest(exit_code=exit_code, stdout=stdout):
                fake_debate.write_text(
                    f'process.stdout.write({json.dumps(stdout)});\n'
                    f'process.stderr.write({json.dumps(stderr)});\n'
                    f'process.exitCode = {exit_code};\n', encoding='utf-8')
                out = self.out / str(index)
                outcome = self.debate(out_dir=out, runner=subprocess.run)
                self.assertTrue(outcome['ran'], outcome['line'])
                self.assertIn('exit_code', outcome)
                self.assertEqual(outcome['exit_code'], exit_code)
                for key, expected in (('stdout_path', stdout), ('stderr_path', stderr)):
                    self.assertIn(key, outcome)
                    saved = Path(outcome[key])
                    self.assertEqual(saved.parent, out)
                    self.assertEqual(saved.read_text(encoding='utf-8'), expected)

    def test_default_tmp_directory_and_skills_environment_are_used(self):
        self.install()
        with patch.object(tempfile, 'gettempdir', return_value=str(self.tmp)):
            outcome = self.debate(skills_dir=None, tmp_dir=None,
                                 env={'ACT_AS_SKILLS_DIR': str(self.skills)})
        self.assertTrue(outcome['ran'])
        self.assertTrue(outcome['worktree_removed'])

    def test_debate_utf8_child_output_is_saved(self):
        self.install()

        def child_runner(command, **kwargs):
            return subprocess.run([sys.executable, '-c',
                                   'import sys; sys.stdout.buffer.write(bytes([217, 129]))'],
                                  **kwargs)

        outcome = self.debate(runner=child_runner)
        self.assertTrue(outcome['ran'])
        self.assertTrue(outcome['worktree_removed'])
        self.assertEqual((self.out / 'debate-stdout.txt').read_text(encoding='utf-8'), '\u0641')

    def test_debate_runner_uses_utf8_with_replacement(self):
        self.install()
        outcome = self.debate()
        self.assertTrue(outcome['ran'])
        self.runner.assert_called_once_with(outcome['command'], capture_output=True, text=True,
                                            encoding='utf-8', errors='replace')

    def test_debate_missing_streams_write_empty_evidence(self):
        self.install()
        self.runner.return_value = subprocess.CompletedProcess([], 0, None, None)
        outcome = self.debate()
        self.assertTrue(outcome['ran'])
        self.assertTrue(outcome['worktree_removed'])
        for stream in ('stdout', 'stderr'):
            self.assertEqual((self.out / f'debate-{stream}.txt').read_bytes(), b'')

    def test_cli_reports_skills_targets_and_gate(self):
        self.install('zindle')
        for args, expected in (
                (('skills', 'zindle', 'floop'), 'installed\nnot checked: floop not installed\n'),
                (('gate', '--author', 'ACME-DEV'), 'inside the team\n'),
                (('gate', '--author', 'floop-dev'),
                 'not checked: debate-review skipped, PR from outside the team\n'),
                (('gate', '--author', 'acme-dev', '--list', self.root / 'absent.txt'),
                 'not checked: team list missing\n')):
            with self.subTest(args=args):
                completed = self.run_cli(*args)
                self.assertEqual((completed.returncode, completed.stdout, completed.stderr),
                                 (0, expected, ''))
        completed = self.run_cli('targets', 'views/zindle.blade.php', 'tests/Zindle.php')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {
            'code': ['views/zindle.blade.php'], 'tests': ['tests/Zindle.php'], 'docs': []})

    def test_cli_debate_skip_paths_never_launch_a_review(self):
        args = ('debate', '--pr', self.pr, '--author', 'floop-dev', '--out-dir', self.out)
        completed = self.run_cli(*args)
        self.assertEqual((completed.returncode, completed.stdout, completed.stderr),
                         (0, 'not checked: debate-review not installed\n', ''))
        self.install()
        completed = self.run_cli(*args)
        self.assertEqual((completed.returncode, completed.stdout, completed.stderr),
            (0, 'not checked: debate-review skipped, PR from outside the team\n', ''))

    def test_cli_usage_errors_exit_2(self):
        for args in ((), ('skills',), ('targets',), ('gate',), ('debate',),
                     ('debate', '--post-draft'), ('unknown',)):
            with self.subTest(args=args):
                completed = self.run_cli(*args)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, '')
                self.assertTrue(completed.stderr)


class GuardInstructionsTests(unittest.TestCase):
    # G34: this checks the written contract, not whether an agent follows it.
    def test_health_requires_guard_runs_saved_reports_and_unavailable_record(self):
        health = Path(__file__).resolve().parents[1] / 'roles/reviewer/modes/health.md'
        block = health.read_text(encoding='utf-8').split(
            '## Guard skills and debate-review (ticket 37)', 1)[1].split(
            '## Finish checklist', 1)[0]
        block = re.sub(r'\s+', ' ', block)
        for guard in ('clean-code-guard', 'test-guard', 'docs-guard'):
            with self.subTest(guard=guard):
                self.assertRegex(block, rf'Run `{guard}`[^.]*report only')
                self.assertIn(f'`runs/{guard}.txt`', block)
        self.assertRegex(block, r'cannot run[^.]*`not checked: <guard> <reason>`'
                                r'[^.]*check record')


if __name__ == '__main__':
    unittest.main()
