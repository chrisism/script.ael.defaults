# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Default scraper implementation
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import re
import os

# --- AEL packages ---
from ael import constants, platforms
from ael.utils import io, text
from ael.scrapers import Scraper

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------------------
# AEL offline metadata scraper.
# ------------------------------------------------------------------------------------------------
class AEL_Offline_Scraper(Scraper):
    # --- Class variables ------------------------------------------------------------------------
    supported_metadata_list = [
        constants.META_TITLE_ID,
        constants.META_YEAR_ID,
        constants.META_GENRE_ID,
        constants.META_DEVELOPER_ID,
        constants.META_NPLAYERS_ID,
        constants.META_ESRB_ID,
        constants.META_PLOT_ID,
    ]

    # --- Constructor ----------------------------------------------------------------------------
    # @param settings: [dict] Addon settings. Particular scraper settings taken from here.
    def __init__(self, settings):
        # --- This scraper settings ---
        self.addon_dir = settings['scraper_aeloffline_addon_code_dir']
        logger.debug('AEL_Offline_Scraper.__init__() Setting addon dir "{}"'.format(self.addon_dir))

        # --- Cached TGDB metadata ---
        self._reset_cached_games()

        # --- Pass down common scraper settings ---
        super(AEL_Offline_Scraper, self).__init__(settings)

    def get_id(self):
        return constants.SCRAPER_AEL_OFFLINE_ID
    
    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self): return 'AEL Offline'

    def get_filename(self): return 'AEL_Offline_Scraper'

    def supports_disk_cache(self): return False

    def supports_search_string(self): return False

    def supports_metadata_ID(self, metadata_ID):
        #TODO: return True if metadata_ID in ScreenScraper.supported_metadata_list else False
        return False

    def supports_metadata(self): return True

    def supports_asset_ID(self, asset_ID): return False

    def supports_assets(self): return False

    def check_before_scraping(self, status_dic): return status_dic

    # Search term is always None for this scraper.
    def get_candidates(self, search_term, rom_FN:io.FileName, rom_checksums_FN, platform, status_dic):
        # AEL Offline cannot be disabled.
        # Prepare data for scraping.
        rombase_noext = rom_FN.getBase_noext()
        logger.debug('AEL_Offline_Scraper.get_candidates() rombase_noext "{}"'.format(rombase_noext))
        logger.debug('AEL_Offline_Scraper.get_candidates() AEL platform  "{}"'.format(platform))

        # If not cached XML data found (maybe offline scraper does not exist for this platform or 
        # cannot be loaded) return an empty list of candidates.
        self._initialise_platform(platform)
        if not self.cached_games: return []

        if platform == 'MAME':
            # --- Search MAME games ---
            candidate_list = self._get_MAME_candidates(rombase_noext, platform)
        else:
            # --- Search No-Intro games ---
            candidate_list = self._get_NoIntro_candidates(rombase_noext, platform)

        return candidate_list

    def get_metadata(self, status_dic):
        gamedata = self._new_gamedata_dic()

        if self.cached_platform == 'MAME':
            key_id = self.candidate['id']
            logger.debug("AEL_Offline_Scraper.get_metadata() Mode MAME id = '{}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['title']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['developer']
            gamedata['nplayers']  = self.cached_games[key_id]['nplayers']
        elif self.cached_platform == 'Unknown':
            # Unknown platform. Behave like NULL scraper
            logger.debug("AEL_Offline_Scraper.get_metadata() Mode Unknown. Doing nothing.")
        else:
            # No-Intro scraper by default.
            key_id = self.candidate['id']
            logger.debug("AEL_Offline_Scraper.get_metadata() Mode No-Intro id = '{}'".format(key_id))
            gamedata['title']     = self.cached_games[key_id]['title']
            gamedata['year']      = self.cached_games[key_id]['year']
            gamedata['genre']     = self.cached_games[key_id]['genre']
            gamedata['developer'] = self.cached_games[key_id]['developer']
            gamedata['nplayers']  = self.cached_games[key_id]['nplayers']
            gamedata['esrb']      = self.cached_games[key_id]['rating']
            gamedata['plot']      = self.cached_games[key_id]['plot']

        return gamedata

    def get_assets(self, asset_info, status_dic): return []

    def resolve_asset_URL(self, selected_asset, status_dic): pass

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic): pass
        
    # --- This class own methods -----------------------------------------------------------------
    def _get_MAME_candidates(self, rombase_noext, platform):
        logger.debug("AEL_Offline_Scraper._get_MAME_candidates() Scraper working in MAME mode.")

        # --- MAME rombase_noext is exactly the rom name ---
        # MAME offline scraper either returns one candidate game or nothing at all.
        rom_base_noext_lower = rombase_noext.lower()
        if rom_base_noext_lower in self.cached_games:
            candidate = self._new_candidate_dic()
            candidate['id'] = self.cached_games[rom_base_noext_lower]['ROM']
            candidate['display_name'] = self.cached_games[rom_base_noext_lower]['title']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            return [candidate]
        else:
            return []

    def _get_NoIntro_candidates(self, rombase_noext, platform):
        # --- First try an exact match using rombase_noext ---
        logger.debug("AEL_Offline_Scraper._get_NoIntro_candidates() Scraper working in No-Intro mode.")
        logger.debug("AEL_Offline_Scraper._get_NoIntro_candidates() Trying exact search for '{}'".format(
            rombase_noext))
        candidate_list = []
        if rombase_noext in self.cached_games:
            logger.debug("AEL_Offline_Scraper._get_NoIntro_candidates() Exact match found.")
            candidate = self._new_candidate_dic()
            candidate['id'] = rombase_noext
            candidate['display_name'] = self.cached_games[rombase_noext]['ROM']
            candidate['platform'] = platform
            candidate['scraper_platform'] = platform
            candidate['order'] = 1
            candidate_list.append(candidate)
        else:
            # --- If nothing found, do a fuzzy search ---
            # Here implement a Levenshtein distance algorithm.
            search_term = text.format_ROM_name_for_scraping(rombase_noext)
            logger.debug("AEL_Offline_Scraper._get_NoIntro_candidates() No exact match found.")
            logger.debug("AEL_Offline_Scraper._get_NoIntro_candidates() Trying fuzzy search '{}'".format(
                search_term))
            search_string_lower = rombase_noext.lower()
            regexp = '.*{}.*'.format(search_string_lower)
            try:
                # Sometimes this produces: raise error, v # invalid expression
                p = re.compile(regexp)
            except:
                logger.info('AEL_Offline_Scraper._get_NoIntro_candidates() Exception in re.compile(regexp)')
                logger.info('AEL_Offline_Scraper._get_NoIntro_candidates() regexp = "{}"'.format(regexp))
                return []

            for key in self.cached_games:
                this_game_name = self.cached_games[key]['ROM']
                this_game_name_lower = this_game_name.lower()
                match = p.match(this_game_name_lower)
                if not match: continue
                # --- Add match to candidate list ---
                candidate = self._new_candidate_dic()
                candidate['id'] = self.cached_games[key]['ROM']
                candidate['display_name'] = self.cached_games[key]['ROM']
                candidate['platform'] = platform
                candidate['scraper_platform'] = platform
                candidate['order'] = 1
                # If there is an exact match of the No-Intro name put that candidate game first.
                if search_term == this_game_name:                         candidate['order'] += 1
                if rombase_noext == this_game_name:                       candidate['order'] += 1
                if self.cached_games[key]['ROM'].startswith(search_term): candidate['order'] += 1
                candidate_list.append(candidate)
            candidate_list.sort(key = lambda result: result['order'], reverse = True)

        return candidate_list

    # Load XML database and keep it cached in memory.
    def _initialise_platform(self, platform):
        # Check if we have data already cached in object memory for this platform
        if self.cached_platform == platform:
            logger.debug('AEL_Offline_Scraper._initialise_platform() platform = "{}" is cached in object.'.format(
                platform))
            return
        else:
            logger.debug('AEL_Offline_Scraper._initialise_platform() platform = "{}" not cached. Loading XML.'.format(
                platform))

        # What if platform is not in the official list dictionary?
        # Then load nothing and behave like the NULL scraper.
        if platform in platforms.platform_long_to_index_dic:
            # Check for aliased platforms
            pobj = platforms.AEL_platforms[platforms.platform_long_to_index_dic[platform]]
            if pobj.aliasof:
                logger.debug('AEL_Offline_Scraper._initialise_platform() Aliased platform. Using parent XML.')
                parent_pobj = platforms.AEL_platforms[platforms.platform_compact_to_index_dic[pobj.aliasof]]
                xml_file = 'data-AOS/' + parent_pobj.long_name + '.xml'
            else:
                xml_file = 'data-AOS/' + platform + '.xml'

        else:
            logger.debug('AEL_Offline_Scraper._initialise_platform() Platform "{}" not found'.format(platform))
            logger.debug('AEL_Offline_Scraper._initialise_platform() Defaulting to Unknown')
            self._reset_cached_games()
            return

        # Load XML database and keep it in memory for subsequent calls
        xml_path = os.path.join(self.addon_dir, xml_file)
        # logger.debug('AEL_Offline_Scraper._initialise_platform() Loading XML {}'.format(xml_path))
        self.cached_games = audit_load_OfflineScraper_XML(xml_path)
        if not self.cached_games:
            self._reset_cached_games()
            return
        self.cached_xml_path = xml_path
        self.cached_platform = platform
        logger.debug('AEL_Offline_Scraper._initialise_platform() cached_xml_path = {}'.format(self.cached_xml_path))
        logger.debug('AEL_Offline_Scraper._initialise_platform() cached_platform = {}'.format(self.cached_platform))

    def _reset_cached_games(self):
        self.cached_games = {}
        self.cached_xml_path = ''
        self.cached_platform = 'Unknown'