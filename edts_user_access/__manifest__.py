# -*- coding: utf-8 -*-
{
    'name': "EDTS USER ACCESS",

    'author': "Niel John Balogo",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'edts', 'edts_reason', 'edts_vendor_si'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/edts_views.xml',
        'views/menuitem.xml',
    ],
}
