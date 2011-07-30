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

USUAL_STATIC_FILES = ['/favicon.ico', '/robots.txt', '/crossdomain.xml',
                      '/sitemap.xml', '/sitemap.xml.gz']


def Add_Usual_Static_Files (rule_pre, files = USUAL_STATIC_FILES):
    CTK.cfg['%s!match'%(rule_pre)]           = 'fullpath'
    CTK.cfg['%s!handler'%(rule_pre)]         = 'file'
    CTK.cfg['%s!handler!iocache'%(rule_pre)] = '1'
    CTK.cfg['%s!encoder!gzip'%(rule_pre)]    = '0'
    CTK.cfg['%s!encoder!deflate'%(rule_pre)] = '0'
    CTK.cfg['%s!expiration'%(rule_pre)]      = 'time'
    CTK.cfg['%s!expiration!time'%(rule_pre)] = '1h'

    n = 1
    for file in files:
        CTK.cfg['%s!match!fullpath!%d'%(rule_pre,n)] = file
        n += 1

