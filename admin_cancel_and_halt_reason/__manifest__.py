# -*- coding: utf-8 -*-
{
    'name': "Admin Cancel and Halt Reasons",
    'author': "Ruel Costob",
    'category': 'tool',
    'version': '13.0.1',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/reset_to_draft.xml',
        'wizard/cancel_reason.xml',
        'wizard/halt_reason.xml',
        'views/admin_cancel_and_halt_reason.xml',
    ],
    'installable': True,
    'auto_install': False,
}
