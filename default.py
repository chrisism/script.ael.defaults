# -*- coding: utf-8 -*-
#
# Default plugins for AEL
# Launchers, scrapers and scanners
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import argparse
import logging
import json
    
# --- Kodi stuff ---
import xbmcaddon

# AEL main imports
from ael import constants, settings
from ael.utils import kodilogging, io, kodi

from ael.launchers import ExecutionSettings, get_executor_factory

# Local modules
from resources.launcher import AppLauncher
from resources.scanner import RomFolderScanner
from resources.scraper import AEL_Offline_Scraper

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
    logger.info('------------ Called Advanced Emulator Launcher Plugin: Default plugins ------------')
    logger.info('addon.id         "{}"'.format(addon_id))
    logger.info('addon.version    "{}"'.format(addon_version))
    logger.info('sys.platform     "{}"'.format(sys.platform))
    if io.is_android(): logger.info('OS               "Android"')
    if io.is_windows(): logger.info('OS               "Windows"')
    if io.is_osx():     logger.info('OS               "OSX"')
    if io.is_linux():   logger.info('OS               "Linux"')
    for i in range(len(sys.argv)): logger.info('sys.argv[{}] "{}"'.format(i, sys.argv[i]))
    
    logger.debug('TEST A')
    parser = argparse.ArgumentParser(prog='script.ael.defaults')
    parser.add_argument('--cmd', help="Command to execute", choices=['launch', 'scan', 'scrape', 'configure'])
    parser.add_argument('--type',help="Plugin type", choices=['LAUNCHER', 'SCANNER', 'SCRAPER'], default=constants.AddonType.LAUNCHER.name)
    parser.add_argument('--romcollection_id', type=str, help="ROM Collection ID")
    parser.add_argument('--rom_id', type=str, help="ROM ID")
    parser.add_argument('--launcher_id', type=str, help="Launcher configuration ID")
    parser.add_argument('--rom', type=str, help="ROM data dictionary")
    parser.add_argument('--rom_args', type=str)
    parser.add_argument('--settings', type=str)
    parser.add_argument('--is_non_blocking', type=bool, default=False)
    
    logger.debug('TEST B')
    try:
        args = parser.parse_args()
        logger.debug('TEST C')
    except Exception as ex:
        logger.error('Exception in plugin', exc_info=ex)
        kodi.dialog_OK(text=parser.usage)
        return
    
    logger.debug('TEST D')
    if   args.type == constants.AddonType.LAUNCHER.name and args.cmd == 'launch': launch_rom(args)
    elif args.type == constants.AddonType.LAUNCHER.name and args.cmd == 'configure': configure_launcher(args)
    elif args.type == constants.AddonType.SCANNER.name  and args.cmd == 'scan': scan_for_roms(args)
    elif args.type == constants.AddonType.SCANNER.name  and args.cmd == 'configure': configure_scanner(args)
    elif args.type == constants.AddonType.SCRAPER.name  and args.cmd == 'scrape': run_scraper(args)
    else:
        kodi.dialog_OK(text=parser.format_help())
    
    logger.debug('Advanced Emulator Launcher Plugin: Default plugins -> exit')

# ---------------------------------------------------------------------------------------------
# Launcher methods.
# ---------------------------------------------------------------------------------------------
def launch_rom(args):
    logger.debug('App Launcher: Starting ...')
    launcher_settings   = json.loads(args.settings)
    rom_arguments       = json.loads(args.rom_args)
    launcher_id         = args.launcher_id
    rom_id              = args.rom_id

    try:
        execution_settings = ExecutionSettings()
        execution_settings.delay_tempo              = settings.getSettingAsInt('delay_tempo')
        execution_settings.display_launcher_notify  = settings.getSettingAsBool('display_launcher_notify')
        execution_settings.is_non_blocking          = True if args.is_non_blocking == 'true' else False
        execution_settings.media_state_action       = settings.getSettingAsInt('media_state_action')
        execution_settings.suspend_audio_engine     = settings.getSettingAsBool('suspend_audio_engine')
        execution_settings.suspend_screensaver      = settings.getSettingAsBool('suspend_screensaver')
        
        addon_dir = kodi.getAddonDir()
        report_path = addon_dir.pjoin('reports')
        if not report_path.exists(): report_path.makedirs()    
        report_path = report_path.pjoin('{}-{}.txt'.format(launcher_id, rom_id))
        
        executor_factory = get_executor_factory(report_path)
        launcher = AppLauncher(executor_factory, execution_settings, launcher_settings)
        launcher.launch(rom_arguments)
    except Exception as e:
        logger.error('Exception while executing ROM', exc_info=e)
        kodi.notify_error('Failed to execute ROM')    

def configure_launcher(args):
    logger.debug('App Launcher: Configuring ...')
    romcollection_id:str = args['romcollection_id'][0] if 'romcollection_id' in args else None
    launcher_id:str      = args['launcher_id'][0] if 'launcher_id' in args else None
    settings:str         = args['settings'][0] if 'settings' in args else None
    
    launcher_settings = json.loads(settings)    
    launcher = AppLauncher(None, None, launcher_settings)
    if launcher_id is None and launcher.build():
        launcher.store_launcher_settings(romcollection_id)
        return
    
    if launcher_id is not None and launcher.edit():
        launcher.store_launcher_settings(romcollection_id, launcher_id)
        return
    
    kodi.notify_warn('Cancelled creating launcher')

# ---------------------------------------------------------------------------------------------
# Scanner methods.
# ---------------------------------------------------------------------------------------------
def scan_for_roms(args):
    logger.debug('ROM Folder scanner: Starting scan ...')
    romcollection_id:str = args['romcollection_id'][0] if 'romcollection_id' in args else None
    scanner_id:str       = args['scanner_id'][0] if 'scanner_id' in args else None
    settings:str         = args['settings'][0] if 'settings' in args else None

    scanner_settings = json.loads(settings) if settings else None
    progress_dialog = kodi.ProgressDialog()

    addon_dir = kodi.getAddonDir()
    report_path = addon_dir.pjoin('reports')
            
    scanner = RomFolderScanner(
        report_path,
        scanner_settings,
        None,
        progress_dialog)
    
    scanner.scan()
    progress_dialog.endProgress()
    
    logger.debug('vw_execute_folder_scanner(): Finished scanning')
    
    amount_scanned = scanner.amount_of_scanned_roms()
    if amount_scanned == 0:
        logger.info('vw_execute_folder_scanner(): No roms scanned')
        return
        
    logger.info('vw_execute_folder_scanner(): {} roms scanned'.format(amount_scanned))
    scanner.store_scanned_roms(romcollection_id, scanner_id)
    kodi.notify('ROMs scanning done')

def configure_scanner(args):
    logger.debug('ROM Folder scanner: Configuring ...')

    romcollection_id:str        = args['romcollection_id'][0] if 'romcollection_id' in args else None
    scanner_id:str              = args['scanner_id'][0] if 'scanner_id' in args else None
    settings:str                = args['settings'][0] if 'settings' in args else None
    def_launcher_settings:str   = args['launcher'][0] if 'launcher' in args else None
    
    scanner_settings = json.loads(settings) if settings else None
    launcher_settings = json.loads(def_launcher_settings) if def_launcher_settings else None
    
    addon_dir = kodi.getAddonDir()
    report_path = addon_dir.pjoin('reports')
    
    scanner = RomFolderScanner(
        report_path, 
        scanner_settings,
        launcher_settings,
        kodi.ProgressDialog())
    
    if scanner.configure():
        scanner.store_scanner_settings(romcollection_id, scanner_id)
        return
    
    kodi.notify_warn('Cancelled configuring scanner')

# ---------------------------------------------------------------------------------------------
# Scraper methods.
# ---------------------------------------------------------------------------------------------
def run_scraper(args):
    logger.debug('Offline scraper: Starting ...')
    scraper_settings = json.loads(args.settings)
    rom_dic          = json.loads(args.rom)
    rom_id           = args.rom_id

    logger.debug('========== run_scraper() BEGIN ==================================================')
    pdialog             = kodi.ProgressDialog()
    scraper_strategy    = AEL_Offline_Scraper(scraper_settings)
    # g_ScraperFactory.create_scraper(launcher, pdialog, scraper_settings)

    # roms = scraper_strategy.scanner_process_launcher(launcher)
    # pdialog.endProgress()
    # pdialog.startProgress('Saving ROM JSON database ...')

        
# ---------------------------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------------------------
try:
    run_plugin()
except Exception as ex:
    logger.fatal('Exception in plugin', exc_info=ex)
    kodi.notify_error("General failure")
    