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

import re
import Wizard2

from util import *


FPM_BINS = ['php-fpm', 'php5-fpm']

DEFAULT_PATHS = ['/usr/bin',
                 '/opt/php',
                 '/usr/php/bin',
                 '/usr/sfw/bin',
                 '/usr/gnu/bin',
                 '/usr/local/bin',
                 '/opt/local/bin',
                 '/usr/php/*.*/bin',
                 '/usr/pkg/libexec/cgi-bin',
                 '/usr/sbin',
                 '/usr/local/sbin',
                 '/opt/local/sbin',
                 '/usr/gnu/sbin']

FPM_ETC_PATHS = ['/etc/php*/fpm/*.conf',
                 '/etc/php*/fpm/*.d/*',
                 '/etc/php*-fpm.d/*',
                 '/etc/php*/fpm/php*fpm.conf',
                 '/usr/local/etc/php*fpm.conf',
                 '/opt/php*/etc/php*fpm.conf',
                 '/opt/local/etc/php*/php*fpm.conf',
                 '/etc/php*/*/php*fpm.conf',
                 '/etc/php*/php*fpm.conf']

PHP_DEFAULT_TIMEOUT = '30'


class Install (Wizard2.Wizard):
    def __init__ (self, params):
        # Base
        Wizard2.Wizard.__init__ (self, "PHP FPM", params)

        # Properties
        self.php_bin = None
        self.rule    = None # vserver!1!rule!10
        self.source  = None # source!1

    def Check_Parameters (self):
        errors = self._Check_Params_Install_Type (allows_dir=True, allows_vserver=False)
        return errors

    def Check_Prerequisites (self):
        # Find the binary
        self.php_bin = _find_binary()
        if not self.php_bin:
            return ["Could not locate the php-fpm binary"]

    def Configure_Cherokee (self):
        pre = 'vserver!%s' %(self.params['vserver_num'])

        # Gather information
        self.source = _find_source()
        self.rule   = _find_rule (pre)

        fpm_info = _figure_fpm_settings()
        if not fpm_info:
            return ["Could not determine PHP-fpm settings."]

        # Already configured
        if self.source and self.rule:
            return

        # Add Source
        if not self.source:
            host      = fpm_info['listen']
            conf_file = fpm_info['conf_file']
            php_bin   = self.php_bin

            # Add Cherokee config
            next = CTK.cfg.get_next_entry_prefix('source')

            CTK.cfg['%s!nick'        %(next)] = 'PHP Interpreter'
            CTK.cfg['%s!type'        %(next)] = 'interpreter'
            CTK.cfg['%s!host'        %(next)] = host
            CTK.cfg['%s!interpreter' %(next)] = '%(php_bin)s --fpm-config %(conf_file)s' %(locals())

            web_user  = CTK.cfg.get_val ('server!user',  str(os.getuid()))
            web_group = CTK.cfg.get_val ('server!group', str(os.getgid()))
            php_user  = fpm_info.get ('user',  web_user)
            php_group = fpm_info.get ('group', web_group)

            if php_user != web_user or php_group != web_group:

                # In case FPM has specific UID/GID and differs from
                # Cherokee's, the interpreter must by spawned by root.
                #
                root_user  = 0 # TODO
                root_group = 0 # TODO

                CTK.cfg['%s!user'  %(next)] = root_user
                CTK.cfg['%s!group' %(next)] = root_group

            self.source = _find_source()

        # Timeout
        timeout = CTK.cfg.get_val ('%s!timeout' %(self.source))
        if not timeout:
            timeout = fpm_info['timeout']
        if not timeout:
            timeout = PHP_DEFAULT_TIMEOUT

        # Add behavior rule
        if not self.rule:
            next = CTK.cfg.get_next_entry_prefix('%s!rule'%(pre))
            src_num = self.source.split('!')[-1]

            CTK.cfg['%s!match' %(next)]                     = 'extensions'
            CTK.cfg['%s!match!extensions' %(next)]          = 'php'
            CTK.cfg['%s!match!check_local_file' %(next)]    = '1'
            CTK.cfg['%s!match!final' %(next)]               = '0'
            CTK.cfg['%s!handler' %(next)]                   = 'fcgi'
            CTK.cfg['%s!handler!balancer' %(next)]          = 'round_robin'
            CTK.cfg['%s!handler!balancer!source!1' %(next)] = src_num
            CTK.cfg['%s!handler!error_handler' %(next)]     = '1'
            CTK.cfg['%s!encoder!gzip' %(next)]              = '1'
            CTK.cfg['%s!timeout' %(next)]                   = timeout

            # Front-Line Cache
            if int(self.params.get('flcache', "1")):
                CTK.cfg['%s!flcache' %(next)]               = 'allow'

            # Normalization
            CTK.cfg.normalize('%s!rule'%(pre))

            self.rule = _find_rule(pre)

        # Index files
        indexes = filter (None, CTK.cfg.get_val ('%s!directory_index' %(pre), '').split(','))
        if not 'index.php' in indexes:
            indexes.append ('index.php')
            CTK.cfg['%s!directory_index' %(pre)] = ','.join(indexes)


#
# Helper functions
#

def _find_binary ():
    return path_find_binary (FPM_BINS,
                             extra_dirs  = DEFAULT_PATHS,
                             custom_test = _test_php_fcgi)

def _test_php_fcgi (path):
    f = os.popen('%s -v' %(path), 'r')
    output = f.read()
    try: f.close()
    except: pass
    return 'fcgi' in output

def _find_source():
    for binary in FPM_BINS:
        source = cfg_source_find_interpreter (binary)
        if source:
            return source

def _find_rule (key):
    return cfg_vsrv_rule_find_extension (key, 'php')

def _figure_fpm_settings():
    # Find config file
    paths = []
    for p in FPM_ETC_PATHS:
        paths.append (p)
        paths.append ('%s-*' %(p))

    # Helper functions
    get_regex = lambda key: r'^\s*' + key.replace('.','\.') + '\s*=\s*(.+?)\s*$'
    findall   = lambda key: re.findall (get_regex(key), content, re.M)

    fpm_info      = {}
    FPM_CONF_KEYS = ('listen', 'request_terminate_timeout', 'user', 'group', 'pm.status_path', 'ping.path')

    # For each configuration file
    for conf_file in path_eval_exist (paths):
        # Read
        try:
            content = open (conf_file, 'r').read()
        except:
            continue

        # Filename
        if not fpm_info.get('conf_file'):
            if '.conf' in conf_file:
                fpm_info['conf_file'] = conf_file

        # Keys
        for conf_key in FPM_CONF_KEYS:
            if not fpm_info.has_key(conf_key):
                tmp = findall (conf_key)
                if tmp:
                    fpm_info[conf_key] = tmp[0]

    # Rename keys
    if fpm_info.has_key('request_terminate_timeout'):
        fpm_info['timeout'] = fpm_info.pop('request_terminate_timeout')

    # Set last minute defaults
    if not fpm_info.get('timeout'):
         fpm_info['timeout'] = PHP_DEFAULT_TIMEOUT

    if not fpm_info.get('listen'):
         fpm_info['listen'] = "127.0.0.1"

    return fpm_info
