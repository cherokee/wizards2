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


_wizards_objs = []
def load_wizards():
    # Cache Miss
    global _wizards_objs
    if not _wizards_objs:
        # Locate the directory
        wizards_path = os.path.realpath (__file__ + "/../wizards")

        wizards = os.listdir (wizards_path)
        for wizard in wizards:
            # Skip back-ups
            if (wizard.startswith ('.')) or ('#' in wizard) or (not wizard.endswith('.py')):
                continue

            # Load the wizard
            wizard_name = wizard.replace('.py', '')
            wizard_fp   = os.path.join (wizards_path, wizard_name)
            mod = CTK.load_module (wizard_fp, wizard.replace('.py', ''))

            # Update Cache
            _wizards_objs.append (mod)

    return _wizards_objs

class Icon (CTK.Image):
    def __init__ (self, wizard_mod, _props={}):
        icon = wizard_mod.software['icon_small']
        name = wizard_mod.software['name']

        props = _props.copy()
        props['src'] = '/static/images/wizards2/%s'%(icon)
        props['alt'] = "%s logo" %(name)

        if 'class' in props:
            props['class'] += ' wizard-icon'
        else:
            props['class'] = 'wizard-icon'

        CTK.Image.__init__ (self, props)


class CategoryList_Widget (CTK.Box):
    def __init__ (self, category_num, wizards_type):
        CTK.Box.__init__ (self)

        self.category_num  = int(category_num)
        self.category_name = get()[self.category_num]

        # GUI
        wlist  = CTK.List({'class': 'wizard-list'})
        hidden = CTK.Hidden ('wizard')

        submit = CTK.Submitter (URL_CAT_APPLY)
        submit += wlist
        submit += hidden
        submit += CTK.RawHTML (js = JS_WIZARD_LIST %({'list_id': self.id}))
        submit.bind ('submit_success', JS_WIZARD_LIST_SUBMIT %({'hidden': hidden.id}))

        self += submit

        # Fill the list
        for wizard_mod in load_wizards():
            if not 'software' in wizard_mod.__dict__:
                continue

            if wizard_mod.software['category'] != self.category_name:
                continue

            w_name = wizard_mod.software['name']
            w_id   = wizard_mod.software['id']
            w_desc = wizard_mod.software['desc_short']

            wlist.Add ([CTK.Box({'class': 'logo'},  Icon(wizard_mod)),
                        CTK.Box({'class': 'title'}, CTK.RawHTML(_(w_name))),
                        CTK.Box({'class': 'descr'}, CTK.RawHTML(_(w_desc)))],
                       {'wizard': w_id})
        return


def CategoryList_Vsrv():
    # Figure the category
    category_num = re.findall (URL_CAT_LIST_VSRV_R, CTK.request.url)[0]

    content = CategoryList_Widget (category_num, TYPE_VSERVER)
    return content.Render().toJSON()

def CategoryList_Rule():
    # Figure the category
    category_num = re.findall (URL_CAT_LIST_RULE_R, CTK.request.url)[0]

    content = CategoryList_Widget (category_num, TYPE_RULE)
    return content.Render().toJSON()

def CategoryList_Apply():
    return CTK.cfg_reply_ajax_ok()


CTK.publish (URL_CAT_LIST_VSRV_R,   CategoryList_Vsrv)
CTK.publish (URL_CAT_LIST_RULE_R,   CategoryList_Rule)
CTK.publish ('^%s'%(URL_CAT_APPLY), CategoryList_Apply, method="POST")


#
# Utilities
#

_wizard_categories = []
def get():
    global _wizard_categories
    if not _wizard_categories:
        categories = []
        for wizard_mod in load_wizards():
            if not 'software' in wizard_mod.__dict__:
                continue
            categories.append (wizard_mod.software['category'])
        _wizard_categories = list(set(categories))

    return _wizard_categories
