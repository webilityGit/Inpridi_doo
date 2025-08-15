# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class iiefakturaProduct(models.Model):
     _inherit = 'account.move'
     _description = 'Indikator statusa slanja u SEF'

     jbkjs = fields.Char(string="Trezor", related='partner_id.jbkjs',
                         help='Jedinstveni broj korisnika javnih sredstava', store=True)
     is_jn = fields.Boolean(string='Faktura za Javnu nabavku?')
     mesto_prometa = fields.Char(string="Mesto prometa", help='Unesi mesto nastanka prometa', default="Beograd")

     # x_sent_to_sef = fields.Char(string="Poslato u SEF", default="notsent")
     x_sent_to_sef = fields.Selection([('no_to_sef', 'Nije za slanje u SEF'), ('sent_to_sef', 'Poslato u SEF'), ('not_sent_to_sef', 'Za slanje na SEF'), ('err_sent_to_sef', 'Greška slanja na SEF'),
                                       ('to_cancel', 'Za otkazivanje')], default = "not_sent_to_sef", string='Status slanja U SEF')
     auto_crf = fields.Boolean(string='Posalji u CRF')
 #    payment_mode_id = fields.Many2one(comodel_name='account.payment.mode', string="Payment Mode", readonly=False, ondelete='restrict')
 #    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', readonly=False, oldname='payment_term')
#     tax_line_ids = fields.One2many('account.invoice.tax', 'invoice_id', string='Tax Lines', oldname='tax_line', copy=True)
##     tax_line_ids = fields.One2many('account.invoice.tax', 'invoice_id', string='Tax Lines', oldname='tax_line',
##                                    readonly=False, states={'draft': [('readonly', False)]}, copy=True)
##     invoice_line_ids = fields.One2many('account.invoice.line', 'invoice_id', string='Invoice Lines',
##                                        oldname='invoice_line',readonly=False, states={'draft': [('readonly', False)]}, copy=True)

 #    date_prometa = fields.Date(string='Datum Prometa', index=True, copy=False)

     x_broj_ugovora_jn = fields.Char("Broj ugovora JN")
     x_broj_odluke = fields.Char("Broj odluke za oslobadjanje")

     x_out_invoice_type = fields.Selection([('entry', 'Nalog'), ('standard', 'Faktura'), ('avans', 'Avansna Faktura'), ('final', 'Konačna faktura')],
                                      string='Tip izlazne fakture', default='standard')

    # Dajemo mogucnost da se ovo polje kroz korisnicki interfejs menja
     invoice_origin = fields.Char(
        string='Origin',
        readonly=False,
        tracking=True,
        help="The document(s) that generated the invoice.",
     )


class iiefakturaProduct(models.Model):
     _inherit = 'product.template'

     unece_categ_id = fields.Many2one(
         "unece.code.list",
         string="PDV kategorija",
         domain=[("type", "=", "tax_categ")],
         ondelete="restrict",
         default=lambda self: self.env['unece.code.list'].search([('code', '=', 'S')]),
         help="Select the Tax Category Code of the official "
              "nomenclature of the United Nations Economic "
              "Commission for Europe (UNECE), DataElement 5305",

     )
     x_pdv_sifra_osnova = fields.Many2one(
         "osnov.pdv.izuzece",
         string="Osniv izuzeca",
         #    domain=[("unece_categ_id", "=", unece_categ_id.id)],
         ondelete="restrict",
         help="Select the Tax Category Code of the official "
              "nomenclature of the United Nations Economic "
              "Commission for Europe (UNECE), DataElement 5305",
     )



   #  x_pdv_sifra_osnova = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=

#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
#class iiefakturaTaxLine(models.Model):
#     _inherit = 'account.invoice.tax'
#     _description = 'ii_faktura.ii_faktura'

#     x_pdv_sifra_razloga = fields.Char()

class iiefakturaInvoiceLine(models.Model):
     _inherit = 'account.move.line'
     _description = 'ii_efaktura kategorija i sifra osnova oslobadjana od PDV'
#
     unece_categ_id = fields.Many2one(
        "unece.code.list",
        string="PDV kategorija",
        domain=[("type", "=", "tax_categ")],
        ondelete="restrict",
        default = lambda self:self.env['unece.code.list'].search([('code', '=', 'S')]),
        help="Select the Tax Category Code of the official "
             "nomenclature of the United Nations Economic "
             "Commission for Europe (UNECE), DataElement 5305",

    )
     x_pdv_sifra_osnova = fields.Many2one(
        "osnov.pdv.izuzece",
        string="Osniv izuzeca",
    #    domain=[("unece_categ_id", "=", unece_categ_id.id)],
        ondelete="restrict",
        help="Select the Tax Category Code of the official "
             "nomenclature of the United Nations Economic "
             "Commission for Europe (UNECE), DataElement 5305",
    )
     @api.onchange('product_id')
     def _onchange_product_id_in_sale_line_method(self):
     #   _logger.info("****************  !!!! Usao u change product self = %s, origin=%s", self._context, self.product_id.id)
        if self.product_id:
            artikli = self.env['product.product'].search([('id','=',self.product_id.id)])
            _logger.info("pronadjeni artikal = %s", artikli)
            for artikal in artikli:
               if artikal.unece_categ_id:
                   self.unece_categ_id = artikal.unece_categ_id.id
               if artikal.x_pdv_sifra_osnova:
                   self.x_pdv_sifra_osnova = artikal.x_pdv_sifra_osnova.id





