# -*- coding: utf-8 -*-
{
    'name': "Vendor Request For Product Proposal",
    'summary': """
        Vendor Request For Product Proposal Management""",
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
        'wizard/link_rfq_item_to_product_view.xml',
        'wizard/reason_to_decline.xml',
        'data/rfp_cron_view.xml',
        'views/request_for_proposal.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'installable': True,
    'auto_install': False,
}
