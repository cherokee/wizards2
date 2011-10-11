
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
import popen

from util import *
from wizards2.common import python

class Install (Wizard2.Wizard):
    def __init__ (self, app_info, config_vserver, config_directory, params=None):
        # Base
        Wizard2.Wizard.__init__ (self, app_info, params)

        # Properties
        self._config_vserver   = config_vserver
        self._config_directory = config_directory

        # Sibling wizard
        self.python_int = python.find_python ('2.4.0', or_greater = True)
        print "self.python_int", self.python_int
