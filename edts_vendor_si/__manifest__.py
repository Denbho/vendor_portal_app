# -*- coding: utf-8 -*-
{
    'name': "EDTS and Vendor SI Connection",
    'summary': """EDTS and Vendor SI Connection""",
    'description': """EDTS and Vendor SI Connection""",
    'author': "Philip Lloyd Feliprada",
    'version': '13.0.1',
    'depends': [
        'base',
        'admin_purchase_order',
        'edts',
    ],
    'data': [
        'data/email_templates.xml',
        'wizard/create_edts.xml',
        'views/invoice_delivery_inherit.xml',
        'views/edts_form_views_inherit.xml',
    ],
    'installable': True,
    'auto_install': False
}
