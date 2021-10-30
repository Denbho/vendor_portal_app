# -*- coding: utf-8 -*-
{
    'name': "Admin Purchase Order",
    'summary': """
            Purchase Order
        """,
    'author': "Ruel Costob",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'account',
        'purchase',
        'admin_purchase_requisition',
        'admin_declined_reason',
        ],
    "post_init_hook": "post_init_hook",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/scheduler.xml',
        'wizard/countered_delivery.xml',
        'wizard/countered_sales_invoice.xml',
        'wizard/allocate_si_amount.xml',
        'views/invoice_delivery.xml',
        'views/purchase_order_view.xml',
        'views/document_requirement.xml',
        'views/admin_po_document_type.xml',
    ],
    'installable': True,
    'auto_install': False,
}
