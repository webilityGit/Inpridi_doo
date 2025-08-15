# -*- coding: utf-8 -*-
{
    'name': 'Elektronska delovodna Knjiga -SEF integracija' ,
    'version': '1.0.2',
    'summary': """
     Dinamicki podesiva elektonska delovodna knjiga sa arhiviranjem izvornih dokumenata i procesima odobravanja
    | preuzimanje faktura dobavljaca sa SEF-a
    | preuzimaju se svi prilozi
    | Automatsko kreiranje metapodataka
    """,
    'category': 'Document Management',
    'author': 'IRVAS',
    'support': 'info@irvas.rs',
    'website': 'https://www.irvas.rs',
    'license': 'OPL-1',
    'price': 20,
    'currency': 'EUR',
    'description':
        """
Document Approval Cycle
=======================
This module helps to create multiple custom, flexible and dynamic approval route
for any type of documents based on settings.

Key Features:

 * Any user can initiate unlimited approval process for documents
 * Pre-defined team of approvers or custom flow specified by the initiator
 * Parallel or serial (step-by-step) approval route for documents
 * Multi-level approval workflow for document packages
 * Documents approval by button or by "handwritten" signature (using mouse or touchscreen)
 * Multi Company features of Odoo System are supported
        """,
    'data': [
        # Access
        #'security/security.xml',
        #'security/ir.model.access.csv',
        # Views
        #'views/menuitems.xml',

        'views/document_package.xml',
        #'views/approver_wizard.xml',
        #'views/config_parameters.xml',
        #'views/project_kanban_view.xml',
        # Data

    ],
    'depends': ['ii_edk_base'],
    'qweb': [],
    'images': [
        'static/description/ii_edk.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
