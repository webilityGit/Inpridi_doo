# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)



class UserFormInherit(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        no=len(self.env['res.users'].search([]))
        _logger.info("CREATE USER %s !!!", no)
        if no < 100:
            result = super(UserFormInherit, self).create(vals)
        else:
            raise UserError(_('Nije moguce dodati novog korisnika, zbog prekoracenja broja licenci!'))
        return result

