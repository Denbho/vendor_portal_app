# -*- coding: utf-8 -*-
{
    'name': "Vendor Portal User Access",

    'author': "Niel John Balogo",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'admin_purchase_requisition', 'admin_request_for_quotation', 'admin_request_for_information',
                'admin_request_for_proposal', 'admin_purchase_bid', 'admin_purchase_order', 'purchase',
                'admin_contracts_and_agreements', 'admin_vendor', 'edts_vendor_si', 'edts'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/vendor_portal_views.xml',
        'views/purchase_order_views.xml',
        'views/menuitem.xml',
    ],
}
