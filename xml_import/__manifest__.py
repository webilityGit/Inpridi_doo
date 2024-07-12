# -*- coding: utf-8 -*-
{
    'name': "Xml import",

    'summary': "An app for seamlessly importing and integrating XML bank statements into Odoo's accounting module",

    'description': """This app facilitates the seamless import of XML bank statements into Odoo's accounting module, parsing the XML files to extract and structure bank statement data efficiently. It enhances the integration process by automating the extraction of transaction details, account numbers, and currencies
    """,

    'author': "Mediod Consulting",
    'website': "https://mediodconsulting.com/",
    "installable": True,
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_import', 'account','account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],


}
