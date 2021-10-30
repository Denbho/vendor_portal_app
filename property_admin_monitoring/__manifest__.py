# -*- coding: utf-8 -*-
{
    'name': "Property Admin Monitoring",
    'summary': """
        Property Admin Monitoring""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'Accounting',
    'version': '0.1',
    'depends': [
        'hr',
        'base',
        'mail',
        'helpdesk',
        'helpdesk_sale',
        'localize_address',
        'company_and_branch_code',
        'contact_personal_information',
        'contact_unique_id_number',
        'admin_api_connector',
        ],
    'data': [
        'data/data.xml',
        'data/scheduler_data.xml',
        'data/email_templates.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/property.xml',
        'wizard/account_cancel.xml',
        'wizard/validate_submitted_docs.xml',
        'wizard/reject_credit_committee_approval.xml',
        'wizard/helpdesk_ticket_closing.xml',
        'views/credit_committee_approval.xml',
        'views/sale_monitoring.xml',
        'views/payments.xml',
        'views/helpdesk.xml',
        'views/partner.xml',
    ],
    'installable': True,
    'auto_install': False,
}
