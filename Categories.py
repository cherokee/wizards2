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

URL_CAT_LIST_VSRV   =   '/2wizard/category/vsrv'
URL_CAT_LIST_VSRV_R = r'^/2wizard/category/vsrv/(.*)$'
URL_CAT_LIST_RULE   =   '/2wizard/category/rule'
URL_CAT_LIST_RULE_R = r'^/2wizard/category/rule/(.*)$'
URL_CAT_APPLY       =   '/2wizard/category/apply'

TYPE_VSERVER = 1
TYPE_RULE    = 1 << 2


# Handle 'click' events inside the Wizard Categories list.
#
JS_WIZARD_LIST = """
$('#%(list_id)s').each(function() {
    var box    = $(this);
    var hidden = box.find('input:hidden');

    box.find('li').each(function() {
        var li = $(this);

        li.bind ('click', function(event) {
            box.find('li').removeClass('wizard-list-selected');
            $(this).addClass ('wizard-list-selected');
            hidden.val (li.attr('wizard'));
        });
    });
});
"""

# Generates a 'open_wizard' event whenever the dialog is submitted.
#
JS_WIZARD_LIST_SUBMIT = """
var selected = $('#%(hidden)s').val();
if (selected) {
    $(this).trigger ({type: 'open_wizard', 'wizard': selected});
}

return false;
"""

class CategoryList_Widget (CTK.Box):
    def __init__ (self, category, wizards_type):
        CTK.Box.__init__ (self)
        self.category = category

        # Locate the directory
        wizards_path = os.path.realpath (__file__ + "/../wizards")

        wlist   = CTK.List({'class': 'wizard-list'})
        entries = os.listdir (wizards_path)

        for entry in entries:
            if not entry.startswith("%s-"%(category)):
                continue

            # Wizards of the category
            wizards = os.listdir (os.path.join (wizards_path, entry))

            for wizard in wizards:
                if not wizard.endswith ('.py') or \
                  wizard.startswith ('.') or \
                  '#' in wizard:
                    continue

                wizard_name = wizard.replace('.py', '')
                wizard_fp   = os.path.join (wizards_path, entry, wizard_name)

                mod = CTK.load_module (wizard_fp, wizard.replace('.py', ''))
                wlist.Add ([CTK.RawHTML ("<h1>%s</h1>" %(wizard_fp))],
                           {'wizard': wizard.replace('.py','')})

            # Category found: done
            break

        # Assembling
        hidden = CTK.Hidden ('wizard')
        submit = CTK.Submitter (URL_CAT_APPLY)
        submit += wlist
        submit += hidden
        submit += CTK.RawHTML (js = JS_WIZARD_LIST %({'list_id': self.id}))
        submit.bind ('submit_success', JS_WIZARD_LIST_SUBMIT %({'hidden': hidden.id}))
        self += submit


def CategoryList_Vsrv():
    # Figure the category
    category = re.findall (URL_CAT_LIST_VSRV_R, CTK.request.url)[0]

    # Instance and Render
    content = CategoryList_Widget (category, TYPE_VSERVER)
    return content.Render().toJSON()

def CategoryList_Rule():
    # Figure the category
    category = re.findall (URL_CAT_LIST_RULE_R, CTK.request.url)[0]

    # Instance and Render
    content = CategoryList_Widget (category, TYPE_RULE)
    return content.Render().toJSON()

def CategoryList_Apply():
    return CTK.cfg_reply_ajax_ok()


CTK.publish (URL_CAT_LIST_VSRV_R,   CategoryList_Vsrv)
CTK.publish (URL_CAT_LIST_RULE_R,   CategoryList_Rule)
CTK.publish ('^%s'%(URL_CAT_APPLY), CategoryList_Apply, method="POST")


#
# Utilities
#

def get():
    wizards_path = os.path.realpath (__file__ + "/../wizards")

    categories = {}
    entries = os.listdir (wizards_path)

    for entry in entries:
        tmp = re.findall (r'^(\d\d)-(.+)$', entry)
        if not tmp:
            continue

        categories[tmp[0][1]] = tmp[0][0]

    return categories
