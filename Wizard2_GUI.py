# -*- coding: utf-8; mode: python -*-
#
# Cherokee-admin
#
# Authors:
#      Alvaro Lopez Ortega <alvaro@alobbs.com>
#
# Copyright (C) 2001-2011 Alvaro Lopez Ortega
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
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
#

import os
import time
import CTK
import validations
import CommandProgress

from configured import *


CFG_PREFIX = "tmp!wizard"

VALIDATION = [
    ('%s!vserver_nick'%(CFG_PREFIX), validations.is_not_empty),
]

#
# Phase's base
#

class Phase (CTK.Container):
    def __init__ (self, title):
        CTK.Container.__init__ (self)
        self.title = title
        self.cont  = CTK.Container()

    def __iadd__ (self, w):
        self.cont += w
        return self

    def Render (self):
        box = CTK.Container()
        box += CTK.RawHTML ('<h2>%s</h2>' %(_(self.title)))
        box += self.cont
        return box.Render()

    def __call__ (self):
        if hasattr (self, '__build_GUI__'):
            self.cont = CTK.Container()
            self.__build_GUI__()

        return self.Render().toStr()

class Phase_Next (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)
        self.buttons_added = False

    def Render (self):
        if not self.buttons_added:
            self.buttons_added = True
            self += CTK.DruidButtonsPanel_Next_Auto()

        return Phase.Render(self)

class Phase_Cancel (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)
        self.buttons_added = False

    def Render (self):
        if not self.buttons_added:
            self.buttons_added = True
            self += CTK.DruidButtonsPanel_Cancel()

        return Phase.Render(self)

class Phase_Close (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)
        self.buttons_added = False

    def Render (self):
        if not self.buttons_added:
            self.buttons_added = True
            self += CTK.DruidButtonsPanel_Close()

        return Phase.Render(self)

class Phase_PrevNext (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)
        self.buttons_added = False

    def Render (self):
        if not self.buttons_added:
            self.buttons_added = True
            self += CTK.DruidButtonsPanel_PrevNext_Auto()

        return Phase.Render(self)


#
# Stages
#

class Phase_Welcome (Phase_Next):
    def __init__ (self, wizard, install_type):
        Phase_Next.__init__ (self, "Welcome to the %s Wizard"%(wizard))
        self += CTK.RawHTML ('Welcome!')

        # Clean up previous wizard info
        del (CTK.cfg[CFG_PREFIX])

        # Set installation type
        CTK.cfg['%s!type'%(CFG_PREFIX)] = install_type


#
# Enter Virtual Server
#

NOTE_VSERVER = N_("Domain name of the Virtual Host you are about to create. Wildcards are allowed. For example: *.example.com")

class Stage_Enter_VServer (Phase_PrevNext):
    class Apply:
        def __call__ (self):
            return CTK.cfg_apply_post()

    def __init__ (self):
        Phase_PrevNext.__init__ (self, _("Name of the new Virtual Server"))

    def __build_GUI__ (self):
        table = CTK.PropsTable()
        table.Add (_('Domain Name'), CTK.TextCfg('%s!vserver_nick'%(CFG_PREFIX), False), _(NOTE_VSERVER))

        box = CTK.Box ({'class': 'market-target-selection'})

        submit = CTK.Submitter (URL_STAGE_ENTER_VSERVER_APPLY)
        submit.bind ('submit_success', CTK.DruidContent__JS_to_goto_next (box.id))
        submit += table

        box += submit
        self += box

URL_STAGE_ENTER_VSERVER       = "/wizard2/stages/enter_vserver"
URL_STAGE_ENTER_VSERVER_APPLY = "/wizard2/stages/enter_vserver/apply"

CTK.publish ('^%s'%(URL_STAGE_ENTER_VSERVER),       Stage_Enter_VServer)
CTK.publish ('^%s'%(URL_STAGE_ENTER_VSERVER_APPLY), Stage_Enter_VServer.Apply, validation=VALIDATION, method="POST")


#
# Virtual Server Logging
#

LOGGING_OPTIONS = [
    ('',     N_('No logging')),
    ('copy', N_('Copy from default'))
]

class Stage_VServer_Logging (Phase_PrevNext):
    class Apply:
        def __call__ (self):
            return CTK.cfg_apply_post()

    def __init__ (self):
        Phase_PrevNext.__init__ (self, _("Logging Configuration"))

    def __build_GUI__ (self):
        submit = CTK.Submitter (URL_STAGE_VSERVER_LOGGING_APPLY)
        submit.bind ('submit_success', submit.JS_to_trigger ('goto_next_stage'))

        submit += CTK.RadioGroupCfg ('%s!logging'%(CFG_PREFIX), LOGGING_OPTIONS, {'checked': LOGGING_OPTIONS[0][0]})

        box = CTK.Box()
        box += submit
        self += box

        # Next stage
        self.bind ('goto_next_stage', CTK.DruidContent__JS_to_goto_next (box.id))


URL_STAGE_VSERVER_LOGGING       = "/wizard2/stages/vserver_logging"
URL_STAGE_VSERVER_LOGGING_APPLY = "/wizard2/stages/vserver_logging/apply"

CTK.publish ('^%s'%(URL_STAGE_VSERVER_LOGGING),       Stage_VServer_Logging)
CTK.publish ('^%s'%(URL_STAGE_VSERVER_LOGGING_APPLY), Stage_VServer_Logging.Apply, validation=VALIDATION, method="POST")


#
# Select Install Type
#

NOTE_DOWNLOAD_URL = N_("URL or path to the software package. For instance, a tar.gz or zip file.")
NOTE_APP_DIR      = N_("Directory where the software is already installed. In case you're using your distro's package, for instance.")

INSTALL_OPTIONS = [
    ('download_auto',   N_('Automatic Download')),
    ('download_URL',    N_('Use a Specific Package')),
    ('local_directory', N_('Already Installed Software')),
]

INSTALL_TYPE_ON_CHANGE_JS = """
$('.stage_install_type_block').hide();

var val = $('#%s input[type=\"radio\"]:checked').val();
     if (val == 'download_auto')   { %s }
else if (val == 'download_URL')    { %s }
else if (val == 'local_directory') { %s }
"""

class Stage_Install_Type (Phase_PrevNext):
    class Apply:
        def __call__ (self):
            type_key = '%s!install_type'%(CFG_PREFIX)
            url_key  = '%s!download_url'%(CFG_PREFIX)
            dir_key  = '%s!app_dir'     %(CFG_PREFIX)

            tipe_cfg  = CTK.cfg.get_val(type_key)
            tipe_post = CTK.post.get_val(type_key)

            # Changed type of install
            if tipe_cfg != tipe_post:
                if tipe_post == 'download_auto':
                    CTK.cfg['%s!app_fetch'%(CFG_PREFIX)] = 'auto'
                return CTK.cfg_apply_post()

            # Download URL
            if tipe_cfg == 'download_auto':
                CTK.cfg['%s!app_fetch'%(CFG_PREFIX)] = 'auto'
                return CTK.cfg_reply_ajax_ok()

            # Download URL
            elif tipe_cfg == 'download_URL':
                url = CTK.post.get_val (url_key)
                if not url:
                    return {'ret': 'unsatisfactory', 'errors': {url_key: _('Cannot be empty')}}

                CTK.cfg['%s!app_fetch'%(CFG_PREFIX)] = url
                return CTK.cfg_reply_ajax_ok()

            # Local Directory
            elif tipe_cfg == 'local_directory':
                directory = CTK.post.get_val (dir_key)
                if not directory:
                    return {'ret': 'unsatisfactory', 'errors': {dir_key: _('Cannot be empty')}}

                CTK.cfg['%s!app_dir'%(CFG_PREFIX)] = directory
                return CTK.cfg_reply_ajax_ok()

    def __init__ (self):
        Phase_PrevNext.__init__ (self, _("Software Retrival Method"))

    def __build_GUI__ (self):
        radios = CTK.RadioGroupCfg ('%s!install_type'%(CFG_PREFIX), INSTALL_OPTIONS, {'checked': INSTALL_OPTIONS[0][0]})

        submit = CTK.Submitter (URL_STAGE_INSTALL_TYPE_APPLY)
        submit += radios
        submit.bind ('submit_success', submit.JS_to_trigger ('goto_next_stage'))

        # Blocks
        prop_blocks        = {'class': 'stage_install_type_block'}
        prop_blocks_hidden = {'class': 'stage_install_type_block', 'style': 'display: none;'}

        # Automatic
        table = CTK.PropsTable()
        table.Add (_('Installation directory'), CTK.TextCfg('%s!app_dir'%(CFG_PREFIX), True, {'optional_string': _('Automatic')}), _(NOTE_APP_DIR))

        automatic = CTK.Box (prop_blocks)
        automatic += CTK.RawHTML ("<h3>%s</h3>"%(_('Automatic Download')))
        automatic += table

        # Download_URL block
        table = CTK.PropsTable()
        table.Add (_('URL/Path to package'), CTK.TextCfg('%s!download_url'%(CFG_PREFIX)), _(NOTE_DOWNLOAD_URL))
        table.Add (_('Installation directory'), CTK.TextCfg('%s!app_dir'%(CFG_PREFIX), True, {'optional_string': _('Automatic')}), _(NOTE_APP_DIR))

        download_URL = CTK.Box (prop_blocks_hidden)
        download_URL += CTK.RawHTML ("<h3>%s</h3>"%(_('Use a specific Package')))
        download_URL += table

        # Local_Directory block
        table = CTK.PropsTable()
        table.Add (_('Directory of the application'), CTK.TextCfg('%s!app_dir'%(CFG_PREFIX)), _(NOTE_APP_DIR))

        local_directory  = CTK.Box (prop_blocks_hidden)
        local_directory += CTK.RawHTML ("<h3>%s</h3>"%(_('Already Installed Software')))
        local_directory += table

        # Events handling
        js = INSTALL_TYPE_ON_CHANGE_JS %(radios.id,
                                         automatic.JS_to_show(),
                                         download_URL.JS_to_show(),
                                         local_directory.JS_to_show())
        radios.bind ('change', js)

        submit += automatic
        submit += download_URL
        submit += local_directory

        box = CTK.Box()
        box += submit
        box += CTK.RawHTML (js = js)
        self += box

        # Next stage
        self.bind ('goto_next_stage', CTK.DruidContent__JS_to_goto_next (box.id))


def validation_download_url (value):
    # URL or Path
    value = validations.is_url_or_path (value)

    # If path, ensure it exists
    if value.startswith('/'):
        value = validations.is_path (value)
        if not os.path.exists (value):
            raise ValueError, _('Path does not exist')

    return value


VALIDATION_INSTALL_TYPE = VALIDATION + [
    ('%s!download_url'%(CFG_PREFIX), validation_download_url)
]

URL_STAGE_INSTALL_TYPE       = "/wizard2/stages/install_type"
URL_STAGE_INSTALL_TYPE_APPLY = "/wizard2/stages/install_type/apply"

CTK.publish ('^%s'%(URL_STAGE_INSTALL_TYPE),       Stage_Install_Type)
CTK.publish ('^%s'%(URL_STAGE_INSTALL_TYPE_APPLY), Stage_Install_Type.Apply, validation=VALIDATION_INSTALL_TYPE, method="POST")



#
# Select Install Type
#

def collect_arguments (installer_params):
    print "[0] installer_params", installer_params

    # Set the installer parameters:
    #
    for key in CTK.cfg.keys (CFG_PREFIX):
        installer_params[key] = CTK.cfg.get_val ('%s!%s' %(CFG_PREFIX, key))

    # Special case: Empty installation directory
    #
    if not installer_params.get('app_dir'):
        installer_params['app_dir'] = os.path.join (CHEROKEE_OWS_ROOT, str(int(time.time()*100)))

    # Ok
    ret = {'retcode': 0}
    return ret

def check_params (stage_obj, installer_params, Install_Class):
    # Instance Installer
    #
    installer = Install_Class (installer_params)
    stage_obj.installer = installer

    # Let the installer check the parameters
    #
    errors = installer.Check_Parameters()
    if errors:
        return {'retcode': 1, 'stderr': errors[0]}

    # Ok
    return {'retcode': 0}

def check_prerequisites (stage_obj):
    installer = stage_obj.installer

    errors = installer.Check_Prerequisites()
    if errors:
        return {'retcode': 1, 'stderr': errors[0]}

    # Ok
    return {'retcode': 0}

def download (stage_obj):
    installer = stage_obj.installer

    errors = installer.Download()
    if errors:
        return {'retcode': 1, 'stderr': errors[0]}

    # Ok
    return {'retcode': 0}

def unpack (stage_obj):
    installer = stage_obj.installer

    errors = installer.Unpack()
    if errors:
        return {'retcode': 1, 'stderr': errors[0]}

    # Ok
    return {'retcode': 0}

def configure_cherokee (stage_obj):
    installer = stage_obj.installer

    errors = installer.Configure_Cherokee()
    if errors:
        return {'retcode': 1, 'stderr': errors[0]}

    # Ok
    return {'retcode': 0}


class Stage_Do_Install (Phase_Cancel):
    def __init__ (self, Install_Class, next_url):
        Phase_Cancel.__init__ (self, _("Installing.."))

        # Logic Installer
        self.installer_params = {}

        # Commands
        commands = [
            ({'function': collect_arguments,   'description': "Collecting arguments...", 'params': {'installer_params': self.installer_params}}),
            ({'function': check_params,        'description': "Checking parameters...",  'params': {'installer_params': self.installer_params, 'stage_obj': self, 'Install_Class': Install_Class}}),
            ({'function': check_prerequisites, 'description': "Checking requisites...",  'params': {'stage_obj': self}}),
            ({'function': download,            'description': "Downloading...",          'params': {'stage_obj': self}}),
            ({'function': unpack,              'description': "Unpacking...",            'params': {'stage_obj': self}}),
            ({'function': configure_cherokee,  'description': "Configuring...",          'params': {'stage_obj': self}}),
        ]

        # GUI
        progress = CommandProgress.CommandProgress (commands, next_url)
        self += progress

#
# Select Install Type
#

class Stage_Finished (Phase_Close):
    class Apply:
        def __call__ (self):
            return CTK.cfg_reply_ajax_ok()

    def __init__ (self):
        Phase_Close.__init__ (self, _("Installation Finished"))
        self += CTK.RawHTML ('We are done and dusted!')


URL_STAGE_FINISHED_APPLY = "/wizard2/stages/finished/apply"
CTK.publish ('^%s'%(URL_STAGE_FINISHED_APPLY), Stage_Finished.Apply, method="POST")
