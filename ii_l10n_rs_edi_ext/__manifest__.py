{
    'author': 'Irvas',
    'name': 'Serbia - eFaktura E-invoicing - irvas ekstenzija',
    'version': '1.0',
    'category': 'Accounting/Localizations/EDI',
    'description': """
eFaktura E-invoice implementation for Serbia ekstension
    """,
    'summary': "E-Invoice implementation for Serbia",
    'countries': ['rs'],
    'depends': [
       'l10n_rs_edi',
        'account_edi_ubl_cii',
        'account_edi_ubl_cii_tax_extension',  # ovaj modul sadryi tipove PDV I razloge ...
    ],


    'data': [
        'views/account_move.xml',
        #'views/account_move_line.xml',
        'views/ii_pdv_views.xml',
        #'views/osnov_pdv_izuzece.xml',
    #    'wizard/account_move_send_views.xml',
        'data/ubl_rs_invoice.xml',
        'data/ii.pdv.category.csv',
        'data/ii.pdv.exemption.reason.csv',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
