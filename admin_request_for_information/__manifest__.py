# -*- coding: utf-8 -*-
{
    'name': "Vendor Request For Product Information",
    'summary': """
        Vendor Request For Product Information Management""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'document_approval',
        'admin_purchase_requisition',
        'admin_declined_reason',
        'admin_cancel_and_halt_reason',
        'admin_email_notif',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/reason_to_decline.xml',
        'data/rfi_cron_view.xml',
        'views/request_for_information.xml',
    ],
    'installable': True,
    'auto_install': False,
}
