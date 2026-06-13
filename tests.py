#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Bob Swift (rdswift)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import unittest

from re_utils import make_re

# Test cases for make_re function: tuples of (input string, expected regular expression)
_FULL_MATCH_TEST_CASES = [
    ('rock', '^rock$'),
    ('?ock', '^.ock$'),
    ('*ock', '^.*ock$'),
    ('r*ck', '^r.*ck$'),
    ('ro?k', '^ro.k$'),
    ('ro*', '^ro.*$'),
    ('*ock*', '^.*ock.*$'),
    ('*o*', '^.*o.*$'),
    ('rollingstone.de [3/5]', '^rollingstone\\.de \\[3/5\\]$'),
    ('5+ wochen', '^5\\+ wochen$'),
    ('ca$h', '^ca\\$h$'),
    ('curly braces {test}', '^curly braces \\{test\\}$'),
    ('square brackets [test]', '^square brackets \\[test\\]$'),
    ('parentheses (test)', '^parentheses \\(test\\)$'),
    ('pipe | test', '^pipe \\| test$'),
    ('backslash \\ test', '^backslash \\\\ test$'),
]

# Test cases for make_re function with full_match=False: tuples of (input string, expected regular expression)
_NO_FULL_MATCH_TEST_CASES = [
    ('rock', 'rock'),
    ('?ock', '.ock'),
    ('*ock', '.*ock'),
    ('r*ck', 'r.*ck'),
    ('ro?k', 'ro.k'),
    ('ro*', 'ro.*'),
    ('*ock*', '.*ock.*'),
    ('*o*', '.*o.*'),
    ('rollingstone.de [3/5]', 'rollingstone\\.de \\[3/5\\]'),
    ('5+ wochen', '5\\+ wochen'),
    ('ca$h', 'ca\\$h'),
    ('curly braces {test}', 'curly braces \\{test\\}'),
    ('square brackets [test]', 'square brackets \\[test\\]'),
    ('parentheses (test)', 'parentheses \\(test\\)'),
    ('pipe | test', 'pipe \\| test'),
    ('backslash \\ test', 'backslash \\\\ test'),
]

# Test cases for make_re function to verify that the generated regular expression matches expected strings and does
# not match non-expected strings: tuples of (input string, list of matching strings, list of non-matching strings)
_REGEX_MATCHING_TEST_CASES = [
    ('rock', ['rock'], ['roc', 'rocknroll']),
    ('?ock', ['rock', 'sock'], ['roc', 'rocknroll', 'socks']),
    ('*ock', ['rock', 'sock', 'mock'], ['roc', 'rocknroll', 'socks', 'mockingbird']),
    ('r*ck', ['rock', 'rack', 'rck', 'roock'], ['roc', 'rocknroll', 'racketeer']),
    ('ro?k', ['rock', 'rook'], ['roc', 'rocknroll', 'rookie']),
    ('ro*', ['rock', 'ro'], ['ra', 'ramadan']),
    ('*ock*', ['rock', 'socket'], ['racket']),
    ('*o*', ['rock', 'so'], ['r', 'racket']),
    ('rollingstone.de [3/5]', ['rollingstone.de [3/5]'], ['rollingstone.de [4/5]']),
    ('5+ wochen', ['5+ wochen'], ['6+ wochen']),
    ('ca$h', ['ca$h'], ['cash', 'ca$hflow']),
    ('curly braces {test}', ['curly braces {test}'], ['curly braces {test} extra']),
    ('square brackets [test]', ['square brackets [test]'], ['square brackets [test] extra']),
    ('parentheses (test)', ['parentheses (test)'], ['parentheses (test) extra']),
    ('pipe | test', ['pipe | test'], ['pipe | test extra']),
    ('backslash \\ test', ['backslash \\ test'], ['backslash \\ test extra']),
]


class TestCreatedReMatching(unittest.TestCase):

    def test_make_re_default_full_match(self):
        """Test that make_re produces the expected regular expression for a variety of input patterns with the default full_match=True."""
        for pattern, string in _FULL_MATCH_TEST_CASES:
            re_pattern = make_re(pattern)
            self.assertEqual(re_pattern, string, f"Pattern '{pattern}' did not convert to expected regular expression '{string}'")

    def test_make_re_no_full_match(self):
        """Test that make_re produces the expected regular expression for a variety of input patterns with full_match=False."""
        for pattern, string in _NO_FULL_MATCH_TEST_CASES:
            re_pattern = make_re(pattern, full_match=False)
            self.assertEqual(re_pattern, string, f"Pattern '{pattern}' did not convert to expected regular expression '{string}'")

    def test_make_re_full_match(self):
        """Test that make_re produces the expected regular expression for a variety of input patterns with full_match=True."""
        for pattern, string in _FULL_MATCH_TEST_CASES:
            re_pattern = make_re(pattern, full_match=True)
            self.assertEqual(re_pattern, string, f"Pattern '{pattern}' did not convert to expected regular expression '{string}'")

    def test_make_re_regex_matching(self):
        """Test that the generated regular expression matches expected strings."""
        for pattern, matching_strings, non_matching_strings in _REGEX_MATCHING_TEST_CASES:
            re_pattern = make_re(pattern)
            for string in matching_strings:
                self.assertRegex(string, re_pattern, f"Pattern '{pattern}' did not match expected string '{string}'")

    def test_make_re_regex_non_matching(self):
        """Test that the generated regular expression does not match non-expected strings."""
        for pattern, matching_strings, non_matching_strings in _REGEX_MATCHING_TEST_CASES:
            re_pattern = make_re(pattern)
            for string in non_matching_strings:
                self.assertNotRegex(string, re_pattern, f"Pattern '{pattern}' unexpectedly matched string '{string}'")


# Run the tests
if __name__ == '__main__':
    unittest.main()
