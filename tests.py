#!/usr/bin/env python3
#
# Copyright (C) 2026 Bob Swift (rdswift)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.

import re
import unittest

from utils import (
    make_re,
    make_replacement_pairs,
    map_genre,
)

# Test cases for make_re function: tuples of (input string, expected regular expression)
FULL_MATCH_TEST_CASES = [
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
NO_FULL_MATCH_TEST_CASES = [
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
REGEX_MATCHING_TEST_CASES = [
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

# Test cases for make_re function to verify case-sensitive and case-insensitive matching: tuples of
# (input string, list of strings matching regardless of case, list of strings matching only when ignoring case,
# list of strings that should never match)
CASE_SENSITIVITY_TEST_CASES = [
    ('rock', ['rock'], ['Rock', 'ROCK'], ['roc', 'rocknroll']),
    ('?ock', ['rock', 'sock'], ['rOCK', 'SOCK'], ['roc', 'socks']),
    ('*ock', ['rock', 'sock'], ['rOCK', 'MOCK'], ['roc', 'mockingbird']),
    ('r*ck', ['rock', 'rack'], ['Rock', 'RACK'], ['roc', 'racketeer']),
    ('ro?k', ['rock', 'rook'], ['Rock', 'ROOK'], ['roc', 'rookie']),
    ('ro*', ['rock', 'ro'], ['Rock', 'RO'], ['ra', 'ramadan']),
    ('*ock*', ['rock', 'socket'], ['rOCK', 'SOCKET'], ['racket']),
    ('*o*', ['rock', 'so'], ['rOck', 'SO'], ['r', 'racket']),
    ('rollingstone.de [3/5]', ['rollingstone.de [3/5]'], ['ROLLINGSTONE.DE [3/5]'], ['rollingstone.de [4/5]']),
    ('5+ wochen', ['5+ wochen'], ['5+ WOCHEN'], ['6+ wochen']),
    ('ca$h', ['ca$h'], ['CA$H'], ['cash', 'ca$hflow']),
    ('curly braces {test}', ['curly braces {test}'], ['CURLY BRACES {TEST}'], ['curly braces {test} extra']),
    ('square brackets [test]', ['square brackets [test]'], ['SQUARE BRACKETS [TEST]'], ['square brackets [test] extra']),
    ('parentheses (test)', ['parentheses (test)'], ['PARENTHESES (TEST)'], ['parentheses (test) extra']),
    ('pipe | test', ['pipe | test'], ['PIPE | TEST'], ['pipe | test extra']),
    ('backslash \\ test', ['backslash \\ test'], ['BACKSLASH \\ TEST'], ['backslash \\ test extra']),
]


class TestCreatedReMatching(unittest.TestCase):

    def test_make_re_default_full_match(self):
        """Test that make_re produces the expected regular expression for a variety of input patterns with the default full_match=True."""
        for pattern, string in FULL_MATCH_TEST_CASES:
            re_pattern = make_re(pattern)
            self.assertEqual(re_pattern, string, f"Pattern '{pattern}' did not convert to expected regular expression '{string}'")

    def test_make_re_no_full_match(self):
        """Test that make_re produces the expected regular expression for a variety of input patterns with full_match=False."""
        for pattern, string in NO_FULL_MATCH_TEST_CASES:
            re_pattern = make_re(pattern, full_match=False)
            self.assertEqual(re_pattern, string, f"Pattern '{pattern}' did not convert to expected regular expression '{string}'")

    def test_make_re_full_match(self):
        """Test that make_re produces the expected regular expression for a variety of input patterns with full_match=True."""
        for pattern, string in FULL_MATCH_TEST_CASES:
            re_pattern = make_re(pattern, full_match=True)
            self.assertEqual(re_pattern, string, f"Pattern '{pattern}' did not convert to expected regular expression '{string}'")

    def test_make_re_regex_matching(self):
        """Test that the generated regular expression matches expected strings."""
        for pattern, matching_strings, non_matching_strings in REGEX_MATCHING_TEST_CASES:
            re_pattern = make_re(pattern)
            for string in matching_strings:
                self.assertRegex(string, re_pattern, f"Pattern '{pattern}' did not match expected string '{string}'")

    def test_make_re_regex_non_matching(self):
        """Test that the generated regular expression does not match non-expected strings."""
        for pattern, matching_strings, non_matching_strings in REGEX_MATCHING_TEST_CASES:
            re_pattern = make_re(pattern)
            for string in non_matching_strings:
                self.assertNotRegex(string, re_pattern, f"Pattern '{pattern}' unexpectedly matched string '{string}'")

    def test_make_re_case_sensitive(self):
        """Test that the generated regular expression matches case-sensitively by default."""
        for pattern, matching_strings, case_variant_strings, non_matching_strings in CASE_SENSITIVITY_TEST_CASES:
            re_pattern = make_re(pattern)
            for string in matching_strings:
                self.assertRegex(string, re_pattern, f"Pattern '{pattern}' did not match expected string '{string}'")
            for string in case_variant_strings + non_matching_strings:
                self.assertNotRegex(string, re_pattern, f"Pattern '{pattern}' unexpectedly matched string '{string}'")

    def test_make_re_case_insensitive(self):
        """Test that the generated regular expression matches case-insensitively when re.IGNORECASE is used."""
        for pattern, matching_strings, case_variant_strings, non_matching_strings in CASE_SENSITIVITY_TEST_CASES:
            re_pattern = re.compile(make_re(pattern), re.IGNORECASE)
            for string in matching_strings + case_variant_strings:
                self.assertRegex(string, re_pattern, f"Pattern '{pattern}' did not match expected string '{string}'")
            for string in non_matching_strings:
                self.assertNotRegex(string, re_pattern, f"Pattern '{pattern}' unexpectedly matched string '{string}'")

    def test_make_re_default_arguments(self):
        """Test that make_re uses the default full_match=True when the argument is omitted."""
        self.assertEqual(make_re('rock'), '^rock$')
        self.assertEqual(make_re('rock'), make_re('rock', full_match=True))

    def test_make_re_argument_overrides(self):
        """Test that make_re honours an explicit full_match override."""
        self.assertEqual(make_re('rock', full_match=False), 'rock')
        self.assertNotEqual(make_re('rock', full_match=False), make_re('rock'))
        self.assertEqual(make_re('rock', full_match=True), make_re('rock'))


class TestMakeReplacementPairs(unittest.TestCase):

    def test_make_replacement_pairs(self):
        """Test that make_replacement_pairs produces the expected list of tuples for a variety of input strings."""
        test_cases = [
            ("rock=stone", [(re.compile("^rock$", re.IGNORECASE), "stone")], False, False),
            ("rock=stone\npop=popular", [(re.compile("^rock$", re.IGNORECASE), "stone"), (re.compile("^pop$", re.IGNORECASE), "popular")], False, False),
            ("rock*=Rock\npop*=Pop", [(re.compile("^rock.*$", re.IGNORECASE), "Rock"), (re.compile("^pop.*$", re.IGNORECASE), "Pop")], False, False),
            ("(.*) rock=\\1", [(re.compile("(.*) rock", re.IGNORECASE), "\\1")], True, False),
            ("^(.*) rock$=\\1", [(re.compile("^(.*) rock$", re.IGNORECASE), "\\1")], True, False),
            ("Rock=stone", [(re.compile("^Rock$", re.IGNORECASE), "stone")], False, False),
            ("rock=stone", [(re.compile("^rock$"), "stone")], False, True),
            ("Rock=stone\nPop=popular", [(re.compile("^Rock$"), "stone"), (re.compile("^Pop$"), "popular")], False, True),
            ("rock*=Rock\npop*=Pop", [(re.compile("^rock.*$"), "Rock"), (re.compile("^pop.*$"), "Pop")], False, True),
            ("(.*) Rock=\\1", [(re.compile("(.*) Rock"), "\\1")], True, True),
            ("^(.*) Rock$=\\1", [(re.compile("^(.*) Rock$"), "\\1")], True, True),
        ]

        for pairs_string, expected, use_regex, case_sensitive in test_cases:
            result, errs = make_replacement_pairs(pairs_string, use_regex=use_regex, case_sensitive=case_sensitive)
            self.assertEqual(result, expected, f"Input '{pairs_string}' did not produce expected output '{expected}'")
            self.assertEqual(errs, [], f"Input '{pairs_string}' produced unexpected errors '{errs}'")

    def test_make_replacement_pairs_invalid_regex(self):
        """Test that make_replacement_pairs returns the expected list of invalid regular expressions for a variety of input strings."""
        test_cases = [
            ("(.*) rock=\\1\n(=invalid", [(re.compile("(.*) rock", re.IGNORECASE), "\\1")], ["("], True, False),
            ("^(.*) rock$=\\1\n(=invalid", [(re.compile("^(.*) rock$", re.IGNORECASE), "\\1")], ["("], True, False),
            ("^(.*) rock$=\\1\nfoo$=bar\n(=invalid", [(re.compile("^(.*) rock$", re.IGNORECASE), "\\1"), (re.compile("foo$", re.IGNORECASE), "bar")], ["("], True, False),
            ("(.*) Rock=\\1\n(=invalid", [(re.compile("(.*) Rock"), "\\1")], ["("], True, True),
            ("^(.*) Rock$=\\1\n(=invalid", [(re.compile("^(.*) Rock$"), "\\1")], ["("], True, True),
            ("^(.*) Rock$=\\1\nfoo$=bar\n(=invalid", [(re.compile("^(.*) Rock$"), "\\1"), (re.compile("foo$"), "bar")], ["("], True, True),
        ]

        for pairs_string, expected_pairs, expected_errs, use_regex, case_sensitive in test_cases:
            result_pairs, result_errs = make_replacement_pairs(pairs_string, use_regex=use_regex, case_sensitive=case_sensitive)
            self.assertEqual(result_pairs, expected_pairs, f"Input '{pairs_string}' did not produce expected output '{expected_pairs}'")
            self.assertEqual(result_errs, expected_errs, f"Input '{pairs_string}' did not produce expected errors '{expected_errs}'")

    def test_make_replacement_pairs_default_arguments(self):
        """Test that make_replacement_pairs uses use_regex=False and case_sensitive=False when the arguments are omitted."""
        pairs_string = "rock=stone\npop=popular"
        expected = [(re.compile("^rock$", re.IGNORECASE), "stone"), (re.compile("^pop$", re.IGNORECASE), "popular")]

        result, errs = make_replacement_pairs(pairs_string)
        self.assertEqual(result, expected, f"Input '{pairs_string}' did not use the expected default arguments")
        self.assertEqual(errs, [], f"Input '{pairs_string}' produced unexpected errors '{errs}'")
        self.assertEqual(result, make_replacement_pairs(pairs_string, use_regex=False, case_sensitive=False)[0])

    def test_make_replacement_pairs_argument_overrides(self):
        """Test that make_replacement_pairs honours explicit use_regex and case_sensitive overrides."""
        result, errs = make_replacement_pairs("(.*) rock=\\1", use_regex=True)
        self.assertEqual(result, [(re.compile("(.*) rock", re.IGNORECASE), "\\1")])
        self.assertEqual(errs, [])

        result, errs = make_replacement_pairs("rock=stone", case_sensitive=True)
        self.assertEqual(result, [(re.compile("^rock$"), "stone")])
        self.assertEqual(errs, [])

        result, errs = make_replacement_pairs("(.*) Rock=\\1", use_regex=True, case_sensitive=True)
        self.assertEqual(result, [(re.compile("(.*) Rock"), "\\1")])
        self.assertEqual(errs, [])


class TestMapGenre(unittest.TestCase):

    def test_map_genre(self):
        """Test that map_genre produces the expected output for a variety of input strings."""
        test_cases = [
            ("rock", [(re.compile("^rock$", re.IGNORECASE), "stone")], False, False, ("stone", [])),
            ("rock", [(re.compile("^rock$"), "stone"), (re.compile("^pop$"), "popular")], False, False, ("stone", [])),
            ("pop", [(re.compile("^rock$"), "stone"), (re.compile("^pop$"), "popular")], False, False, ("popular", [])),
            ("rock", [(re.compile("^rock.*$"), "Rock"), (re.compile("^pop.*$"), "Pop")], False, False, ("Rock", [])),
            ("pop", [(re.compile("^rock.*$"), "Rock"), (re.compile("^pop.*$"), "Pop")], False, False, ("Pop", [])),
            ("hard rock", [(re.compile("(.*) rock"), "\\1")], True, False, ("hard", [])),
            ("hard rock", [(re.compile("(.*) rock"), "rock (\\1)")], True, False, ("rock (hard)", [])),
            ("soft rock", [(re.compile("(.*) rock"), "\\1")], True, True, ("soft", [])),
            ("hard rock", [(re.compile("(.*) rock"), "\\1"), (re.compile("(.*) pop"), "\\1")], True, False, ("hard", [])),
            ("soft pop", [(re.compile("(.*) rock"), "\\1"), (re.compile("(.*) pop"), "\\1")], True, False, ("soft", [])),
            ("soft pop", [(re.compile("(.*) rock"), "\\1"), (re.compile("(.*) pop"), "\\1")], True, True, ("soft", [])),
        ]

        for genre, pairs, use_regex, first_match_only, expected in test_cases:
            result = map_genre(genre, pairs, use_regex=use_regex, first_match_only=first_match_only)
            self.assertEqual(result, expected, f"Input '{genre}' with pairs '{pairs}' did not produce expected output '{expected}'")

    def test_map_genre_case_sensitive(self):
        """Test that map_genre matches case-sensitively when the pair patterns are compiled without re.IGNORECASE."""
        test_cases = [
            ("rock", [(re.compile("^rock$"), "stone")], False, False, ("stone", [])),
            ("Rock", [(re.compile("^rock$"), "stone")], False, False, ("Rock", [])),
            ("ROCK", [(re.compile("^rock$"), "stone")], False, False, ("ROCK", [])),
            ("hard rock", [(re.compile("(.*) rock"), "\\1")], True, False, ("hard", [])),
            ("Hard Rock", [(re.compile("(.*) rock"), "\\1")], True, False, ("Hard Rock", [])),
            ("soft pop", [(re.compile("(.*) rock"), "\\1"), (re.compile("(.*) pop"), "\\1")], True, True, ("soft", [])),
            ("Soft Pop", [(re.compile("(.*) rock"), "\\1"), (re.compile("(.*) pop"), "\\1")], True, True, ("Soft Pop", [])),
        ]

        for genre, pairs, use_regex, first_match_only, expected in test_cases:
            result = map_genre(genre, pairs, use_regex=use_regex, first_match_only=first_match_only)
            self.assertEqual(result, expected, f"Input '{genre}' with pairs '{pairs}' did not produce expected output '{expected}'")

    def test_map_genre_case_insensitive(self):
        """Test that map_genre matches case-insensitively when the pair patterns are compiled with re.IGNORECASE."""
        test_cases = [
            ("rock", [(re.compile("^rock$", re.IGNORECASE), "stone")], False, False, ("stone", [])),
            ("Rock", [(re.compile("^rock$", re.IGNORECASE), "stone")], False, False, ("stone", [])),
            ("ROCK", [(re.compile("^rock$", re.IGNORECASE), "stone")], False, False, ("stone", [])),
            ("hard rock", [(re.compile("(.*) rock", re.IGNORECASE), "\\1")], True, False, ("hard", [])),
            ("Hard Rock", [(re.compile("(.*) rock", re.IGNORECASE), "\\1")], True, False, ("Hard", [])),
            ("soft pop", [(re.compile("(.*) rock", re.IGNORECASE), "\\1"), (re.compile("(.*) pop", re.IGNORECASE), "\\1")], True, True, ("soft", [])),
            ("Soft Pop", [(re.compile("(.*) rock", re.IGNORECASE), "\\1"), (re.compile("(.*) pop", re.IGNORECASE), "\\1")], True, True, ("Soft", [])),
        ]

        for genre, pairs, use_regex, first_match_only, expected in test_cases:
            result = map_genre(genre, pairs, use_regex=use_regex, first_match_only=first_match_only)
            self.assertEqual(result, expected, f"Input '{genre}' with pairs '{pairs}' did not produce expected output '{expected}'")

    def test_map_genre_default_arguments(self):
        """Test that map_genre uses use_regex=False and first_match_only=False when the arguments are omitted."""
        pairs = [(re.compile("^rock$", re.IGNORECASE), "stone"), (re.compile("^stone$", re.IGNORECASE), "pebble")]

        self.assertEqual(map_genre("rock", pairs), ("pebble", []))
        self.assertEqual(map_genre("rock", pairs), map_genre("rock", pairs, use_regex=False, first_match_only=False))

    def test_map_genre_argument_overrides(self):
        """Test that map_genre honours explicit use_regex and first_match_only overrides."""
        pairs = [(re.compile("(.*) rock"), "\\1")]
        self.assertEqual(map_genre("hard rock", pairs), ("\\1", []))
        self.assertEqual(map_genre("hard rock", pairs, use_regex=True), ("hard", []))

        pairs = [(re.compile("^rock$", re.IGNORECASE), "stone"), (re.compile("^stone$", re.IGNORECASE), "pebble")]
        self.assertEqual(map_genre("rock", pairs), ("pebble", []))
        self.assertEqual(map_genre("rock", pairs, first_match_only=True), ("stone", []))


# Run the tests
if __name__ == '__main__':
    unittest.main()
