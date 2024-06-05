# -*- coding: utf-8 -*-
from datetime import datetime as dt
import datetime

from odoo import _, models, fields, api


import logging
_logger = logging.getLogger(__name__)

class SEFServiceGetInvoiceWizard(models.TransientModel):
    _name = 'ii.sef.getinvoice.wizard'

    date_start = fields.Date(string='Datum od',default=fields.Date.today)
    date_end = fields.Date(string='Datum do', default=fields.Date.today)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
    )


