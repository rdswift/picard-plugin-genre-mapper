# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2025 Bob Swift (rdswift)
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


import re

from picard.metadata import MULTI_VALUED_JOINER
from picard.plugin3.api import (
    OptionsPage,
    PluginApi,
    t_,
)

from .ui_options_genre_mapper import (
    Ui_GenreMapperOptionsPage,
)


USER_GUIDE_URL = 'https://picard-plugins-user-guides.readthedocs.io/en/latest/genre_mapper/user_guide.html'

pairs_split = re.compile(r"\r\n|\n\r|\n").split

OPT_GENRE_SEPARATOR = 'join_genres'
OPT_MATCH_ENABLED = 'genre_mapper_enabled'
OPT_MATCH_PAIRS = 'genre_mapper_replacement_pairs'
OPT_MATCH_FIRST = 'genre_mapper_apply_first_match_only'
OPT_MATCH_REGEX = 'genre_mapper_use_regex'


class GenreMappingPairs:
    pairs = []

    @classmethod
    def set_pairs(cls, new_pairs):
        cls.pairs = new_pairs


class GenreMapper:
    def __init__(self, api: PluginApi):
        self.api = api

    def refresh(self):
        self.api.logger.debug(
            "Refreshing the genre replacement maps processing pairs using '%s' translation.",
            'RegEx' if self.api.plugin_config[OPT_MATCH_REGEX] else 'Simple',
        )
        if self.api.plugin_config[OPT_MATCH_PAIRS] is None:
            self.api.logger.warning("Unable to read the '%s' setting.", OPT_MATCH_PAIRS,)
            return

        def _make_re(map_string):
            # Replace period with temporary placeholder character (newline)
            re_string = str(map_string).strip().replace('.', '\n')

            # Convert wildcard characters to regular expression equivalents
            re_string = re_string.replace('*', '.*').replace('?', '.')

            # Escape carat and dollar sign for regular expression
            re_string = re_string.replace('^', '\\^').replace('$', '\\$')

            # Replace temporary placeholder characters with escaped periods
            re_string = '^' + re_string.replace('\n', '\\.') + '$'

            # Return regular expression with carat and dollar sign to force match condition on full string
            return re_string

        pairs = []
        for pair in pairs_split(self.api.plugin_config[OPT_MATCH_PAIRS]):
            if "=" not in pair:
                continue

            original, replacement = pair.split('=', 1)
            original = original.strip()
            if not original:
                continue

            replacement = replacement.strip()
            pairs.append((original if self.api.plugin_config[OPT_MATCH_REGEX] else _make_re(original), replacement))
            self.api.logger.debug('Add genre mapping pair: "%s" = "%s"', original, replacement,)

        GenreMappingPairs.set_pairs(pairs)

        if not pairs:
            self.api.logger.debug("No genre replacement maps defined.")

    def track_genre_mapper(self, api, album, metadata, *args):
        if not self.api.plugin_config[OPT_MATCH_ENABLED]:
            return

        if 'genre' not in metadata or not metadata['genre']:
            self.api.logger.debug('No genres found for: "%s"', metadata['title'],)
            return

        genre_joiner = self.api.plugin_config[OPT_GENRE_SEPARATOR] if self.api.plugin_config[OPT_GENRE_SEPARATOR] else MULTI_VALUED_JOINER
        genres = set()
        metadata_genres = str(metadata['genre']).split(genre_joiner)
        for genre in metadata_genres:
            for (original, replacement) in GenreMappingPairs.pairs:
                try:
                    if genre and re.search(original, genre, re.IGNORECASE):
                        genre = replacement
                        if self.api.plugin_config[OPT_MATCH_FIRST]:
                            break
                except re.error:
                    self.api.logger.error('Invalid regular expression ignored: "%s"', original,)
            if genre:
                genres.add(genre.title())

        genres = sorted(genres)
        self.api.logger.debug('Genres updated from %s to %s', metadata_genres, genres,)
        metadata['genre'] = genres


class GenreMapperOptionsPage(OptionsPage):

    TITLE = t_("ui.options_page_title", "Genre Mapper")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_GenreMapperOptionsPage()
        self.ui.setupUi(self)
        self._add_translations()

    def _add_translations(self):
        bold_start = '<span style="font-weight:600;">'
        bold_end = '</span>'

        self.ui.gm_description.setTitle(self.api.tr("ui.gm_description", "Genre Mapper"))
        self.ui.format_description.setText(
            "<html><head/><body><p>"
            + self.api.tr(
                "ui.format_description_p1",
                (
                    "These are the original / replacement pairs used to map one genre entry to another. Each pair must be entered on a "
                    "separate line in the form:"
                )
            )
            + "</p><p>"
            + bold_start
            + self.api.tr("ui.format_description_p2", "[genre match test string]=[replacement genre]")
            + bold_end
            + "</p><p>"
            + self.api.tr(
                "ui.format_description_p3",
                (
                    "Unless the \"regular expressions\" option is enabled, supported wildcards in the test string part of the mapping include "
                    "'*' and '?' to match any number of characters and a single character respectively. An example for mapping all types of "
                    "Rock genres (e.g. Country Rock, Hard Rock, Progressive Rock) to \"Rock\" would be done using the following line:"
                )
            )
            + "</p><p>"
            + "<span style=\" font-family:\'Courier New\'; font-size:10pt; font-weight:600;\">"
            + self.api.tr("ui.format_description_p4", "*rock*=Rock")
            + "</span></p><p>"
            + self.api.tr(
                "ui.format_description_p5",
                (
                    "Blank lines and lines beginning with an equals sign (=) will be ignored. Case-insensitive tests are used when matching. "
                    "Replacements will be made in the order they are found in the list."
                )
            )
            + "</p><p>"
            + self.api.tr(
                "ui.format_description_p6",
                "Please see the {start_link}User Guide{end_link} for additional information."
            ).format(start_link=f'<a href="{USER_GUIDE_URL}"><span style="text-decoration: underline; color:#0000ff;">', end_link="</span></a>")
            + "</p></body></html>"
        )
        self.ui.cb_enable_genre_mapping.setText(self.api.tr("ui.cb_enable_genre_mapping", "Enable genre mapping"))
        self.ui.gm_replacement_pairs.setTitle(self.api.tr("ui.gm_replacement_pairs", "Replacement Pairs"))
        self.ui.cb_use_regex.setText(self.api.tr("ui.cb_use_regex", "Match tests are entered as regular expressions"))
        self.ui.genre_mapper_first_match_only.setText(self.api.tr("ui.genre_mapper_first_match_only", "Apply only the first matching replacement"))
        self.ui.genre_mapper_replacement_pairs.setPlaceholderText(self.api.tr("ui.genre_mapper_replacement_pairs", "Enter replacement pairs (one per line)"))

    def load(self):
        # Enable external link
        self.ui.format_description.setOpenExternalLinks(True)

        self.ui.genre_mapper_replacement_pairs.setPlainText(self.api.plugin_config[OPT_MATCH_PAIRS])
        self.ui.genre_mapper_first_match_only.setChecked(self.api.plugin_config[OPT_MATCH_FIRST])
        self.ui.cb_enable_genre_mapping.setChecked(self.api.plugin_config[OPT_MATCH_ENABLED])
        self.ui.cb_use_regex.setChecked(self.api.plugin_config[OPT_MATCH_REGEX])

        self.ui.cb_enable_genre_mapping.stateChanged.connect(self._set_enabled_state)
        self._set_enabled_state()

    def save(self):
        self.api.plugin_config[OPT_MATCH_PAIRS] = self.ui.genre_mapper_replacement_pairs.toPlainText()
        self.api.plugin_config[OPT_MATCH_FIRST] = self.ui.genre_mapper_first_match_only.isChecked()
        self.api.plugin_config[OPT_MATCH_ENABLED] = self.ui.cb_enable_genre_mapping.isChecked()
        self.api.plugin_config[OPT_MATCH_REGEX] = self.ui.cb_use_regex.isChecked()

        GenreMapper(self.api).refresh()

    def _set_enabled_state(self, *args):
        self.ui.gm_replacement_pairs.setEnabled(self.ui.cb_enable_genre_mapping.isChecked())


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    # Register configuration options
    api.plugin_config.register_option(OPT_MATCH_PAIRS, ''),
    api.plugin_config.register_option(OPT_MATCH_FIRST, False),
    api.plugin_config.register_option(OPT_MATCH_ENABLED, False),
    api.plugin_config.register_option(OPT_MATCH_REGEX, False),

    # Migrate settings from 2.x version if available
    migrate_settings(api)

    plugin = GenreMapper(api)
    plugin.refresh()

    api.register_track_metadata_processor(plugin.track_genre_mapper)
    api.register_options_page(GenreMapperOptionsPage)


def migrate_settings(api: PluginApi):
    if api.global_config.setting.raw_value(OPT_MATCH_PAIRS) is None or api.plugin_config[OPT_MATCH_PAIRS]:
        return

    api.logger.info("Migrating settings from 2.x version.")

    mapping = [
        (OPT_MATCH_PAIRS, str),
        (OPT_MATCH_FIRST, bool),
        (OPT_MATCH_ENABLED, bool),
        (OPT_MATCH_REGEX, bool),
    ]

    for key, qtype in mapping:
        if api.global_config.setting.raw_value(key) is None:
            continue
        api.plugin_config[key] = api.global_config.setting.raw_value(key, qtype=qtype)
        api.global_config.setting.remove(key)
