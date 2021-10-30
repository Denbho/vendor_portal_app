# -*- coding: utf-8 -*-
{
    'name': "Admin Vendor",
    'summary': """
            Admin Vendor
        """,
    'author': "Ruel Costob",
    'category': 'Base',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'admin_purchase_bid',
        'document_approval',
        'admin_email_notif',
        'admin_sap_field',
        'property_admin_monitoring',
        'admin_cancel_and_halt_reason',
        'admin_product',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduler_data.xml',
        'wizard/link_vendor_item_to_product.xml',
        'wizard/select_evaluation_type.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'auto_install': False,
}
