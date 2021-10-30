# -*- coding: utf-8 -*-
{
    'name': "Admin Vendor Plant Access",
    'summary': """
            Admin Vendor Plant Access
        """,
    'author': "Ruel Costob",
    'category': 'Plant',
    'version': '13.0.1',
    'depends': [
            'base',
            'admin_purchase_order',
            'admin_purchase_requisition',
        ],
    'data': [
        'views/res_users_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
