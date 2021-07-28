# -*- coding: utf-8 -*-
#
# TGDB Scraper for AEL
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import logging
import json

from urllib.parse import urlsplit, parse_qs
    
# --- Kodi stuff ---
import xbmcaddon

# AEL main imports
from ael.launchers import *
from ael import settings
from ael.utils import kodilogging, text, kodi, io

#from resources.scraper import RetroarchLauncher

kodilogging.config() 
logger = logging.getLogger(__name__)

# --- Addon object (used to access settings) ---
addon           = xbmcaddon.Addon()
addon_id        = addon.getAddonInfo('id')
addon_version   = addon.getAddonInfo('version')

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin():
    # --- Some debug stuff for development ---
    logger.info('------------ Called Advanced Emulator Launcher Plugin: TGDB Scraper ------------')
    logger.info('addon.id         "{}"'.format(addon_id))
    logger.info('addon.version    "{}"'.format(addon_version))
    logger.info('sys.platform   "{}"'.format(sys.platform))
    if io.is_android(): logger.info('OS             "Android"')
    if io.is_windows(): logger.info('OS             "Windows"')
    if io.is_osx():     logger.info('OS             "OSX"')
    if io.is_linux():   logger.info('OS             "Linux"')
    for i in range(len(sys.argv)): logger.info('sys.argv[{}] "{}"'.format(i, sys.argv[i]))
    
    logger.debug('Advanced Emulator Launcher Plugin: TGDB Scraper -> exit')

try:
    run_plugin()
except Exception as ex:
    logger.fatal('Exception in plugin', exc_info=ex)
    kodi.notify_error("General failure")
    