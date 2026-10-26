import unittest

from check11_parse import parse


class ParseTests(unittest.TestCase):
    # Boundaries: missing summary, 0/1 counts, skips, errors, and missing runner.
    def test_phpunit_states_and_counts(self):
        cases = [
            ('OK (1 test, 1 assertion)', 0, 'ok', 1, 1),
            ('OK (2 tests, 3 assertions)', 0, 'ok', 2, 3),
            ('FAILURES!\nTests: 1, Assertions: 1, Failures: 1.', 1, 'assertion', 1, 1),
            ('ERRORS!\nTests: 1, Assertions: 0, Errors: 1.', 2, 'error', 1, 0),
            ('OK, but there were issues!\nTests: 1, Assertions: 0, Skipped: 1.', 0, 'none', 1, 0),
            ('Tests: 2, Assertions: 1, Incomplete: 1.', 1, 'none', 2, 1),
            ('No tests executed!', 0, 'none', 0, 0),
            ('OK (0 tests, 0 assertions)', 0, 'none', 0, 0),
            ('OK (1 test, 0 assertions)', 0, 'none', 1, 0),
            ('cart runner failed', 127, 'unrunnable', 0, 0),
            ('cart runner failed', 126, 'unrunnable', 0, 0),
            ('Could not open input file: cart.php', 1, 'unrunnable', 0, 0),
            ('sh: cart: command not found', 1, 'unrunnable', 0, 0),
            ('No such file or directory', 1, 'unrunnable', 0, 0),
            ('cart not found', 1, 'unrunnable', 0, 0),
            ('PHPUnit 11.0\n1) Cart::test_missing\nClass not found\nERRORS!\n'
             'Tests: 1, Assertions: 0, Errors: 1.', 2, 'error', 1, 0),
            ('Fatal error: cart crashed', 255, 'error', 0, 0),
            ('PHP Parse error: bad cart', 255, 'error', 0, 0),
            ('syntax error: bad cart', 1, 'error', 0, 0),
            ('FAILURES!\nTests: 2, Assertions: 1, Failures: 1, Errors: 1.', 2, 'error', 2, 1),
            ('FAILURES!\nTests: 2, Assertions: 1, Failures: 1, Skipped: 1.', 1, 'none', 2, 1),
            ('FAILURES!\nTests: 1, Assertions: 1, Failures: 0.', 1, 'none', 1, 1),
            ('unrecognised cart output', 0, 'none', 0, 0),
            ('OK (1 test, 1 assertion)', 1, 'none', 1, 1),
        ]
        for text, code, state, tests, assertions in cases:
            with self.subTest(text=text, code=code):
                parsed = parse(text, code)
                self.assertEqual(parsed, dict(state=state, tests=tests,
                                             assertions=assertions, message=''))

    def test_first_failure_message_includes_assertion_line(self):
        text = ('PHPUnit 11.0\n1) Cart::test_total\n/cart/CartTest.php:12\n'
                'Failed asserting that 9 matches expected 8.\n2) Cart::test_tax\n'
                'Failed asserting that 4 matches expected 3.\nFAILURES!\n'
                'Tests: 2, Assertions: 2, Failures: 2.')
        self.assertEqual(parse(text, 1)['message'],
                         'Cart::test_total\nFailed asserting that 9 matches expected 8.')


if __name__ == '__main__':
    unittest.main()
