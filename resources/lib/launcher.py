#
# Advanced Emulator Launcher: Default launcher implementation
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

# --- AEL packages ---
from ael import platforms
from ael.utils import io, kodi
from ael.launchers import LauncherABC

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Default implementation for launching anything ROMs or item based using an application.
# Inherit from this base class to implement your own specific ROM App launcher.
# -------------------------------------------------------------------------------------------------
class AppLauncher(LauncherABC):

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str: return 'App Launcher'
     
    def get_launcher_addon_id(self) -> str: 
        addon_id = kodi.get_addon_id()
        return addon_id

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs. Called by parent build() method.
    #
    def _builder_get_wizard(self, wizard):    
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application', 1, self._builder_get_appbrowser_filter)
        wizard = kodi.WizardDialog_Dummy(wizard, 'args', '', self._builder_get_arguments_from_application_path)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        
        return wizard
    
    def _editor_get_wizard(self, wizard):
        wizard = kodi.WizardDialog_YesNo(wizard, 'change_app', 'Change application?', 'Set a different application? Currently "{}"'.format(self.launcher_settings['application']))
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application', 1, self._builder_get_appbrowser_filter, 
                                              None, self._builder_wants_to_change_app)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        
        return wizard
            
    def _build_post_wizard_hook(self):        
        self.non_blocking = True
        app = self.launcher_settings['application']
        app_FN = io.FileName(app)
        
        self.launcher_settings['secname'] = app_FN.getBase()
        return True
    
    def _builder_get_arguments_from_application_path(self, input, item_key, launcher_args):
        if input: return input
        app = launcher_args['application']
        appPath = io.FileName(app)
        default_arguments = platforms.emudata_get_program_arguments(appPath.getBase())

        return default_arguments
    
    #
    # Wizard helper, when a user wants to change the application path.
    #
    def _builder_wants_to_change_app(self, item_key, launcher):
        return launcher[item_key] == True

    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def get_application(self) -> str:
        if 'application' not in self.launcher_settings:
            logger.error('LauncherABC::launch() No application argument defined')            
            return None
        
        application = io.FileName(self.launcher_settings['application'])
        
        # --- Check for errors and abort if errors found ---
        if not application.exists():
            logger.error('Launching app not found "{0}"'.format(application.getPath()))
            kodi.notify_warn('App {0} not found.'.format(application.getPath()))
            return None
        
        return application.getPath()
        