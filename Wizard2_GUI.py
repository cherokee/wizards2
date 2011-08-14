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

class Phase (CTK.Box):
    def __init__ (self, title):
        CTK.Box.__init__ (self)
        self.title = title

    def Render (self):
        self.Empty()
        self += CTK.RawHTML ('<h2>%s</h2>' %(_(self.title)))
        if hasattr (self, '__build_GUI__'):
            self.__build_GUI__()

        return CTK.Box.Render (self)

    def __call__ (self):
        return self.Render().toStr()

class Phase_Next (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)

    def Render (self):
        render = Phase.Render (self)
        render += CTK.DruidButtonsPanel_Next_Auto().Render()
        return render

class Phase_Cancel (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)

    def Render (self):
        render = Phase.Render (self)
        render += CTK.DruidButtonsPanel_Cancel().Render()
        return render

class Phase_Close (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)

    def Render (self):
        render = Phase.Render (self)
        render += CTK.DruidButtonsPanel_Close().Render()
        return render

class Phase_PrevNext (Phase):
    def __init__ (self, title):
        Phase.__init__ (self, title)

    def Render (self):
        render = Phase.Render (self)
        render += CTK.DruidButtonsPanel_PrevNext_Auto().Render()
        return render


#
# Stages
#

class Phase_Welcome (Phase_Next):
    def __init__ (self, wizard, install_type):
        Phase_Next.__init__ (self, "Welcome to the %s Wizard"%(wizard))

        # Clean up previous wizard info
        del (CTK.cfg[CFG_PREFIX])

        # Set installation type
        CTK.cfg['%s!type'%(CFG_PREFIX)] = install_type

    def __build_GUI__ (self):
        self += CTK.RawHTML ('Welcome!')


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
        table.Add (_('Domain Name'), CTK.TextCfg('%s!vserver_nick'%(CFG_PREFIX), False, {'class':'noauto'}), _(NOTE_VSERVER))

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

class Stage_VServer_Logging (Phase_PrevNext):
    class Apply:
        def __call__ (self):
            return CTK.cfg_apply_post()

    def __init__ (self):
        Phase_PrevNext.__init__ (self, _("Logging Configuration"))

    def __build_GUI__ (self):
        vsrv_def = CTK.cfg.get_lowest_entry ('vserver')

        logging_options = [
            ('',       N_('No logging')),
            (vsrv_def, N_('Copy from default'))
        ]

        submit = CTK.Submitter (URL_STAGE_VSERVER_LOGGING_APPLY)
        submit += CTK.RadioGroupCfg ('%s!cp_vsrv_log'%(CFG_PREFIX), logging_options, {'checked': logging_options[0][0]})

        box = CTK.Box()
        box += submit
        self += box

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

class Stage_Install_Type (Phase_PrevNext):
    def __init__ (self, default_download_URL):
        Phase_PrevNext.__init__ (self, _("Software Retrival Method"))
        self.default_URL = default_download_URL

    def __build_GUI__ (self):
        # Refresh
        refresh = CTK.Refreshable({'id': 'wizard2-stage-install-type-refresh'})
        refresh.register (lambda: self.Refresh_Content (refresh, self).Render())

        # Radio buttons
        radios = CTK.RadioGroupCfg ('%s!install_type'%(CFG_PREFIX), INSTALL_OPTIONS, {'checked': INSTALL_OPTIONS[0][0]})

        # Submitter
        submit = CTK.Submitter (URL_STAGE_INSTALL_APPLY)
        submit.bind ('submit_success', CTK.DruidContent__JS_if_internal_submit (refresh.JS_to_refresh()))
        submit += radios

        # GUI Layout
        self += submit
        self += refresh
        self.bind ('goto_next_stage', CTK.DruidContent__JS_to_goto_next (self.id))

    class Apply:
        def __call__ (self):
            tipe = CTK.post.get_val ('%s!install_type'%(CFG_PREFIX))

            if tipe == 'download_auto':
                CTK.cfg['%s!app_fetch'%(CFG_PREFIX)] = 'auto'
            elif CTK.cfg.get_val('%s!app_fetch'%(CFG_PREFIX)) == 'auto':
                del (CTK.cfg['%s!app_fetch'%(CFG_PREFIX)])

            return CTK.cfg_apply_post()

    class Refresh_Content (CTK.Box):
        def __init__ (self, refresh, parent_widget):
            CTK.Box.__init__ (self)

            pself   = parent_widget
            default = INSTALL_OPTIONS[0][0]
            method  = CTK.cfg.get_val ('%s!install_type'%(CFG_PREFIX), default)

            if method == 'download_auto':
                self += pself.Download_Auto (pself)
            elif method == 'download_URL':
                self += pself.Download_URL (refresh)
            elif method == 'local_directory':
                self += pself.Local_Directory (refresh)
            else:
                self += CTK.RawHTML ('<h1>%s</h1>' %(_("Unknown method")))

    class Download_Auto (CTK.Box):
        def __init__ (self, pself):
            CTK.Box.__init__ (self)

            submit = CTK.Submitter (URL_STAGE_INSTALL_AUTO_APPLY)
            submit += CTK.Hidden ('%s!app_fetch'%(CFG_PREFIX), pself.default_URL)
            self += submit

        class Apply:
            def __call__ (self):
                return CTK.cfg_apply_post()

    class Download_URL (CTK.Box):
        def __init__ (self, refresh):
            CTK.Box.__init__ (self)

            table = CTK.PropsTable()
            table.Add (_('URL/Path to package'), CTK.TextCfg('%s!app_fetch'%(CFG_PREFIX), False, {'class':'noauto'}), _(NOTE_DOWNLOAD_URL))

            submit = CTK.Submitter (URL_STAGE_INSTALL_URL_APPLY)
            submit.bind ('submit_success', table.JS_to_trigger ('goto_next_stage'))
            submit += table

            self += CTK.RawHTML ("<h3>%s</h3>"%(_('Use a specific Package')))
            self += submit

        class Apply:
            def __call__ (self):
                key = '%s!app_fetch'%(CFG_PREFIX)
                if not CTK.post.get_val(key):
                    return {'ret': 'unsatisfactory', 'errors': {key: _('Cannot be empty')}}

                return CTK.cfg_apply_post()

    class Local_Directory (CTK.Box):
        def __init__ (self, refresh):
            CTK.Box.__init__ (self)

            table = CTK.PropsTable()
            table.Add (_('Directory of the application'), CTK.TextCfg('%s!app_dir'%(CFG_PREFIX), False, {'class':'noauto'}), _(NOTE_APP_DIR))

            submit = CTK.Submitter (URL_STAGE_INSTALL_LOCAL_APPLY)
            submit.bind ('submit_success', table.JS_to_trigger ('goto_next_stage'))
            submit += table

            self += CTK.RawHTML ("<h3>%s</h3>"%(_('Already Installed Software')))
            self += submit

        class Apply:
            def __call__ (self):
                key = '%s!app_dir' %(CFG_PREFIX)
                if not CTK.post.get_val(key):
                    return {'ret': 'unsatisfactory', 'errors': {key: _('Cannot be empty')}}

                return CTK.cfg_apply_post()


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
    ('%s!app_fetch'%(CFG_PREFIX), validation_download_url)
]

URL_STAGE_INSTALL_APPLY       = "/wizard2/stages/install_type/apply"
URL_STAGE_INSTALL_AUTO_APPLY  = "/wizard2/stages/install_type/auto/apply"
URL_STAGE_INSTALL_URL_APPLY   = "/wizard2/stages/install_type/url/apply"
URL_STAGE_INSTALL_LOCAL_APPLY = "/wizard2/stages/install_type/local_dir/apply"

CTK.publish ('^%s'%(URL_STAGE_INSTALL_APPLY),       Stage_Install_Type.Apply,                 validation=VALIDATION_INSTALL_TYPE, method="POST")
CTK.publish ('^%s'%(URL_STAGE_INSTALL_AUTO_APPLY),  Stage_Install_Type.Download_Auto.Apply,   validation=VALIDATION_INSTALL_TYPE, method="POST")
CTK.publish ('^%s'%(URL_STAGE_INSTALL_URL_APPLY),   Stage_Install_Type.Download_URL.Apply,    validation=VALIDATION_INSTALL_TYPE, method="POST")
CTK.publish ('^%s'%(URL_STAGE_INSTALL_LOCAL_APPLY), Stage_Install_Type.Local_Directory.Apply, validation=VALIDATION_INSTALL_TYPE, method="POST")


#
# Installation Directory
#

INSTALL_DIR_OPTIONS = [
    ('auto',       N_('Automatic')),
    ('custom_dir', N_('Install in a custom directory')),
]

class Stage_Install_Directory (Phase_PrevNext):
    def __init__ (self):
        Phase_PrevNext.__init__ (self, _("Installation Directory"))

    def __build_GUI__ (self):
        # Skip phase if it's configuring an already installed app
        install_type = CTK.cfg.get_val ('%s!install_type'%(CFG_PREFIX))
        if install_type == 'local_directory':
            self += CTK.DruidContent_TriggerNext()
            return

        # Refresh
        refresh = CTK.Refreshable({'id': 'wizard2-stage-install-dir-type-refresh'})
        refresh.register (lambda: self.Refresh_Content (refresh, self).Render())

        # Radio buttons
        radios = CTK.RadioGroupCfg ('%s!install_dir_type'%(CFG_PREFIX), INSTALL_DIR_OPTIONS, {'checked': INSTALL_DIR_OPTIONS[0][0]})

        # Submitter
        submit = CTK.Submitter (URL_STAGE_INSTALL_DIR_APPLY)
        submit.bind ('submit_success', CTK.DruidContent__JS_if_internal_submit (refresh.JS_to_refresh()))
        submit += radios

        # GUI Layout
        self += submit
        self += refresh
        self.bind ('goto_next_stage', CTK.DruidContent__JS_to_goto_next (self.id))

    class Apply:
        def __call__ (self):
            dir_type = CTK.post.get_val ('%s!install_dir_type'%(CFG_PREFIX))

            if dir_type == 'auto':
                del (CTK.cfg['%s!app_dir'%(CFG_PREFIX)])
                return CTK.cfg_reply_ajax_ok()

            return CTK.cfg_apply_post()

    class Refresh_Content (CTK.Box):
        def __init__ (self, refresh, parent_widget):
            CTK.Box.__init__ (self)

            pself   = parent_widget
            default = INSTALL_DIR_OPTIONS[0][0]
            method  = CTK.cfg.get_val ('%s!install_dir_type'%(CFG_PREFIX), default)

            if method == 'auto':
                None
            elif method == 'custom_dir':
                self += pself.Custom_Dir (refresh)
            else:
                self += CTK.RawHTML ('<h1>%s</h1>' %(_("Unknown method")))

    class Custom_Dir (CTK.Box):
        def __init__ (self, refresh):
            CTK.Box.__init__ (self)

            table = CTK.PropsTable()
            table.Add (_('Installation directory'), CTK.TextCfg('%s!app_dir'%(CFG_PREFIX), True, {'optional_string': _('Automatic')}), _(NOTE_APP_DIR))

            submit = CTK.Submitter (URL_STAGE_INSTALL_DIR_APPLY)
            submit.bind ('submit_success', table.JS_to_trigger ('goto_next_stage'))
            submit += table

            self += submit


VALIDATION_INSTALL_DIR_TYPE = [
    ('%s!app_dir'%(CFG_PREFIX), validations.parent_is_dir),
]

URL_STAGE_INSTALL_DIR_APPLY = "/wizard2/stages/install_dir_type/apply"

CTK.publish ('^%s'%(URL_STAGE_INSTALL_DIR_APPLY), Stage_Install_Directory.Apply, validation=VALIDATION_INSTALL_DIR_TYPE, method="POST")


#
# Download
#

class Stage_Download (Phase_Cancel):
    def __init__ (self):
        Phase_Cancel.__init__ (self, _("Downloading"))

    def __build_GUI__ (self):
        app_fetch = CTK.cfg.get_val ('%s!app_fetch'%(CFG_PREFIX))
        skip      = False

        # Special cases
        if not app_fetch:
            skip = True

        if not app_fetch.startswith('http'):
            skip = True

            # (app_fetch != 'auto')):


        # Skip the phase?
        if skip:
            self += CTK.RawHTML (js = CTK.DruidContent__JS_to_goto_next (self.id))
            return

        # Report
        report = CTK.Box()
        report += CTK.RawHTML (_("Initiating download.."))

        # Download widget
        down = CTK.Downloader ('package', app_fetch)
        down.bind ('finished', CTK.DruidContent__JS_to_goto_next (self.id))
        down.bind ('stopped',  "") ## TODO!!
        down.bind ('error',    "") ## TODO!!
        down.bind ('update', "$('#%s').html('Downloaded: ' + (event.downloaded / 1024).toFixed() + ' Kb');"%(report.id))

        self += CTK.RawHTML ('<p>%s</p>' %(_('The application is being downloaded. Hold on tight!')))
        self += down
        self += report
        self += CTK.RawHTML (js = down.JS_to_start())


#
# Installation
#

def collect_arguments (installer_params):
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

def check_post_unpack (stage_obj):
    installer = stage_obj.installer

    errors = installer.Check_PostUnpack()
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
        self.Install_Class = Install_Class
        self.next_url      = next_url

    def __build_GUI__ (self):
        install_type = CTK.cfg.get_val ('%s!install_type'%(CFG_PREFIX))

        # Logic Installer
        self.installer_params = {}

        # Commands (first block)
        commands = [
            ({'function': collect_arguments,   'description': "Collecting arguments...", 'params': {'installer_params': self.installer_params}}),
            ({'function': check_params,        'description': "Checking parameters...",  'params': {'installer_params': self.installer_params, 'stage_obj': self, 'Install_Class': self.Install_Class}}),
            ({'function': check_prerequisites, 'description': "Checking requisites...",  'params': {'stage_obj': self}}),
        ]

        # Commands (Download and Unpack are optional)
        if install_type != 'local_directory':
            commands += [
                ({'function': download, 'description': "Downloading...", 'params': {'stage_obj': self}}),
                ({'function': unpack,   'description': "Unpacking...",   'params': {'stage_obj': self}}),
            ]

        # Commands (second block)
        commands += [
            ({'function': check_post_unpack,  'description': "Checking app...", 'params': {'stage_obj': self}}),
            ({'function': configure_cherokee, 'description': "Configuring...",  'params': {'stage_obj': self}}),
        ]

        # GUI
        progress = CommandProgress.CommandProgress (commands, self.next_url)
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

    def __build_GUI__ (self):
        self += CTK.RawHTML ('We are done and dusted!')


URL_STAGE_FINISHED_APPLY = "/wizard2/stages/finished/apply"
CTK.publish ('^%s'%(URL_STAGE_FINISHED_APPLY), Stage_Finished.Apply, method="POST")



#
# Helpers
#

def Register_Standard_VServer_GUI (wizard_name, Install_Class, default_download_URL):
    wizard_url_name = wizard_name.lower().replace(' ', '_')
    url_srv         = '/wizard/vserver/%s' %(wizard_url_name)

    CTK.publish ('^%s$'  %(url_srv), lambda: Phase_Welcome (wizard_name, 'vserver').Render().toStr())
    CTK.publish ('^%s/2$'%(url_srv), lambda: Stage_Install_Type (default_download_URL).Render().toStr())
    CTK.publish ('^%s/3$'%(url_srv), Stage_Install_Directory)
    CTK.publish ('^%s/4$'%(url_srv), Stage_Enter_VServer)
    CTK.publish ('^%s/5$'%(url_srv), Stage_VServer_Logging)
    CTK.publish ('^%s/6$'%(url_srv), Stage_Download)
    CTK.publish ('^%s/7$'%(url_srv), lambda: Stage_Do_Install (Install_Class, "%s/8"%(url_srv)).Render().toStr())
    CTK.publish ('^%s/8$'%(url_srv), Stage_Finished)

def Register_Standard_Directory_GUI (wizard_name, Install_Class, default_download_URL):
    None

def Register_Standard_GUI (*args, **kw):
    Register_Standard_VServer_GUI   (*args, **kw)
    Register_Standard_Directory_GUI (*args, **kw)
