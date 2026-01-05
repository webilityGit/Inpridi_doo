# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)



class iiefakturaInvoiceLine(models.Model):
     _inherit = 'account.move.line'
     _description = 'account move line with kategorija i sifra osnova oslobadjana od PDV'

     #ilija
     ubl_cii_tax_category_code = fields.Many2one(
        "ii.pdv.category", string="PDV Kategorija"
     )
     ubl_cii_tax_exemption_reason_code = fields.Many2one(
          "ii.pdv.exemption.reason",
          string="Osnov za izuzece",
          domain="[('category_id', '=', ubl_cii_tax_category_code)]",
     )

     ubl_cii_tax_exemption_reason = fields.Char(
          string="Broj odluke",
     )

     @api.onchange('ubl_cii_tax_category_code')
     def _onchange_ubl_cii_tax_category_code(self):
          if self.ubl_cii_tax_category_code.code != self.ubl_cii_tax_category_code:
               self.ubl_cii_tax_exemption_reason_code = False
               self.ubl_cii_tax_exemption_reason = False

    # @api.onchange('tax_ids', 'product_id')
    #  def _getPDVcategory(self):
    #     _logger.info("self = %s %s", self.tax_ids, self.product_id)
    #     for tax in self.tax_ids:
    #         _logger.info("!!!!!!!!!!! tax = %s %s", tax, tax.ubl_cii_tax_category_code)
    #         self.ubl_cii_tax_category_code = tax.ubl_cii_tax_category_code
    #     return

       
        #_logger.info("PDV CAT = %s", pdv_cat_ids)
        # return dict(self.env['account.tax'].fields_get()['pdv_cat_ids']['selection']).get(pdv_cat_ids)
         #return pdv_cat_ids
#
    #  unece_categ_id = fields.Many2one(
    #     "unece.code.list",
    #     string="PDV kategorija",
    #     domain=[("type", "=", "tax_categ")],
    #     ondelete="restrict",
    #     default = lambda self:self.env['unece.code.list'].search([('code', '=', 'S')]),
    #     help="Select the Tax Category Code of the official "
    #          "nomenclature of the United Nations Economic "
    #          "Commission for Europe (UNECE), DataElement 5305",
    #
    # )
    #  x_pdv_sifra_osnova = fields.Many2one(
    #     "osnov.pdv.izuzece",
    #     string="Osniv izuzeca",
    # #    domain=[("unece_categ_id", "=", unece_categ_id.id)],
    #     ondelete="restrict",
    #     help="Select the Tax Category Code of the official "
    #          "nomenclature of the United Nations Economic "
    #          "Commission for Europe (UNECE), DataElement 5305",
    # )
    #  @api.onchange('product_id')
    #  def _onchange_product_id_in_sale_line_method(self):
    #  #   _logger.info("****************  !!!! Usao u change product self = %s, origin=%s", self._context, self.product_id.id)
    #     if self.product_id:
    #         artikli = self.env['product.product'].search([('id','=',self.product_id.id)])
    #         _logger.info("pronadjeni artikal = %s", artikli)
    #         for artikal in artikli:
    #            if artikal.unece_categ_id:
    #                self.unece_categ_id = artikal.unece_categ_id.id
    #            if artikal.x_pdv_sifra_osnova:
    #                self.x_pdv_sifra_osnova = artikal.x_pdv_sifra_osnova.id

