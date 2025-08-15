from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from .selection import (ApprovalMethods, DocumentState, ApproverState, ApprovalStep, DocumentVisibility,
                 DocumentSource, DocumentMove, SaveFormat, IzvorniOblik, DocumentArchiveState, DocumentGroupType)
from datetime import datetime
import requests
import base64
import logging
_logger = logging.getLogger(__name__)


_editable_states = {
    False: [('readonly', False)],
    'draft': [('readonly', False)],
    }
class DocArhBookLine(models.Model):
    _name = 'ii.eal.book'
    _inherit = ['mail.thread']
    _description = 'Collection of documents organised as Archive Book'
    archive_date = fields.Date(
        string='Archive Date',
        required=True,
        readonly=True,
        default=datetime.now(),
        states=_editable_states,
        tracking=True,
    )

    book_year = fields.Char(
        string='Year',
        required=True,
        translate=True,
        default="2023",
    )

    subject = fields.Char(  # sadrzaj
        string='Subject',
        copy='False',
        readonly=False,
    )
    document_category = fields.Char(  # Klasifikacija dokumenta
        string='Clasification',
        copy='False',
        readonly=False,
    )
    rok_cuvanja_meseci = fields.Integer(
        string='Storage Period in mounths',
        required=True,
    )
    rok_cuvanja_godina = fields.Char(
        string='Storage Period in years',
    )
    approved_number = fields.Char(  # Broj saglasnosti na listi kategorija
        string='Subject',
        copy='False',
        readonly=False,
    )

    kolicina_dokumenata = fields.Integer(
        string='Documet Qty',
        required=True,
    )
    laokacija_za_cuvanje = fields.Char(
        string='Storage location',
    )

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    note = fields.Char(
        string='Note',
    )
    # def action_read_document_category(self):
    #     self.ensure_one()
    #     return {
    #         'name': self.display_name,
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'ii.edk.lista.kag',
    #         'res_id': self.id,
    #     }
