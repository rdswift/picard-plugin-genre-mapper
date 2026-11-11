"""Genre Mapper Plugin for MusicBrainz Picard"""

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
    make_replacement_pairs,
    map_genre,
)

USER_GUIDE_URL = 'https://picard-plugins-user-guides.readthedocs.io/en/latest/genre_mapper/user_guide.html'

OPT_GENRE_SEPARATOR = 'join_genres'
OPT_MATCH_ENABLED = 'genre_mapper_enabled'
OPT_MATCH_PAIRS = 'genre_mapper_replacement_pairs'
OPT_MATCH_FIRST = 'genre_mapper_apply_first_match_only'
OPT_MATCH_REGEX = 'genre_mapper_use_regex'
OPT_MATCH_CASE_SENSITIVE = 'genre_mapper_case_sensitive'
OPT_VERBOSE_DEBUG_LOGGING = 'genre_mapper_verbose_logging'


# Hold the compiled pairs in a class variable so they can be accessed independently from all
# instances of the `GenreMapper` class.  This allows the pairs to be shared between both the
# plugin and the option settings screen.
class GenreMapperPairs:
    """Genre Mapping Pairs"""

    pairs: list[tuple[re.Pattern[str], str]] = []


class GenreMapper:
    """Genre Mapper Plugin"""

    verbose_logging: bool = False

    def __init__(self, api: PluginApi):
        self.api = api

    @classmethod
    def set_verbose_logging(cls, enabled: bool):
        """Set the verbose logging flag for the plugin."""
        cls.verbose_logging = enabled

    def log_verbose(self, message: str, *args):
        """Log a message to the Picard log if verbose logging is enabled."""
        if self.verbose_logging:
            self.api.logger.debug(message, *args)

    def refresh(self):
        """Refresh the genre mapping pairs from the option settings.
        """
        self.set_verbose_logging(self.api.plugin_config[OPT_VERBOSE_DEBUG_LOGGING])
        self.api.logger.debug(
            "Refreshing the genre replacement maps processing pairs using '%s' translation.",
            'RegEx' if self.api.plugin_config[OPT_MATCH_REGEX] else 'Simple',
        )
        pairs_string = self.api.plugin_config[OPT_MATCH_PAIRS]
        if pairs_string is None:
            self.api.logger.warning("Unable to read the '%s' setting.", OPT_MATCH_PAIRS,)
            return

        case_sensitive = self.api.plugin_config[OPT_MATCH_CASE_SENSITIVE]

        GenreMapperPairs.pairs, errs = make_replacement_pairs(
            pairs_string,
            use_regex=self.api.plugin_config[OPT_MATCH_REGEX],
            case_sensitive=case_sensitive,
        )

        for err in errs:
            self.api.logger.error('Invalid regular expression ignored: "%s"', err,)

        if not GenreMapperPairs.pairs:
            self.api.logger.debug("No genre replacement maps defined.")
            return

        for original_re, replacement in GenreMapperPairs.pairs:
            self.log_verbose('Compiled genre replacement map: "%s" => "%s" (case-%ssensitive)',
                             original_re.pattern, replacement, "" if case_sensitive else "in")

    def track_genre_mapper(self, api, album, metadata, *args):
        if not self.api.plugin_config[OPT_MATCH_ENABLED]:
            return

        if 'genre' not in metadata or not metadata['genre']:
            self.api.logger.debug('No genres found for: "%s"', metadata['title'],)
            return

        genre_joiner = self.api.global_config.setting[OPT_GENRE_SEPARATOR]
        if not genre_joiner:
            genre_joiner = MULTI_VALUED_JOINER

        use_regex = self.api.plugin_config[OPT_MATCH_REGEX]
        match_first_only = self.api.plugin_config[OPT_MATCH_FIRST]

        self.log_verbose("Using '%s' as the genre separator.", genre_joiner,)

        genres = set()
        metadata_genres = str(metadata['genre']).split(genre_joiner)

        self.log_verbose("Original metadata genres: '%s'", metadata_genres,)

        for genre in metadata_genres:
            new_genre, errs = map_genre(genre, GenreMapperPairs.pairs, use_regex, match_first_only)
            for err in errs:
                self.api.logger.error('Invalid regular expression ignored: "%s"', err,)

            self.log_verbose("Original genre: '%s'  ==>  Mapped genre: '%s'", genre, new_genre)

            if new_genre:
                genres.add(new_genre.title())

        genres = sorted(genres)
        self.api.logger.debug('Genres updated from %s to %s', metadata_genres, genres,)
        metadata['genre'] = genres


class GenreMapperOptionsPage(OptionsPage):

    TITLE = t_("ui.options_page_title", "Genre Mapper")
    OPTIONS = {
        OPT_MATCH_ENABLED: {'widgets': ['cb_enable_genre_mapping']},
        OPT_MATCH_PAIRS: {'widgets': ['genre_mapper_replacement_pairs']},
        OPT_MATCH_FIRST: {'widgets': ['cb_first_match_only']},
        OPT_MATCH_REGEX: {'widgets': ['cb_use_regex']},
        OPT_MATCH_CASE_SENSITIVE: {'widgets': ['cb_case_sensitive']},
        OPT_VERBOSE_DEBUG_LOGGING: {'widgets': ['cb_verbose_logging']},
    }
    HELP_URL = USER_GUIDE_URL

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_GenreMapperOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.genre_mapper_replacement_pairs.setPlainText(self.api.plugin_config[OPT_MATCH_PAIRS])
        self.ui.cb_first_match_only.setChecked(self.api.plugin_config[OPT_MATCH_FIRST])
        self.ui.cb_enable_genre_mapping.setChecked(self.api.plugin_config[OPT_MATCH_ENABLED])
        self.ui.cb_use_regex.setChecked(self.api.plugin_config[OPT_MATCH_REGEX])
        self.ui.cb_case_sensitive.setChecked(self.api.plugin_config[OPT_MATCH_CASE_SENSITIVE])
        self.ui.cb_verbose_logging.setChecked(self.api.plugin_config[OPT_VERBOSE_DEBUG_LOGGING])

    def save(self):
        self.api.plugin_config[OPT_MATCH_PAIRS] = self.ui.genre_mapper_replacement_pairs.toPlainText()
        self.api.plugin_config[OPT_MATCH_FIRST] = self.ui.cb_first_match_only.isChecked()
        self.api.plugin_config[OPT_MATCH_ENABLED] = self.ui.cb_enable_genre_mapping.isChecked()
        self.api.plugin_config[OPT_MATCH_REGEX] = self.ui.cb_use_regex.isChecked()
        self.api.plugin_config[OPT_MATCH_CASE_SENSITIVE] = self.ui.cb_case_sensitive.isChecked()
        self.api.plugin_config[OPT_VERBOSE_DEBUG_LOGGING] = self.ui.cb_verbose_logging.isChecked()

        GenreMapper(self.api).refresh()


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    # Register configuration options
    api.plugin_config.register_option(
        OPT_MATCH_PAIRS,
        '',
        title=api.tr('ui.option.title.match_pairs', "Match pairs"),
        in_profile=True,
    ),

    api.plugin_config.register_option(
        OPT_MATCH_FIRST,
        False,
        title=api.tr('ui.option.title.match_first', "Match first only"),
        in_profile=True,
    ),

    api.plugin_config.register_option(
        OPT_MATCH_ENABLED,
        False,
        title=api.tr('ui.option.title.match_enabled', "Mapping enabled"),
        in_profile=True,
    ),

    api.plugin_config.register_option(
        OPT_MATCH_REGEX,
        False,
        title=api.tr('ui.option.title.match_regex', "Use regular expressions"),
        in_profile=True,
    ),

    api.plugin_config.register_option(
        OPT_MATCH_CASE_SENSITIVE,
        False,
        title=api.tr('ui.option.title.match_case_sensitive', "Case-sensitive matching"),
        in_profile=True,
    ),

    api.plugin_config.register_option(
        OPT_VERBOSE_DEBUG_LOGGING,
        False,
        title=api.tr('ui.option.title.verbose_debug_logging', "Verbose debug logging"),
        in_profile=True,
    ),

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
