# -*- coding: utf-8 -*-
{
    'name': "ii_efaktura",
    'summary': " Dorade neophodne za rad specijalizacije UBL 2.1 standarda za eFakture",
    'description': "Modul sadrzi implermentaciju podrske za UBL 2.1  i cusmatizaciju Poreske uprave  - V14",

    'author': "Irvas Int. doo",
    'website': "http://www.irvas.rs",

    
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_payment_mode', 'base_unece'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/osnov_pdv_izuzece.xml',
        'views/res_partner.xml',
        'views/account_invoice_view.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}
