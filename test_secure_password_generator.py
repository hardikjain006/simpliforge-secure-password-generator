"""Public-behavior tests for the secure-password-generator command.

These tests exercise only the public CLI contract (arguments, standard
output, standard error, exit status, password length, and alphabet
membership). They do not import implementation internals.
"""

import os
import subprocess
import sys
import unittest

CMD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "secure-password-generator")

ALPHABET = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "!@#$%^&*()-_=+"
)


def run(args, stdin_data=None):
    return subprocess.run(
        [sys.executable, CMD] + args,
        input=stdin_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )


def assert_success(testcase, proc, expected_length):
    testcase.assertEqual(proc.returncode, 0)
    testcase.assertEqual(proc.stderr, b"")
    testcase.assertTrue(proc.stdout.endswith(b"\n"))
    testcase.assertEqual(proc.stdout.count(b"\n"), 1)
    password = proc.stdout[:-1].decode("utf-8")
    testcase.assertEqual(len(password), expected_length)
    for ch in password:
        testcase.assertIn(ch, ALPHABET)


def assert_error(testcase, proc):
    testcase.assertEqual(proc.returncode, 2)
    testcase.assertEqual(proc.stdout, b"")
    testcase.assertTrue(proc.stderr.endswith(b"\n"))
    testcase.assertEqual(proc.stderr.count(b"\n"), 1)
    testcase.assertGreater(len(proc.stderr[:-1]), 0)
    testcase.assertNotIn(b"usage:", proc.stderr.lower())


class TestSuccess(unittest.TestCase):
    def test_default_length_is_16(self):
        assert_success(self, run([]), 16)

    def test_minimum_length_8(self):
        assert_success(self, run(["--length", "8"]), 8)

    def test_maximum_length_128(self):
        assert_success(self, run(["--length", "128"]), 128)

    def test_leading_zeros_decimal(self):
        assert_success(self, run(["--length", "016"]), 16)

    def test_mid_range_length(self):
        assert_success(self, run(["--length", "32"]), 32)

    def test_alphabet_membership_various_lengths(self):
        for n in (8, 16, 32, 128):
            with self.subTest(n=n):
                assert_success(self, run(["--length", str(n)]), n)

    def test_stdin_is_ignored(self):
        assert_success(self, run([], stdin_data=b"ignored input\n"), 16)

    def test_password_is_not_empty_line(self):
        proc = run([])
        assert_success(self, proc, 16)
        self.assertNotEqual(proc.stdout, b"\n")


class TestHelp(unittest.TestCase):
    def assert_help(self, proc):
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, b"")
        text = proc.stdout.decode("utf-8")
        lowered = text.lower()
        self.assertIn("secure", lowered)
        self.assertIn("password", lowered)
        self.assertIn("--length", text)
        self.assertIn("16", text)
        self.assertIn("8", text)
        self.assertIn("128", text)
        self.assertIn("standard output", lowered)
        self.assertIn("secure-password-generator", text)
        self.assertGreaterEqual(text.count("\n"), 1)

    def test_short_help(self):
        self.assert_help(run(["-h"]))

    def test_long_help(self):
        self.assert_help(run(["--help"]))

    def test_help_precedence_after_length(self):
        self.assert_help(run(["--length", "16", "--help"]))

    def test_help_precedence_before_length(self):
        self.assert_help(run(["--help", "--length", "16"]))

    def test_help_ignores_invalid_length(self):
        self.assert_help(run(["--help", "--length", "abc"]))

    def test_help_generates_no_password(self):
        proc = run(["--help"])
        self.assert_help(proc)


class TestErrors(unittest.TestCase):
    def test_out_of_range(self):
        for value in ("7", "129", "-5"):
            with self.subTest(value=value):
                proc = run(["--length", value])
                assert_error(self, proc)
                text = proc.stderr.decode("utf-8").lower()
                self.assertIn("out-of-range", text)
                self.assertIn("8", text)
                self.assertIn("128", text)

    def test_non_integer(self):
        for value in ("abc", "12.5", "+16", "", " 16", "--foo"):
            with self.subTest(value=value):
                proc = run(["--length", value])
                assert_error(self, proc)
                self.assertIn("non-integer",
                              proc.stderr.decode("utf-8").lower())

    def test_missing_value(self):
        proc = run(["--length"])
        assert_error(self, proc)
        self.assertIn("missing value",
                      proc.stderr.decode("utf-8").lower())

    def test_repeated_length(self):
        proc = run(["--length", "8", "--length", "16"])
        assert_error(self, proc)
        self.assertIn("more than once",
                      proc.stderr.decode("utf-8").lower())

    def test_equals_form_rejected(self):
        proc = run(["--length=16"])
        assert_error(self, proc)
        self.assertIn("unknown option",
                      proc.stderr.decode("utf-8").lower())

    def test_length_consumes_flag_like_value(self):
        proc = run(["--length", "--foo"])
        assert_error(self, proc)
        self.assertIn("non-integer",
                      proc.stderr.decode("utf-8").lower())

    def test_length_consumes_help_as_value(self):
        proc = run(["--length", "--help"])
        assert_error(self, proc)
        self.assertIn("non-integer",
                      proc.stderr.decode("utf-8").lower())
        self.assertEqual(proc.stdout, b"")

    def test_unknown_option(self):
        proc = run(["--foo"])
        assert_error(self, proc)
        self.assertIn("unknown option",
                      proc.stderr.decode("utf-8").lower())

    def test_extra_positional(self):
        proc = run(["extra"])
        assert_error(self, proc)
        text = proc.stderr.decode("utf-8").lower()
        self.assertIn("unknown", text)

    def test_extra_positional_after_valid_length(self):
        proc = run(["--length", "16", "extra"])
        assert_error(self, proc)

    def test_unknown_after_valid_length(self):
        proc = run(["--length", "16", "--foo"])
        assert_error(self, proc)
        self.assertIn("unknown option",
                      proc.stderr.decode("utf-8").lower())

    def test_error_stdout_empty_and_single_line(self):
        for args in (["--foo"], ["extra"], ["--length"],
                     ["--length", "abc"], ["--length", "7"],
                     ["--length", "8", "--length", "16"],
                     ["--length=16"], ["--length", "--help"]):
            with self.subTest(args=args):
                proc = run(args)
                assert_error(self, proc)


if __name__ == "__main__":
    unittest.main()
