#
# Copyright (C) 2022-2026 Bob Swift (rdswift)
# Copyright (C) 2026 joshinils
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

from picard.debug_opts import DebugOpt
from picard.metadata import MULTI_VALUED_JOINER
from picard.plugin3.api import (
    OptionsPage,
    PluginApi,
    t_,
)

from .ui_options_genre_mapper import (
    Ui_GenreMapperOptionsPage,
)
from .utils import (
    # make_re,
    make_replacement_pairs,
    map_genre,
)

USER_GUIDE_URL = 'https://picard-plugins-user-guides.readthedocs.io/en/latest/genre_mapper/user_guide.html'

pairs_split = re.compile(r"\r\n|\n\r|\n").split

OPT_GENRE_SEPARATOR = 'join_genres'
OPT_MATCH_ENABLED = 'genre_mapper_enabled'
OPT_MATCH_PAIRS = 'genre_mapper_replacement_pairs'
OPT_MATCH_FIRST = 'genre_mapper_apply_first_match_only'
OPT_MATCH_REGEX = 'genre_mapper_use_regex'


# Hold the compiled pairs in a class variable so they can be accessed independently from all instances of the
# GenreMapper class. This allows the pairs to be shared across both the plugin and the option settings screen,
# and ensures that they are only compiled once when the option settings are saved, improving performance.
class GenreMapperPairs:
    pairs: list[tuple[re.Pattern[str], str]] = []

    # @classmethod
    # def set_pairs(cls, new_pairs: list[tuple[re.Pattern[str], str]]) -> None:
    #     cls.pairs = new_pairs


class GenreMapper:
    def __init__(self, api: PluginApi):
        self.api = api

    def refresh(self):
        self.api.logger.debug(
            "Refreshing the genre replacement maps processing pairs using '%s' translation.",
            'RegEx' if self.api.plugin_config[OPT_MATCH_REGEX] else 'Simple',
        )
        pairs_string = self.api.plugin_config[OPT_MATCH_PAIRS]
        if pairs_string is None:
            self.api.logger.warning("Unable to read the '%s' setting.", OPT_MATCH_PAIRS,)
            return

        GenreMapperPairs.pairs, errs = make_replacement_pairs(pairs_string, use_regex=self.api.plugin_config[OPT_MATCH_REGEX])

        for err in errs:
            self.api.logger.error('Invalid regular expression ignored: "%s"', err,)

        if not GenreMapperPairs.pairs:
            self.api.logger.debug("No genre replacement maps defined.")
            return

        for original_re, replacement in GenreMapperPairs.pairs:
            self.api.logger.debug_if(DebugOpt.PLUGIN_DEVELOPMENT, 'Add genre mapping pair: "%s" = "%s"', original_re.pattern, replacement,)

        # pairs: list[tuple[re.Pattern[str], str]] = []
        # for pair in pairs_split(self.api.plugin_config[OPT_MATCH_PAIRS]):
        #     if "=" not in pair:
        #         continue

        #     original, replacement = pair.split('=', 1)
        #     original = original.strip()
        #     if not original:
        #         continue

        #     replacement = replacement.strip()
        #     pairs.append(
        #         (
        #             re.compile(
        #                 original if self.api.plugin_config[OPT_MATCH_REGEX] else make_re(original),
        #                 flags=re.IGNORECASE
        #             ),
        #             replacement
        #         )
        #     )
        #     self.api.logger.debug_if(DebugOpt.PLUGIN_DEVELOPMENT, 'Add genre mapping pair: "%s" = "%s"', original, replacement,)

        # GenreMapperPairs.pairs = pairs

    def track_genre_mapper(self, api, album, metadata, *args):
        if not self.api.plugin_config[OPT_MATCH_ENABLED]:
            return

        if 'genre' not in metadata or not metadata['genre']:
            self.api.logger.debug('No genres found for: "%s"', metadata['title'],)
            return

        genre_joiner = self.api.global_config.setting[OPT_GENRE_SEPARATOR] if self.api.global_config.setting[OPT_GENRE_SEPARATOR] else MULTI_VALUED_JOINER
        self.api.logger.debug("Using '%s' as the genre separator.", genre_joiner,)

        use_regex = self.api.plugin_config[OPT_MATCH_REGEX]
        match_first_only = self.api.plugin_config[OPT_MATCH_FIRST]

        genres = set()


        print(f"\n\nOriginal metadata genres: '{metadata['genre']}'")  # Debugging print statement


        metadata_genres = str(metadata['genre']).split(genre_joiner)
        for genre in metadata_genres:
            new_genre, errs = map_genre(genre, GenreMapperPairs.pairs, use_regex, match_first_only)
            # for (original_re, replacement) in GenreMapperPairs.pairs:
            #     try:
            #         if genre and original_re.search(genre):
            #             if self.api.plugin_config[OPT_MATCH_REGEX]:
            #                 genre = original_re.sub(replacement, genre)
            #             else:
            #                 genre = replacement
            #             if self.api.plugin_config[OPT_MATCH_FIRST]:
            #                 break
            #     except re.error:
            #         self.api.logger.error('Invalid regular expression ignored: "%s"', original_re.pattern,)
            for err in errs:
                self.api.logger.error('Invalid regular expression ignored: "%s"', err,)


            print(f"  - Original genre: '{genre}', Mapped genre: '{new_genre}'")  # Debugging print statement


            if new_genre:
                genres.add(new_genre.title())

        genres = sorted(genres)
        self.api.logger.debug('Genres updated from %s to %s', metadata_genres, genres,)
        metadata['genre'] = genres


        print('\n')  # Debugging print statement



class GenreMapperOptionsPage(OptionsPage):

    TITLE = t_("ui.options_page_title", "Genre Mapper")
    HELP_URL = USER_GUIDE_URL

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_GenreMapperOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.genre_mapper_replacement_pairs.setPlainText(self.api.plugin_config[OPT_MATCH_PAIRS])
        self.ui.genre_mapper_first_match_only.setChecked(self.api.plugin_config[OPT_MATCH_FIRST])
        self.ui.cb_enable_genre_mapping.setChecked(self.api.plugin_config[OPT_MATCH_ENABLED])
        self.ui.cb_use_regex.setChecked(self.api.plugin_config[OPT_MATCH_REGEX])

    def save(self):
        self.api.plugin_config[OPT_MATCH_PAIRS] = self.ui.genre_mapper_replacement_pairs.toPlainText()
        self.api.plugin_config[OPT_MATCH_FIRST] = self.ui.genre_mapper_first_match_only.isChecked()
        self.api.plugin_config[OPT_MATCH_ENABLED] = self.ui.cb_enable_genre_mapping.isChecked()
        self.api.plugin_config[OPT_MATCH_REGEX] = self.ui.cb_use_regex.isChecked()

        GenreMapper(self.api).refresh()


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
