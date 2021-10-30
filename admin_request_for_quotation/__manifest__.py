# -*- coding: utf-8 -*-
{
    'name': "Vendor Request For Quotation",
    'summary': """
        Vendor Request For Quotation Management""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'product',
        'purchase',
        'admin_declined_reason',
        'document_approval',
        'admin_cancel_and_halt_reason',
        'admin_email_notif',
        ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'data/rfq_cron_view.xml',
        'wizard/select_rfq_vendor.xml',
        'wizard/reason_to_decline.xml',
        'views/rfq.xml'
    ],
    'installable': True,
    'auto_install': False,
}
