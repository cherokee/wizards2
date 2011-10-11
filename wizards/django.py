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

import CTK
import vserver
import Wizard2
import Wizard2_GUI as GUI

from util import *

python_tpl = Wizard2.Load_Template ('Python.py')

DESC_SHORT = """
Django is..
"""

software = {
 'id':             'django',
 'name':           'Django',
 'author':         'Django Community',
 'URL':            'http://www.djangoproject.com/',
 'icon_small':     'django_x96.png',
 'category':       'Frameworks',
 'packager_name':  'Alvaro Lopez Ortega',
 'packager_email': 'alvaro@alobbs.com',
 'desc_short':     DESC_SHORT,
}


#
# Installer
#
class Install (python_tpl.Install):
    def __init__ (self, params):
        python_tpl.Install.__init__ (self,
                                     app_info         = {},
                                     config_vserver   = CONFIG_VSERVER,
                                     config_directory = CONFIG_DIR,
                                     params           = params)


#
# GUI
#
GUI.Register_Standard_GUI (software, Install, None)
