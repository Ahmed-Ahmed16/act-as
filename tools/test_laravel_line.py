import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('laravel_line.py')


class LaravelLineTests(unittest.TestCase):
    # Cases: missing, invalid, empty, mixed types, first match, and unsafe text.
    def setUp(self):
        tree = tempfile.TemporaryDirectory()
        self.addCleanup(tree.cleanup)
        self.folder = Path(tree.name)
        self.lock = self.folder / 'composer.lock'
        self.manifest = self.folder / 'composer.json'

    def run_tool(self, *args):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_L1_to_L5b_L7_L8_L9_versions_fallbacks_and_packet_shape(self):
        locked = 'Laravel: project 11.54.0, card docs 12.x'
        constraint = 'Laravel: project ^11.0, card docs 12.x, from the constraint, not the lock'
        unknown = 'Laravel: project ___ (laravel version), card docs 12.x'
        cases = [
            ('L1', {'packages': [{'name': 'laravel/framework', 'version': 'v11.54.0'}]}, '^11.0', locked),
            ('L1b', {'packages': [{'name': 'laravel/framework', 'version': '11.9.0'}]}, '^11.0',
             'Laravel: project 11.9.0, card docs 12.x'),
            ('L2', {'packages-dev': [{'name': 'laravel/framework', 'version': 'v12.0.0'}]}, '^11.0', constraint),
            ('L3', None, '^11.0', constraint),
            ('L4', '{bad json', '^11.0', constraint),
            ('L5', None, {}, unknown),
            ('L5b', None, None, unknown),
            ('L7', None, '>=11.0, <12',
             'Laravel: project >=11.0 <12, card docs 12.x, from the constraint, not the lock'),
            ('L8', {'packages': [None, {'name': 'laravel/framework', 'version': 11}]}, '^11.0', constraint),
            ('lock array', [], '^11.0', constraint),
            ('packages object', {'packages': {}}, '^11.0', constraint),
            ('empty version', {'packages': [{'name': 'laravel/framework', 'version': ', \t\n'}]}, '^11.0', constraint),
            ('first version unusable', {'packages': [{'name': 'laravel/framework', 'version': ', \t\n'},
                                                    {'name': 'laravel/framework', 'version': '12.0.0'}]},
             '^11.0', constraint),
            ('first usable', {'packages': [{'name': 'garden/seed', 'version': '9'},
                                          {'name': 'laravel/framework', 'version': ''},
                                          {'name': 'laravel/framework', 'version': 'v11.54.0'},
                                          {'name': 'laravel/framework', 'version': 'v12.0.0'}]}, None, locked),
            ('version whitespace', {'packages': [{'name': 'laravel/framework', 'version': ' v11.54.0,\n\t '}]},
             None, locked),
            ('v without digit', {'packages': [{'name': 'laravel/framework', 'version': 'vnext'}]}, None,
             'Laravel: project vnext, card docs 12.x'),
            ('invalid manifest', None, '{bad json', unknown),
            ('manifest array', None, [], unknown),
            ('require null', None, {'require': None}, unknown),
            ('empty constraint', None, ', \t\n', unknown),
            ('non string constraint', None, 11, unknown),
        ]
        for label, lock, manifest, expected in cases:
            with self.subTest(case=label):
                for path in (self.lock, self.manifest):
                    path.unlink(missing_ok=True)
                if lock is not None:
                    self.lock.write_bytes((lock if isinstance(lock, str) else json.dumps(lock)).encode())
                if manifest is not None:
                    document = {'require': {'laravel/framework': manifest}} if isinstance(manifest, (str, int)) else manifest
                    contents = manifest if label == 'invalid manifest' else json.dumps(document)
                    self.manifest.write_bytes(contents.encode())
                run = self.run_tool(self.lock, self.manifest)
                self.assertEqual((run.returncode, run.stderr, run.stdout), (0, '', expected + '\n'))
                self.assertEqual(len(run.stdout.splitlines()), 1)
                self.assertRegex(run.stdout.rstrip('\n'),
                                 r'^Laravel: project [^,]+, card docs [0-9]+\.x(, from the constraint, not the lock)?$')

    def test_L6_L6b_wrong_argument_counts_have_1_error_line(self):
        for args in [(), (self.lock,), (self.lock, self.manifest, 'orchard')]:
            with self.subTest(args=args):
                run = self.run_tool(*args)
                self.assertEqual((run.returncode, run.stdout), (2, ''))
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
                self.assertTrue(run.stderr.startswith('laravel_line: '), run.stderr)


if __name__ == '__main__':
    unittest.main()
