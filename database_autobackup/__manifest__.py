# -*- coding: utf-8 -*-

{
    'name': 'Database Auto Backup (filestore)',
    'author': 'Khubab & Ghazali',
    'summary': 'Database auto backup application, includes filestore option.',
    'version': '1.0',
    'license': 'OPL-1',
    'category': 'Tools',
    'description': """
Database Auto Backup
========
""",
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'data/autobackup_cron.xml',
        'data/autobackup_data.xml',
        'views/autobackup_config_settings_views.xml'
    ],
    'images': ['static/description/thumbnails.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
