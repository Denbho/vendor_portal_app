# -*- coding: utf-8 -*-
{
    'name': "Admin Product",
    'summary': """
            Inherit module product.
        """,
    'author': "Ruel Costob",
    'category': 'Product',
    'version': '13.0.1',
    'depends': [
        'product',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
