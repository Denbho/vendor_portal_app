# -*- coding: utf-8 -*-
{
    'name': "Admin Vendor Client Extend",
    'summary': """
            Allows user to extend the vendor to other client server or company
        """,
    'author': "Dennis Boy Silva",
    'category': 'Base',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'document_approval',
        'admin_vendor',
        'admin_sap_unique_field'
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/vendor.xml'
    ],
    'installable': True,
    'auto_install': False,
}
