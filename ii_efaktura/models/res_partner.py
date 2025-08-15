# -*- coding: utf-8 -*-
# © <2017> <builtforfifty>

from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    jbkjs = fields.Char(string="Trezor", help='Jedinstveni broj korisnika javnih sredstava')

 #   is_in_PDV = fields.Boolean(string = "je u PDV sistemu")
