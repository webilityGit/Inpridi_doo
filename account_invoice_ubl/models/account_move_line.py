# -*- coding: utf-8 -*-

from odoo import models, fields, api
class iiefakturaInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    _description = 'ii_efaktura kategorija i sifra osnova oslobadjana od PDV'
    #
    unece_categ_id = fields.Many2one(
        "unece.code.list",
        string="PDV kategorija",
        domain=[("type", "=", "tax_categ")],
        ondelete="restrict",
        help="Select the Tax Category Code of the official "
             "nomenclature of the United Nations Economic "
             "Commission for Europe (UNECE), DataElement 5305",
    )

    @api.onchange('product_id')
    def _inverse_product_id(self):
        self._conditional_add_to_compute('account_id', lambda line: (
                line.display_type == 'product' and line.move_id.is_invoice(True)
        ))

    def _conditional_add_to_compute(self, fname, condition):
        field = self._fields[fname]
        to_reset = self.filtered(lambda line:
                                 condition(line)
                                 and not self.env.is_protected(field, line)
                                 )
        to_reset.invalidate_recordset([fname])
        self.env.add_to_compute(field, to_reset)
