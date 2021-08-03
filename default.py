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
from ael import constants, settings, api
from ael.utils import kodilogging, io, kodi

from ael.launchers import ExecutionSettings, get_executor_factory

# Local modules
from resources.lib.launcher import AppLauncher
from resources.lib.scanner import RomFolderScanner
from resources.lib.scraper import AEL_Offline_Scraper

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
    
    parser = argparse.ArgumentParser(prog='script.ael.defaults')
    parser.add_argument('--cmd', help="Command to execute", choices=['launch', 'scan', 'scrape', 'configure'])
    parser.add_argument('--type',help="Plugin type", choices=['LAUNCHER', 'SCANNER', 'SCRAPER'], default=constants.AddonType.LAUNCHER.name)
    parser.add_argument('--server_host', type=str, help="Host")
    parser.add_argument('--server_port', type=int, help="Port")
    parser.add_argument('--rom_id', type=str, help="ROM ID")
    parser.add_argument('--romcollection_id', type=str, help="ROM Collection ID")
    parser.add_argument('--launcher_id', type=str, help="Launcher configuration ID")
    parser.add_argument('--rom_args', type=str)
    
    try:
        args = parser.parse_args()
    except Exception as ex:
        logger.error('Exception in plugin', exc_info=ex)
        kodi.dialog_OK(text=parser.usage)
        return
    
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
# Arguments: --settings (json) --rom_args (json) --launcher_id --rom_id --server_host --server_port
def launch_rom(args):
    logger.debug('App Launcher: Starting ...')
    rom_arguments       = json.loads(args.rom_args)
    try:
        execution_settings = ExecutionSettings()
        execution_settings.delay_tempo              = settings.getSettingAsInt('delay_tempo')
        execution_settings.display_launcher_notify  = settings.getSettingAsBool('display_launcher_notify')
        execution_settings.is_non_blocking          = settings.getSettingAsBool('is_non_blocking')
        execution_settings.media_state_action       = settings.getSettingAsInt('media_state_action')
        execution_settings.suspend_audio_engine     = settings.getSettingAsBool('suspend_audio_engine')
        execution_settings.suspend_screensaver      = settings.getSettingAsBool('suspend_screensaver')
                
        addon_dir = kodi.getAddonDir()
        report_path = addon_dir.pjoin('reports')
        if not report_path.exists(): report_path.makedirs()    
        report_path = report_path.pjoin('{}-{}.txt'.format(args.launcher_id, args.rom_id))
        
        executor_factory = get_executor_factory(report_path)
        launcher = AppLauncher(executor_factory, execution_settings, args.server_host, args.server_port)
        launcher.load_launcher_settings(args.rom_id, args.launcher_id)
        launcher.launch(rom_arguments)
    except Exception as e:
        logger.error('Exception while executing ROM', exc_info=e)
        kodi.notify_error('Failed to execute ROM')    

# Arguments: --settings (json) --launcher_id --romcollection_id
def configure_launcher(args):
    logger.debug('App Launcher: Configuring ...')
        
    launcher = AppLauncher(None, None, args.server_host, args.server_port)
    
    if args.launcher_id is not None:
        launcher.load_launcher_settings(args.romcollection_id, args.rom_id, args.launcher_id)
        if launcher.edit():
            launcher.store_launcher_settings(args.romcollection_id, args.rom_id, args.launcher_id)
            return
    else:
        if launcher.build():
            launcher.store_launcher_settings(args.romcollection_id, args.rom_id,)
            return
    
    kodi.notify_warn('Cancelled creating launcher')

# ---------------------------------------------------------------------------------------------
# Scanner methods.
# ---------------------------------------------------------------------------------------------
# Arguments: --settings (json) --scanner_id --romcollection_id --server_host --server_port
def scan_for_roms(args):
    logger.debug('ROM Folder scanner: Starting scan ...')
    scanner_settings = json.loads(args.settings) if args.settings else None
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
    
    logger.debug('scan_for_roms(): Finished scanning')
    
    amount_scanned = scanner.amount_of_scanned_roms()
    if amount_scanned == 0:
        logger.info('scan_for_roms(): No roms scanned')
        return
        
    logger.info('scan_for_roms(): {} roms scanned'.format(amount_scanned))
    scanner.store_scanned_roms(args.romcollection_id, args.scanner_id)
    kodi.notify('ROMs scanning done')

# Arguments: --settings (json) --scanner_id (opt) --romcollection_id --launcher_settings (opt)
def configure_scanner(args):
    logger.debug('ROM Folder scanner: Configuring ...')    
    scanner_settings = json.loads(args.settings) if args.settings else None
    launcher_settings = json.loads(args.launcher_settings) if args.launcher_settings else None
    
    addon_dir = kodi.getAddonDir()
    report_path = addon_dir.pjoin('reports')
    
    scanner = RomFolderScanner(
        report_path, 
        scanner_settings,
        launcher_settings,
        kodi.ProgressDialog())
    
    if scanner.configure():
        scanner.store_scanner_settings(args.romcollection_id, args.scanner_id)
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
    