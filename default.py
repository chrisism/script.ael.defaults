﻿# -*- coding: utf-8 -*-
#
# Default plugins for AKL
# Launchers, scrapers and scanners
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import logging

# --- Kodi stuff ---
import xbmcaddon

# AKL main imports
from akl import constants, settings, addons
from akl.utils import kodilogging, io, kodi

from akl.launchers import ExecutionSettings, get_executor_factory
from akl.scrapers import ScrapeStrategy, ScraperSettings

# Local modules
from resources.lib.launcher import AppLauncher
from resources.lib.scanner import RomFolderScanner
from resources.lib.scraper import LocalFilesScraper

kodilogging.config()
logger = logging.getLogger(__name__)

# --- Addon object (used to access settings) ---
addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')


# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin():
    os_name = io.is_which_os()
    
    # --- Some debug stuff for development ---
    logger.info('------------ Called Advanced Kodi Launcher Plugin: Default plugins ------------')
    logger.info(f'addon.id         "{addon_id}"')
    logger.info(f'addon.version    "{addon_version}"')
    logger.info(f'sys.platform     "{sys.platform}"')
    logger.info(f'OS               "{os_name}"')
    
    for i in range(len(sys.argv)):
        logger.info('sys.argv[{}] "{}"'.format(i, sys.argv[i]))

    addon_args = addons.AklAddonArguments('script.akl.defaults')
    try:
        addon_args.parse()
    except Exception as ex:
        logger.error('Exception in plugin', exc_info=ex)
        kodi.dialog_OK(text=addon_args.get_usage())
        return
    
    if addon_args.get_command() == addons.AklAddonArguments.LAUNCH:
        launch_rom(addon_args)
    elif addon_args.get_command() == addons.AklAddonArguments.CONFIGURE_LAUNCHER:
        configure_launcher(addon_args)
    elif addon_args.get_command() == addons.AklAddonArguments.SCAN:
        scan_for_roms(addon_args)
    elif addon_args.get_command() == addons.AklAddonArguments.CONFIGURE_SCANNER:
        configure_scanner(addon_args)
    elif addon_args.get_command() == addons.AklAddonArguments.SCRAPE:
        run_scraper(addon_args)
    else:
        kodi.dialog_OK(text=addon_args.get_help())
    
    logger.debug('Advanced Kodi Launcher Plugin: Default plugins -> exit')


# ---------------------------------------------------------------------------------------------
# Launcher methods.
# ---------------------------------------------------------------------------------------------
# Arguments: --akl_addon_id --rom_id
def launch_rom(args: addons.AklAddonArguments):
    logger.debug('App Launcher: Starting ...')
    
    try:
        execution_settings = ExecutionSettings()
        execution_settings.delay_tempo = settings.getSettingAsInt('delay_tempo')
        execution_settings.display_launcher_notify = settings.getSettingAsBool('display_launcher_notify')
        execution_settings.is_non_blocking = settings.getSettingAsBool('is_non_blocking')
        execution_settings.media_state_action = settings.getSettingAsInt('media_state_action')
        execution_settings.suspend_audio_engine = settings.getSettingAsBool('suspend_audio_engine')
        execution_settings.suspend_screensaver = settings.getSettingAsBool('suspend_screensaver')
        execution_settings.suspend_joystick_engine = settings.getSettingAsBool('suspend_joystick')
                
        addon_dir = kodi.getAddonDir()
        report_path = addon_dir.pjoin('reports')
        if not report_path.exists():
            report_path.makedirs()
        report_path = report_path.pjoin('{}-{}.txt'.format(args.get_akl_addon_id(), args.get_entity_id()))
        
        executor_factory = get_executor_factory(report_path)
        launcher = AppLauncher(
            args.get_akl_addon_id(),
            args.get_entity_id(),
            args.get_webserver_host(),
            args.get_webserver_port(),
            executor_factory,
            execution_settings)
        
        launcher.launch()
    except Exception as e:
        logger.error('Exception while executing ROM', exc_info=e)
        kodi.notify_error('Failed to execute ROM')


# Arguments: --akl_addon_id --romcollection_id | --rom_id
def configure_launcher(args: addons.AklAddonArguments):
    logger.debug('App Launcher: Configuring ...')
        
    launcher = AppLauncher(
        args.get_akl_addon_id(),
        args.get_entity_id(),
        args.get_webserver_host(),
        args.get_webserver_port())
    
    if launcher.build():
        launcher.store_settings()
        return
    
    kodi.notify_warn('Cancelled creating launcher')


# ---------------------------------------------------------------------------------------------
# Scanner methods.
# ---------------------------------------------------------------------------------------------
# Arguments: --source_id --server_host --server_port
def scan_for_roms(args: addons.AklAddonArguments):
    logger.debug('ROM Folder scanner: Starting scan ...')
    progress_dialog = kodi.ProgressDialog()

    addon_dir = kodi.getAddonDir()
    report_path = addon_dir.pjoin('reports')
            
    scanner = RomFolderScanner(
        report_path,
        args.get_entity_id(),
        args.get_webserver_host(),
        args.get_webserver_port(),
        progress_dialog)
        
    scanner.scan()
    progress_dialog.endProgress()
    
    logger.debug('scan_for_roms(): Finished scanning')
    
    amount_dead = scanner.amount_of_dead_roms()
    if amount_dead > 0:
        logger.info(f'scan_for_roms(): {amount_dead} roms marked as dead')
        scanner.remove_dead_roms()
        
    amount_scanned = scanner.amount_of_scanned_roms()
    if amount_scanned == 0:
        logger.info('scan_for_roms(): No roms scanned')
    else:
        logger.info(f'scan_for_roms(): {amount_scanned} roms scanned')
        scanner.store_scanned_roms()
        
    kodi.notify('ROMs scanning done')


# Arguments: --source_id
def configure_scanner(args: addons.AklAddonArguments):
    logger.debug('ROM Folder scanner: Configuring ...')
    addon_dir = kodi.getAddonDir()
    report_path = addon_dir.pjoin('reports')
    
    scanner = RomFolderScanner(
        report_path,
        args.get_entity_id(),
        args.get_webserver_host(),
        args.get_webserver_port(),
        kodi.ProgressDialog())
    
    if scanner.configure():
        scanner.store_settings()
        return
    
    kodi.notify_warn('Cancelled configuring scanner')


# ---------------------------------------------------------------------------------------------
# Scraper methods.
# ---------------------------------------------------------------------------------------------
def run_scraper(args: addons.AklAddonArguments):
    logger.debug('========== Local files.run_scraper() BEGIN ==================================================')
    pdialog = kodi.ProgressDialog()
    settings = ScraperSettings.from_settings_dict(args.settings)
    # OVERRIDES
    settings.search_term_mode = constants.SCRAPE_AUTOMATIC
    settings.game_selection_mode = constants.SCRAPE_AUTOMATIC
    settings.asset_selection_mode = constants.SCRAPE_AUTOMATIC
    settings.overwrite_existing = constants.SCRAPE_AUTOMATIC
    
    if settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE:
        settings.scrape_metadata_policy = constants.SCRAPE_POLICY_LOCAL_ONLY
    if settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE:
        settings.scrape_assets_policy = constants.SCRAPE_POLICY_LOCAL_ONLY
    
    scraper_strategy = ScrapeStrategy(
        args.get_webserver_host(),
        args.get_webserver_port(),
        settings,
        LocalFilesScraper(),
        pdialog)
                        
    if args.get_entity_type() == constants.OBJ_ROM:
        scraped_rom = scraper_strategy.process_single_rom(args.get_entity_id())
        pdialog.endProgress()
        pdialog.startProgress('Saving ROM in database ...')
        scraper_strategy.store_scraped_rom(args.get_akl_addon_id(), args.get_entity_id(), scraped_rom)
        pdialog.endProgress()
    else:
        scraped_roms = scraper_strategy.process_roms(args.get_entity_type(), args.get_entity_id())
        pdialog.endProgress()
        pdialog.startProgress('Saving ROMs in database ...')
        scraper_strategy.store_scraped_roms(args.get_akl_addon_id(), 
                                            args.get_entity_type(), 
                                            args.get_entity_id(), 
                                            scraped_roms)
        pdialog.endProgress()
        
        
# ---------------------------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------------------------
try:
    run_plugin()
except Exception as ex:
    logger.fatal('Exception in plugin', exc_info=ex)
    kodi.notify_error("General failure")
