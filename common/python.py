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

"""
Detection of Python interpreter in the system.
"""

import os
import re
import CTK
import popen

from util import *

PYTHON_BINS = [
    'python',
    'python2',
    'python2.7',
    'python2.6',
    'python2.5',
    'python2.4',
]

DEFAULT_PATHS = [
    '/usr/bin',
    '/usr/sfw/bin',
    '/usr/gnu/bin',
    '/usr/local/bin',
    '/opt/local/bin',
    '/opt/python*/bin',
    '/usr/local/python*/bin',
    '/usr/python*/bin',
]


def _is_bin_version (bin, required_version):
    ret = popen.popen_sync ("'%s' -V"%(bin))

    tmp = re.findall (r'Python ([\d.]+)', ret['stderr'], re.M)
    if not tmp: return

    v_int = version_to_int (tmp[0])
    r_int = version_to_int (required_version)

    return v_int >= r_int


def _test_py24(s):
    return _is_bin_version (s, '2.4.0')

def _test_py25(s):
    return _is_bin_version (s, '2.5.0')

def _test_py26(s):
    return _is_bin_version (s, '2.6.0')

def _test_py27(s):
    return _is_bin_version (s, '2.7.0')


def find_python (version, or_greater):
    """Report Python interpeter of specified version. The or_greater
    parameter indicates whether higher versions should also be
    accepted or not.

    find_python() returns the absolute path to the binary of the
    interpreter found."""

    tmp = version.split('.')
    ver = int(''.join(tmp[0:2]))

    if ver <= 27 or or_greater:
        python27 = path_find_binary (PYTHON_BINS,
                                     extra_dirs  = DEFAULT_PATHS,
                                     custom_test = _test_py27)
        if python27:
            return python27

    if ver <=26 or or_greater:
        python26 = path_find_binary (PYTHON_BINS,
                                     extra_dirs  = DEFAULT_PATHS,
                                     custom_test = _test_py26)
        if python26:
            return python26

    if ver <= 25 or or_greater:
        python25 = path_find_binary (PYTHON_BINS,
                                     extra_dirs  = DEFAULT_PATHS,
                                     custom_test = _test_py25)
        if python25:
            return python25

    if ver <= 24 or or_greater:
        python24 = path_find_binary (PYTHON_BINS,
                                     extra_dirs  = DEFAULT_PATHS,
                                     custom_test = _test_py24)
        if python24:
            return python24
