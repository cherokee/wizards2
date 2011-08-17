# -*- coding: utf-8 -*-
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
import re
import CTK
import popen
import Install_Log


class Wizard (object):
    """
    self.params
    -----------
    type :        'directory' or 'vserver'
    vserver_num:  10, 20, ..
    directory:    /webdir
    vserver_nick: example.com
    app_fetch:    /tmp/bat.tgz, http://_/foo.tgz
    app_dir:      /var/www_apps/worpress
    targz_path:   /tmp/foobar.tgz
    """

    type       = property (lambda s: s.params.get('type'),       lambda s,v: s.params.update({'type': v}))
    app_dir    = property (lambda s: s.params.get('app_dir'),    lambda s,v: s.params.update({'app_dir': v}))
    app_fetch  = property (lambda s: s.params.get('app_fetch'),  lambda s,v: s.params.update({'app_fetch': v}))
    targz_path = property (lambda s: s.params.get('targz_path'), lambda s,v: s.params.update({'targz_path': v}))

    def __init__ (self, app_info, params=None):
        self.app_info = app_info

        # Do not copy the params. We do want a child wizard to
        # reference its parent params dict.
        #
        self.params = params or {}

    #
    # Public
    #
    def Check_Parameters (self):
        return []

    def Check_Prerequisites (self):
        return []

    def Download (self):
        return []

    def Unpack (self):
        return []

    def Check_PostUnpack (self):
        return []

    def Configure_Cherokee (self):
        return []

    def Configure_Cherokee_PostApply (self):
        return []

    #
    # Protected
    #
    def _Register_Child_Wizard (self, wizard_obj):
        wizard_obj.params = self.params
        return wizard_obj

    def _Check_Params_Install_Type (self, allows_dir, allows_vserver):
        errors = []

        # Type
        if not self.type:
            errors += ["Missing 'type' property. Suitable values are: 'vserver' or 'directory'"]
            return errors

        if not self.type in ['directory', 'vserver']:
            errors += ["Invalid 'type' value. It must be either 'vserver' or 'directory'"]
            return errors

        # Directory
        if self.type == 'directory':
            vserver_num = self.params.get('vserver_num')
            directory   = self.params.get('directory')

            if not vserver_num:
                errors += ["Property 'vserver_num' missing"]
            elif not vserver_num.isdigit():
                errors += ["Invalid value of the 'directory' property: it must be a number"]

            if not directory:
                errors += ["Property 'directory' missing"]
            elif directory[0] != '/':
                errors += ["Invalid value of the 'directory' property: it must be a directory path"]

        # Virtual Server
        elif self.type == 'vserver':
            vserver_nick = self.params.get('vserver_nick')
            vserver_num  = self.params.get('vserver_num')

            if not vserver_nick:
                errors += ["Property 'vserver_nick' missing"]

            if vserver_num and CTK.cfg['vserver!%s'%(vserver_num)]:
                errors += ["Invalid 'vserver_num'. Virtual server ID already in use."]
            else:
                self.params['vserver_num'] = CTK.cfg.get_next_entry_prefix ('vserver').split ('!')[-1]

        return errors

    def _Check_Software_Location (self):
        errors = []

        if self.app_fetch:
            return []

        if not self.app_dir:
            errors += ["The 'app_dir' property must be provided"]

        return errors

    def _Handle_Download (self, tarball=None):
        errors   = []
        url      = None
        pkg_path = None

        # In case of running from the GUI, the file is downloaded by
        # now, so the only thing left to do is to update the params.
        if self.app_fetch and self.app_fetch.startswith ("http:"):
            if CTK.DownloadEntry_Exists (self.app_fetch):
                down_entry = CTK.DownloadEntry_Factory (self.app_fetch)
                self.targz_path = down_entry.target_path
                return []

        # Auto
        if not self.app_fetch or self.app_fetch == 'auto':
            url = tarball

        # Static file
        elif self.app_fetch[0] == '/':
            if not os.path.exists (self.app_fetch):
                errors += [_("File or Directory not found: %(app_path)s") %({'app_path': self.app_fetch})]
                return errors

            if os.path.isdir(self.app_fetch):
                self.targz_path = self.app_dir
            else:
                self.targz_path = self.app_fetch

        # Download the software
        else:
            url = self.app_fetch

        if url:
            Install_Log.log ("Downloading: %s" %(url))

            self.downloader = CTK.DownloadEntry_Factory (url)
            self.downloader.start()

            while self.downloader.isAlive():
                self.downloader.join(1)
                if self.downloader.size <= 0:
                    Install_Log.log ("Downloaded %d bytes..." %(self.downloader.downloaded))
                else:
                    Install_Log.log ("Downloaded %d / %d (%d%%)..." %(self.downloader.downloaded, self.downloader.size, (self.downloader.downloaded * 100 / self.downloader.size)))

            self.targz_path = self.downloader.target_path
            Install_Log.log ("Download completed: %s" %(self.targz_path))

        return []

    def _Handle_Unpacking (self):
        if not self.targz_path:
            return []

        assert self.app_dir

        # Create the app directory
        if not os.path.exists(self.app_dir):
            os.makedirs (self.app_dir)

        # Unpack
        command = "gzip -dc '%s' | tar xfv -" %(self.targz_path)
        Install_Log.log ("(cd: %s): %s" %(self.app_dir, command))

        ret = popen.popen_sync (command, cd=self.app_dir)
        Install_Log.log (ret['stdout'])
        Install_Log.log (ret['stderr'])

        return []

    def _Update_app_dir (self, re_filter=None):
        assert self.app_dir

        for f in os.listdir (self.app_dir):
            fp = os.path.join (self.app_dir, f)
            if re_filter:
                if not re.match (re_filter, f):
                    continue

            Install_Log.log ("Updating app_dir: %s to %s" %(self.app_dir, fp))
            self.app_dir = fp
            return []

        Install_Log.log ("app_dir was not updated: %s" %(self.app_dir))
        return []

    def _Handle_Log_VServer (self):
        vserver_num = self.params.get('vserver_num')
        cp_vsrv_log = self.params.get('cp_vsrv_log')

        # For VServers only
        if not self.type == 'vserver':
            return []

        # Log config cloning
        if cp_vsrv_log:
            vsrv_1st = CTK.cfg.get_lowest_entry ('vserver')

            if CTK.cfg['vserver!%s!logger' %(vsrv_1st)]:
                CTK.cfg.clone ('vserver!%s!logger' %(vsrv_1st), 'vserver!%s!logger' %(vserver_num))

            if CTK.cfg['vserver!%s!error_writer'%(vsrv_1st)]:
                CTK.cfg.clone ('vserver!%s!error_writer' %(vsrv_1st), 'vserver!%s!error_writer' %(vserver_num))

        return []


    #
    # Checks
    #
    def _Check_File_Exists (self, filename):
        assert self.app_dir
        assert self.app_info and self.app_info.has_key('name')

        errors = []
        fpath  = os.path.join (self.app_dir, filename)

        if not os.path.exists (fpath):
            errors += [_("The '%(app_dir)s' directory does not look like a %(name)s directory: The %(filename)s file is missing.")
                       %({'app_dir': self.app_dir, 'name': self.app_info['name'], 'filename': filename})]

        return errors

def Load_Module (path):
    tmp = path.split('/')
    dsc = tmp[-1].replace('.py','')

    php_mod_path = os.path.realpath (__file__ + '/../wizards/' + path)
    return CTK.load_module_pyc (php_mod_path, dsc)

def Load_Template (path):
    tmp = path.split('/')
    dsc = tmp[-1].replace('.py','')

    php_mod_path = os.path.realpath (__file__ + '/../templates/' + path)
    return CTK.load_module_pyc (php_mod_path, dsc)

