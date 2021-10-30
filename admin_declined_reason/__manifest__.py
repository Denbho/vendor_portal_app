# -*- coding: utf-8 -*-
{
    'name': "Admin Declined Reason",
    'author': "Ruel Costob",
    'category': 'tool',
    'version': '13.0.1',
    'depends': ['purchase', 'admin_cancel_and_halt_reason'],
    'data': [
        'security/ir.model.access.csv',
        'views/admin_declined_reason.xml',
    ],
    'installable': True,
    'auto_install': False,
}
