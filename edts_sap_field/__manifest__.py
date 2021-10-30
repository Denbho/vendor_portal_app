# -*- coding: utf-8 -*-
{
    'name': "EDTS SAP Field",
    'summary': """EDTS SAP field""",
    'description': """EDTS SAP field""",
    'author': "Philip Lloyd Feliprada",
    'version': '13.0.1',
    'depends': [
        'base',
        'admin_purchase_order',
        'edts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/edts_sap_field.xml',
    ],
    'installable': True,
    'auto_install': False,
}
