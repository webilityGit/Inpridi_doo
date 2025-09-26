{
    'name': 'Inpridi Purchase Order i Riportovi',
    'version': '1.0',
    'summary': 'Inherit purchase order and customize form and report views',
    'category': 'Purchases',
    'author': 'Vladimir',
    'website': 'http://yourwebsite.com',
    'depends': ['purchase', 'account'],
    'data': [
        'views/purchase_order_views.xml',
        'report/purchase_order_report_templates.xml',

    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
