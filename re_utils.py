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
