# -*- coding: utf-8 -*-
{
    'name': "Admin Vendor API Connections",
    'summary': """
            Connecting to SAP:
            * Tagging of PO Been accepted or Declined;
            * Creation of Vendor to SAP
        """,
    'author': "Dennis Boy Silva",
    'category': 'Tool',
    'version': '13.0.1',
    'depends': [
        'admin_api_connector',
        'purchase',
        'admin_purchase_order',
        'admin_declined_reason',
        'admin_vendor',
        'admin_vendor_portal_access'
        ],
    'data': [
    ],
    'installable': True,
    'auto_install': False,
}
