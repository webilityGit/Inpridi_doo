# Copyright 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    xml_format_in_pdf_invoice = fields.Selection(
        selection_add=[("ubl", "Universal Business Language (UBL)")], default="ubl"
    )
    embed_pdf_in_ubl_xml_invoice = fields.Boolean(
        string="Embed PDF in UBL XML Invoice",
        help="If active, the standalone UBL Invoice XML file will include the "
        "PDF of the invoice in base64 under the node "
        "'AdditionalDocumentReference'. For example, to be compliant with the "
        "e-fff standard used in Belgium, you should activate this option.",
    )
    efaktura_api_key = fields.Char('API Key Sa sefa')
    efaktura_api_url = fields.Char('URL na SEFFu za postovanje faktura')


class ResPartner(models.Model):
    _inherit = "res.partner"

    # sifra partnera u trezoru
    jbkjs = fields.Char(string="JBKJS", help='Jedinstveni broj korisnika javnih sredstava')
    supplier_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        company_dependent=True,
        check_company=True,
        domain="[('payment_type', '=', 'outbound'),"
        "('company_id', '=', current_company_id)]",
        help="Select the default payment mode for this supplier.",
    )