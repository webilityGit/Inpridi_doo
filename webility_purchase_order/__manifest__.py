{
    'name': 'Webility Purchase Order',
    'version': '1.0',
    'summary': 'Inherit purchase order and customize form and report views',
    'category': 'Purchases',
    'author': 'Your Name',
    'website': 'http://yourwebsite.com',
    'depends': ['purchase', 'account', 'product', 'web'],
    'data': [
        'views/purchase_order_views.xml',
        'report/purchase_order_report_templates.xml',
        'report/custom_header.xml',

    ],
    'installable': True,
    'application': False,
}
