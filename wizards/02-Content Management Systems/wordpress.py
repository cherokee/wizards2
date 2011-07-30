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
import re
import CTK
import vserver
import Wizard2
import Wizard2_GUI

from util import *

CONFIG_VSERVER = """
vserver!%(vserver_num)s!nick = %(vserver_nick)s
vserver!%(vserver_num)s!document_root = %(app_dir)s/wordpress
vserver!%(vserver_num)s!directory_index = index.php,index.html

# The PHP rule comes here

%(pre_rule_minus2)s!match = fullpath
%(pre_rule_minus2)s!match!fullpath!1 = /wp-admin
%(pre_rule_minus2)s!handler = redir
%(pre_rule_minus2)s!handler!rewrite!1!show = 0
%(pre_rule_minus2)s!handler!rewrite!1!substring = /wp-admin/

%(pre_rule_minus3)s!match = exists
%(pre_rule_minus3)s!match!iocache = 1
%(pre_rule_minus3)s!match!match_any = 1
%(pre_rule_minus3)s!match!match_only_files = 1
%(pre_rule_minus3)s!handler = common
%(pre_rule_minus3)s!handler!iocache = 1
%(pre_rule_minus3)s!handler = common
%(pre_rule_minus3)s!handler!allow_dirlist = 0

vserver!%(vserver_num)s!rule!1!match = default
vserver!%(vserver_num)s!rule!1!handler = redir
vserver!%(vserver_num)s!rule!1!handler!rewrite!1!show = 0
vserver!%(vserver_num)s!rule!1!handler!rewrite!1!regex = /?(.*)
vserver!%(vserver_num)s!rule!1!handler!rewrite!1!substring = /index.php?/$1
"""

CONFIG_DIR = """
%(pre_rule_plus1)s!match = directory
%(pre_rule_plus1)s!match!directory = %(directory)s
%(pre_rule_plus1)s!match!final = 0
%(pre_rule_plus1)s!document_root = %(app_dir)s/wordpress

# The PHP rule comes here

%(pre_rule_minus1)s!match = fullpath
%(pre_rule_minus1)s!match!fullpath!1 = %(directory)s/wp-admin
%(pre_rule_minus1)s!handler = redir
%(pre_rule_minus1)s!handler!rewrite!10!show = 0
%(pre_rule_minus1)s!handler!rewrite!10!substring = %(directory)s/wp-admin/

%(pre_rule_minus3)s!match = and
%(pre_rule_minus3)s!match!final = 1
%(pre_rule_minus3)s!match!left = directory
%(pre_rule_minus3)s!match!left!directory = %(directory)s
%(pre_rule_minus3)s!match!right = exists
%(pre_rule_minus3)s!match!right!iocache = 1
%(pre_rule_minus3)s!match!right!match_any = 1
%(pre_rule_minus3)s!match!right!match_index_files = 1
%(pre_rule_minus3)s!match!right!match_only_files = 1
%(pre_rule_minus3)s!handler = common
%(pre_rule_minus3)s!handler!allow_dirlist = 0
%(pre_rule_minus3)s!handler!allow_pathinfo = 0
%(pre_rule_minus3)s!handler!iocache = 1

%(pre_rule_minus4)s!match = request
%(pre_rule_minus4)s!match!request = %(directory)s/?(.*)
%(pre_rule_minus4)s!handler = redir
%(pre_rule_minus4)s!handler!rewrite!1!show = 0
%(pre_rule_minus4)s!handler!rewrite!1!substring = %(directory)s/index.php?/$1
"""

TARBALL = "http://wordpress.org/latest.tar.gz"
php_fpm = Wizard2.Load_Module ('01-Development Platforms/php-fpm.py')


class Install (Wizard2.Wizard):
    def __init__ (self, params):
        # Base
        Wizard2.Wizard.__init__ (self, "Wordpress", params)

        # Sibling wizard
        self.php = self._Register_Child_Wizard (php_fpm.Install (params))

    def Check_Parameters (self):
        # PHP
        errors = self.php.Check_Parameters()

        # App location
        errors += self._Check_Params_Install_Type (allows_dir=True, allows_vserver=True)
        errors += self._Check_Software_Location()

        return errors

    def Check_Prerequisites (self):
        # PHP
        errors = self.php.Check_Prerequisites()
        if errors: return errors

        # Wordpress
        errors = self._Handle_Download (tarball=TARBALL)
        if errors: return errors

        errors = self._Handle_Unpacking ()
        if errors: return errors

    def Configure_Cherokee (self):
        # PHP
        errors = self.php.Configure_Cherokee()
        if errors: return errors

        # Collect substitutions
        props = cfg_get_surrounding_repls ('pre_rule', self.php.rule)
        props.update (self.__dict__)

        # Wordpress
        if self.type == 'directory':
            # Apply the configuration
            config = CONFIG_DIR %(props)
            CTK.cfg.apply_chunk (config)

        elif self.type == 'vserver':
            # Apply the configuration
            config = CONFIG_VSERVER %(props)
            CTK.cfg.apply_chunk (config)

            # Static files
            vserver.Add_Usual_Static_Files (props['pre_rule_plus1'])

            # Normalize rules
            CTK.cfg.normalize ('vserver!%s!rule'%(self.vserver_num))


#
# GUI
#

CTK.publish ('^/wizard/vserver/wordpress$',   lambda: Wizard2_GUI.Phase_Welcome ('Wordpress', 'vserver').Render().toStr())
CTK.publish ('^/wizard/vserver/wordpress/2$', Wizard2_GUI.Stage_Install_Type)
CTK.publish ('^/wizard/vserver/wordpress/3$', Wizard2_GUI.Stage_Enter_VServer)
CTK.publish ('^/wizard/vserver/wordpress/4$', Wizard2_GUI.Stage_VServer_Logging)
CTK.publish ('^/wizard/vserver/wordpress/5$', lambda: Wizard2_GUI.Stage_Do_Install (Install, "/wizard/vserver/wordpress/6").Render().toStr())
CTK.publish ('^/wizard/vserver/wordpress/6$', Wizard2_GUI.Stage_Finished)
