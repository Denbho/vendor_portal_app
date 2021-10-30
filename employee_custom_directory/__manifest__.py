# -*- coding: utf-8 -*-
{
    'name': "Employee Directory",

    'summary': """
        Employee Custom Directory""",

    'description': """
        Employee Custom Directory 
    """,

    'author': "Elmo Bunani",
    'category': 'Extra Tools',
    'version': '13.0.1.0.0',
    'depends': [
        'base',
        'hr',
        'mail',
        'contact_personal_information',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/emp_custom_directory_view.xml',
        'data/emp_directory_data.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}
