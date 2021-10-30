# -*- coding: utf-8 -*-
{
    'name': "My Purchase Order",
    'summary': """My Purchase Order""",
    'description': """ My Purchase Order - Website Screen Design """,
    'author': "Srikesh Infotech",
    'category': 'Website',
    'version': '0.1',
    'depends': [
            'website', 'purchase', 'website_sale',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/po_notification_data.xml',
        'data/po_mail_data.xml',
        'views/my_po_templates.xml',
        'report/watermark.xml',
        'views/my_po_notification.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
