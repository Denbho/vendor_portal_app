# -*- coding: utf-8 -*-
{
    'name': "My Invoice",
    'summary': """My Invoice""",
    'description': """ My Invoice - Website Screen Design """,
    'author': "Srikesh Infotech",
    'category': 'Website',
    'version': '0.1',
    'depends': [
            'website', 'account', 'admin_purchase_order'
        ],
    'data': [
        'views/my_inv_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
