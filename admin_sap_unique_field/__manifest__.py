# -*- coding: utf-8 -*-
{
    'name': "Property Admin Monitoring - SAP Field",
    'summary': """
        SAP Unique client ID field""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'tool',
    'version': '0.1',
    'depends': [
        'base',
        'company_and_branch_code',
        'partner_autocomplete',
        'property_admin_monitoring'
        ],
    'data': [
        'view/property_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
