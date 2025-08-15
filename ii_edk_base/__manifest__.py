# -*- coding: utf-8 -*-
{
    'name': 'Document in/out Registry Base',
    'version': '1.0.4',
    'summary': """
    Dinamicki podesiva elektonska delovodna knjiga sa arhiviranjem izvornih dokumenata i procesima odobravanja
    | Proces odobravanja dokumenata
    | Podrzan Koncept paketa dokumenata i odobravanja
    | approve document package
    | Proces odobravanja ugovora
    | Proces odobravanja faktura
    """,
    'category': 'Document Management',
    'author': 'IRVAS',
    'support': 'info@irvas.rs',
    'website': 'https://www.irvas.rs',
    'license': 'OPL-1',
    'price': 120,
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
        'security/security.xml',
        'security/ir.model.access.csv',
        # Views
        'views/menuitems.xml',
        'views/participants.xml',
        'views/books.xml',
        'views/document_package.xml',
        'views/approver_wizard.xml',
        'views/config_parameters.xml',
        'views/document_category.xml',
        'views/document_location_views.xml',
        'views/document_archive.xml',
         'views/documents.xml',
        # 'views/project_kanban_view.xml',
        # Data
        'data/delovodni_broj.xml',
        'data/mail_templates.xml',
        'data/mail_message_subtypes.xml',
    ],
    'depends': ['base', 'mail'],
    'qweb': [],
    'images': [
        'static/description/ii_edk.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
