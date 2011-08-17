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
import urllib2

import CTK
import vserver
import Wizard2
import Wizard2_GUI as GUI
from util import *

php_tpl = Wizard2.Load_Template ('PHP.py')

#
# Configuration
#
CONFIG_VSERVER = """
vserver!%(vserver_num)s!nick = %(vserver_nick)s
vserver!%(vserver_num)s!document_root = %(app_dir)s
vserver!%(vserver_num)s!directory_index = index.php,index.html

%(pre_rule_plus3)s!match = request
%(pre_rule_plus3)s!match!request = ^/([0-9]+)$
%(pre_rule_plus3)s!handler = redir
%(pre_rule_plus3)s!handler!rewrite!1!regex = ^/([0-9]+)$
%(pre_rule_plus3)s!handler!rewrite!1!show = 0
%(pre_rule_plus3)s!handler!rewrite!1!substring = /index.php?q=/node/$1

%(pre_rule_plus2)s!match = request
%(pre_rule_plus2)s!match!request = \.(engine|inc|info|install|module|profile|test|po|sh|.*sql|theme|tpl(\.php)?|xtmpl|svn-base)$|^(code-style\.pl|Entries.*|Repository|Root|Tag|Template|all-wcprops|entries|format)$
%(pre_rule_plus2)s!handler = custom_error
%(pre_rule_plus2)s!handler!error = 403

%(pre_rule_plus1)s!match = fullpath
%(pre_rule_plus1)s!match!fullpath!1 = /
%(pre_rule_plus1)s!handler = redir
%(pre_rule_plus1)s!handler!rewrite!1!show = 0
%(pre_rule_plus1)s!handler!rewrite!1!substring = /index.php

# IMPORTANT: The PHP rule comes here

%(pre_rule_minus1)s!match = exists
%(pre_rule_minus1)s!match!iocache = 1
%(pre_rule_minus1)s!match!match_any = 1
%(pre_rule_minus1)s!match!match_index_files = 0
%(pre_rule_minus1)s!match!match_only_files = 1
%(pre_rule_minus1)s!handler = file

%(pre_rule_minus2)s!match = default
%(pre_rule_minus2)s!handler = redir
%(pre_rule_minus2)s!handler!rewrite!1!show = 0
%(pre_rule_minus2)s!handler!rewrite!1!regex = ^/(.*)\?(.*)$
%(pre_rule_minus2)s!handler!rewrite!1!substring = /index.php?q=$1&$2
%(pre_rule_minus2)s!handler!rewrite!2!show = 0
%(pre_rule_minus2)s!handler!rewrite!2!regex = ^/(.*)$
%(pre_rule_minus2)s!handler!rewrite!2!substring = /index.php?q=$1
"""

CONFIG_DIR = """
%(pre_rule_plus4)s!match = request
%(pre_rule_plus4)s!match!request = ^%(target_directory)s/([0-9]+)$
%(pre_rule_plus4)s!handler = redir
%(pre_rule_plus4)s!handler!rewrite!1!regex = ^%(target_directory)s/([0-9]+)$
%(pre_rule_plus4)s!handler!rewrite!1!show = 0
%(pre_rule_plus4)s!handler!rewrite!1!substring = %(target_directory)s/index.php?q=/node/$1

%(pre_rule_plus3)s!match = request
%(pre_rule_plus3)s!match!request = %(target_directory)s/$
%(pre_rule_plus3)s!handler = redir
%(pre_rule_plus3)s!handler!rewrite!1!show = 0
%(pre_rule_plus3)s!handler!rewrite!1!substring = %(target_directory)s/index.php

%(pre_rule_plus2)s!match = directory
%(pre_rule_plus2)s!match!directory = %(target_directory)s
%(pre_rule_plus2)s!match!final = 0
%(pre_rule_plus2)s!document_root = %(app_dir)s

%(pre_rule_plus1)s!match = and
%(pre_rule_plus1)s!match!left = directory
%(pre_rule_plus1)s!match!left!directory = %(target_directory)s
%(pre_rule_plus1)s!match!right = request
%(pre_rule_plus1)s!match!right!request = \.(engine|inc|info|install|module|profile|test|po|sh|.*sql|theme|tpl(\.php)?|xtmpl|svn-base)$|^(code-style\.pl|Entries.*|Repository|Root|Tag|Template|all-wcprops|entries|format)$
%(pre_rule_plus1)s!handler = custom_error
%(pre_rule_plus1)s!handler!error = 403

# IMPORTANT: The PHP rule comes here

%(pre_rule_minus1)s!match = and
%(pre_rule_minus1)s!match!left = directory
%(pre_rule_minus1)s!match!left!directory = %(target_directory)s
%(pre_rule_minus1)s!match!right = exists
%(pre_rule_minus1)s!match!right!iocache = 1
%(pre_rule_minus1)s!match!right!match_any = 1
%(pre_rule_minus1)s!match!right!match_index_files = 0
%(pre_rule_minus1)s!match!right!match_only_files = 1
%(pre_rule_minus1)s!handler = file

%(pre_rule_minus2)s!match = directory
%(pre_rule_minus2)s!match!directory = %(target_directory)s
%(pre_rule_minus2)s!handler = redir
%(pre_rule_minus2)s!handler!rewrite!1!show = 0
%(pre_rule_minus2)s!handler!rewrite!1!regex = ^/(.*)\?(.*)$
%(pre_rule_minus2)s!handler!rewrite!1!substring = %(target_directory)s/index.php?q=$1&$2
%(pre_rule_minus2)s!handler!rewrite!2!show = 0
%(pre_rule_minus2)s!handler!rewrite!2!regex = ^/(.*)$
%(pre_rule_minus2)s!handler!rewrite!2!substring = %(target_directory)s/index.php?q=$1
"""

#
# Public info
#
DESC_SHORT = """Drupal is a content management system software that is
much-beloved by a large and thriving developer community. Its main
features are flexibility, simplicity, utility, modularity,
extensibility and maintainability in the code."""

software = {
 'id':          'drupal',
 'name':        'Drupal',
 'author':      'Drupal Community',
 'URL':         'http://drupal.org/',
 'icon_small':  'drupal_x96.png',
 'desc_short':  DESC_SHORT,
 'category':    'Content Management',
}


#
# Utils
#
tarball_cache = None
def get_tarball():
    global tarball_cache
    if not tarball_cache:
        html  = urllib2.urlopen ("http://drupal.org/project/drupal").read()
        downs = re.findall (r'href="(http://ftp.drupal.org/files/projects/drupal-\d+\.\d+.tar.gz)"', html)
        downs.sort()
        tarball_cache = downs[-1]
    return tarball_cache

#
# Installer
#
class Install (php_tpl.Install):
    def __init__ (self, params):
        php_tpl.Install.__init__ (self,
                                  app_info         = software,
                                  config_vserver   = CONFIG_VSERVER,
                                  config_directory = CONFIG_DIR,
                                  default_download = get_tarball,
                                  params           = params)

    def Check_Prerequisites (self):
        return php_tpl.Install.Check_Prerequisites (self)

    def _Handle_Unpacking (self):
        errors = php_tpl.Install._Handle_Unpacking (self)
        if errors: return errors

        # Update app_dir, WP is in a subdir
        self._Update_app_dir ("drupal-\d+.\d+")

    def Check_PostUnpack (self):
        return self._Check_File_Exists ('includes/menu.inc')

    def Configure_Cherokee_PostApply (self):
        if self.type == 'vserver':
            vserver.Add_Usual_Static_Files (self.cfg_replacements['pre_rule_plus1'])

#
# GUI
#
GUI.Register_Standard_GUI (software, Install, get_tarball)
