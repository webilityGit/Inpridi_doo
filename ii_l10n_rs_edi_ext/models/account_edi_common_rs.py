from markupsafe import Markup

from odoo import fields, api, _, models, Command
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.exceptions import UserError, ValidationError

from odoo.tools.float_utils import float_round
from odoo.tools.misc import clean_context, formatLang, html_escape
from odoo.tools.xml_utils import find_xml_value
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# UNIT OF MEASURE
# -------------------------------------------------------------------------
UOM_TO_UNECE_CODE = {
    'uom.product_uom_unit': 'H87',
    'uom.product_uom_dozen': 'DZN',
    'uom.product_uom_kgm': 'KGM',
    'uom.product_uom_gram': 'GRM',
    'uom.product_uom_day': 'DAY',
    'uom.product_uom_hour': 'HUR',
    'uom.product_uom_ton': 'TNE',
    'uom.product_uom_meter': 'MTR',
    'uom.product_uom_km': 'KMT',
    'uom.product_uom_cm': 'CMT',
    'uom.product_uom_litre': 'LTR',
    'uom.product_uom_cubic_meter': 'MTQ',
    'uom.product_uom_lb': 'LBR',
    'uom.product_uom_oz': 'ONZ',
    'uom.product_uom_inch': 'INH',
    'uom.product_uom_foot': 'FOT',
    'uom.product_uom_mile': 'SMI',
    'uom.product_uom_floz': 'OZA',
    'uom.product_uom_qt': 'QT',
    'uom.product_uom_gal': 'GLL',
    'uom.product_uom_cubic_inch': 'INQ',
    'uom.product_uom_cubic_foot': 'FTQ',
    'uom.uom_square_meter': 'MTK',
    'uom.uom_square_foot': 'FTK',
    'uom.product_uom_yard': 'YRD',
    'uom.product_uom_millimeter': 'MMT',
}
class AccountEdiCommon(models.AbstractModel):
    _inherit = "account.edi.common"
    _description = "Common functions for EDI UoMs: generate the data, the constraints, etc"

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

 #   def _get_uom_unece_code(self, uom):

    
 #   Override Odoo mapping za jedinicu mere.
 #   - Ako je kompanija u Srbiji → koristi H87 (lokalni zahtev)
 #   - Inače koristi default iz Odoo mappinga (C62 i dr.)

#      company = self.env.company 
#       if hasattr(self, "move") and self.move:
#            company = self.move.company_id
#        elif hasattr(self, "company_id"):
#            company = self.company_id
#        xmlid = uom.get_external_id()
#        if xmlid and uom.id in xmlid:
#            if company and company.country_id.code == "RS":  # Srbija
#                return 'H87'
#            return self.UOM_TO_UNECE_CODE.get(xmlid[uom.id], 'C62')
#        # default fallback
#        return 'H87'

    def _get_uom_unece_code(self, uom):
        company = self.env.company
        if hasattr(self, "move") and self.move:
            company = self.move.company_id
        elif hasattr(self, "company_id"):
            company = self.company_id

        xmlid_map = uom.get_external_id() or {}
        xmlid = xmlid_map.get(uom.id)

        # Srbija: forsiraj H87 
        if company and company.country_id.code == "RS":
            return "H87"

        # Ostale zemlje: mapiranje ako postoji, u suprotnom C62
        if xmlid:
            return UOM_TO_UNECE_CODE.get(xmlid, "C62")
        return "C62"

    @api.model
    def _get_tax_unece_codes(self, customer, supplier, tax):
        
        result = super()._get_tax_unece_codes(customer, supplier, tax)
        
        invoice = self.env['account.move'].browse(self.env.context['active_id'])

        if invoice.vat_liability_arising:
            #TODO for line in lines
            first_line = invoice.invoice_line_ids[:1]

            category = first_line.ubl_cii_tax_category_code
            exemption = first_line.ubl_cii_tax_exemption_reason_code
            reason = first_line.ubl_cii_tax_exemption_reason

            if category:
                result['tax_category_code'] = category.code
            if exemption:
                result['tax_exemption_reason_code'] = exemption.code
                result['tax_exemption_reason'] = reason

        return result
    
# """ class UoM(models.Model):
#     _inherit = "uom.uom"

#     fiscal_country_codes = fields.Char(compute="_compute_fiscal_country_codes")

#     @api.depends_context("allowed_company_ids")
#     def _compute_fiscal_country_codes(self):
#         for record in self:
#             record.fiscal_country_codes = ",".join(self.env.companies.mapped("account_fiscal_country_id.code")) """

    # def _get_unece_code(self):
    #     """ Returns the UNECE code used for international trading for corresponding to the UoM as per
    #     https://unece.org/fileadmin/DAM/cefact/recommendations/rec20/rec20_rev3_Annex2e.pdf"""
    #     mapping = {
    #         'uom.product_uom_unit': 'H87',
    #         'uom.product_uom_dozen': 'DZN',
    #         'uom.product_uom_kgm': 'KGM',
    #         'uom.product_uom_gram': 'GRM',
    #         'uom.product_uom_day': 'DAY',
    #         'uom.product_uom_hour': 'HUR',
    #         'uom.product_uom_ton': 'TNE',
    #         'uom.product_uom_meter': 'MTR',
    #         'uom.product_uom_km': 'KMT',
    #         'uom.product_uom_cm': 'CMT',
    #         'uom.product_uom_litre': 'LTR',
    #         'uom.product_uom_lb': 'LBR',
    #         'uom.product_uom_oz': 'ONZ',
    #         'uom.product_uom_inch': 'INH',
    #         'uom.product_uom_foot': 'FOT',
    #         'uom.product_uom_mile': 'SMI',
    #         'uom.product_uom_floz': 'OZA',
    #         'uom.product_uom_qt': 'QT',
    #         'uom.product_uom_gal': 'GLL',
    #         'uom.product_uom_cubic_meter': 'MTQ',
    #         'uom.product_uom_cubic_inch': 'INQ',
    #         'uom.product_uom_cubic_foot': 'FTQ',
    #         'uom.uom_square_meter': 'MTK',
    #         'uom.uom_square_foot': 'FTK',
    #         'uom.product_uom_yard': 'YRD',
    #         'uom.product_uom_millimeter': 'MMT',
    #     }
    #     xml_ids = self._get_external_ids().get(self.id, [])
    #     matches = list(set(xml_ids) & set(mapping.keys()))
    #     return matches and mapping[matches[0]] or 'H87'
