"""Plugin utility functions"""

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


def make_re(map_string: str, full_match: bool = True) -> str:
    """Convert a string with wildcards '*' and '?' to a regular expression.

    Args:
        map_string (str): String to convert
        full_match (bool, optional): Add the '^' and '$' bookends to the
        regular expression. Defaults to True.

    Returns:
        str: Regular expression.
    """
    re_string = str(map_string)

    # Escape the regular expression special characters
    re_string = re.escape(re_string)

    # Replace the escaped wildcard characters with their regular expression equivalents
    re_string = re_string.replace(r'\*', '.*').replace(r'\?', '.')

    # Clean up any accidental '.*.*' that may have been created by replacing multiple '*' characters
    re_string = re_string.replace('.*.*', '.*')

    # Clean up hard spaces that may have been escaped by re.escape()
    re_string = re_string.replace(r'\ ', ' ')

    # If full_match is True, add the '^' and '$' bookends to the regular expression
    if full_match:
        re_string = '^' + re_string + '$'

    return re_string


def make_replacement_pairs(pairs_string: str, use_regex: bool = False) -> tuple[list[tuple[re.Pattern[str], str]], list[str]]:
    """Convert a string of replacement pairs to a list of tuples.

    Args:
        pairs_string (str): String of replacement pairs.
        use_regex (bool, optional): Use regular expressions for matching. Defaults to False.

    Returns:
        tuple[list[tuple[re.Pattern[str], str]], list[str]]: A tuple containing the list of replacement pairs and a list of invalid regular expressions.
    """
    pairs = []
    errs = []
    for pair in pairs_string.splitlines():
        if '=' in pair:
            match, replacement = pair.split('=', 1)
            match = match.strip()
            replacement = replacement.strip()
            if match and replacement:
                try:
                    re_pattern = re.compile(match if use_regex else make_re(match), re.IGNORECASE)
                    pairs.append((re_pattern, replacement))
                except re.error:
                    errs.append(match)

    return pairs, errs


def map_genre(genre: str, pairs: list[tuple[re.Pattern[str], str]], use_regex: bool = False, first_match_only: bool = False) -> tuple[str, list[str]]:
    """Map a genre string to a new genre string using the provided replacement pairs.

    Args:
        genre (str): Genre string to map.
        pairs (list[tuple[re.Pattern[str], str]]): List of tuples containing the compiled regular expression and the replacement string.
        use_regex (bool, optional): Use regular expressions for matching. Defaults to False.
        first_match_only (bool, optional): Stop after the first match. Defaults to False.

    Returns:
        tuple[str, list[str]]: A tuple containing the mapped genre string and a list of invalid regular expressions encountered.
    """
    errs = []
    for original_re, replacement in pairs:
        try:
            if original_re.search(genre):
                if use_regex:
                    genre = original_re.sub(replacement, genre)
                else:
                    genre = replacement
                if first_match_only:
                    break
        except re.error:
            errs.append(original_re.pattern)

    return genre, errs
