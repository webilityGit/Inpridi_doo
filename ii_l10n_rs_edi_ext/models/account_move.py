import uuid
import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from requests.exceptions import Timeout, ConnectionError, HTTPError
import logging
_logger = logging.getLogger(__name__)
DEMO_EFAKTURA_URL = 'https://demoefaktura.mfin.gov.rs/api/publicApi/sales-invoice/ubl'
EFAKTURA_URL = 'https://efakturadev.mfin.gov.rs/api/publicApi/sales-invoice/ubl'


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_rs_invoice_out_subtype = fields.Selection(                   # Lubi
        string="Invoice out subtype",
        selection=[
            ('avans', 'Advanced Payment Invoice'),
            ('final', 'Final Invoice'),
            ('regular', 'Standard Invoice'),
        ],
        store=True,
        readonly=False,
        compute='_compute_l10n_rs_invoice_out_subtype',
    )
   
    #ilija
    vat_liability_arising = fields.Boolean(
        string="Nastanak PDV obaveze",
        help="Ako je oznaceno: PDV se oobracunava...",
        default=True,
    )
    show_vat_warning = fields.Boolean(
        compute="_compute_show_vat_warning",
        store=False
    )

    @api.depends('country_code','line_ids.product_id','line_ids.name')
    def _compute_l10n_rs_invoice_out_subtype(self):
        for move in self:
            if move.country_code == 'RS':
                result = move.check_move_lines_for_down_payment()
                _logger.info("!!!!!!!!!!! ************* rezultat=%s", result)
                if int(result['line_count']) == 1 and result['has_down_payment_product']:  # znaci radi se o avansnom racunu
                    move.l10n_rs_invoice_out_subtype = 'avans'
                    move.l10n_rs_tax_date_obligations_code = '432'
                    return
                elif int(result['line_count']) > 1 and result['has_down_payment_product']:  # znaci radi se o finalnom racunu
                    move.l10n_rs_invoice_out_subtype = 'final'
                    move.l10n_rs_tax_date_obligations_code = '35'
                    return
                else:
                    move.l10n_rs_invoice_out_subtype = 'regular'
                    move.l10n_rs_tax_date_obligations_code = '3'
            else:
                move.l10n_rs_invoice_out_subtype = 'regular'
                move.l10n_rs_tax_date_obligations_code = '3'

    def check_move_lines_for_down_payment(self):
        """
        Proverava za account.move:
         - broj povezanih account.move.line stavki
         - da li neka od stavki ima proizvod sa nazivom "Down Payment"
        """
        self.ensure_one()

        line_count = len(self.invoice_line_ids)
        has_down_payment_product = False

        for line in self.line_ids:
            if line.is_downpayment:
                has_down_payment_product = True
                break

        return {
            'line_count' : line_count,
            'has_down_payment_product': has_down_payment_product,
        }

    def _l10n_rs_edi_send(self, sendToCir):
        _logger.info("!!!!!!!!!!! ************* send =%s", self)
        self.ensure_one()
        self.env['res.company']._with_locked_records(self)
        xml, errors = self.env['account.edi.xml.ubl.rs']._export_invoice(self)
        if errors:
            return xml, errors
        _logger.info("!!!!!!!!!!! ************* proslo formiranje XML-a %s", xml)    
        params = {
            'requestId': self.l10n_rs_edi_uuid,
            'sendToCir': 'Yes' if sendToCir else 'No'
        }
        url = DEMO_EFAKTURA_URL if self.company_id.l10n_rs_edi_demo_env else EFAKTURA_URL
        headers = {
            'Content-Type': 'application/xml',
            'ApiKey': self.company_id.l10n_rs_edi_api_key,
        }
        error_message = False
        try:
            response = requests.post(url=url, params=params, headers=headers, data=xml, timeout=30)
            response.raise_for_status()
        except (Timeout, ConnectionError, HTTPError) as exception:
            sefporuka = "** SEF ERR ** Neuspesno slanje fakture na server PU! URL = " + url + "\n Kod greske je =" + str(response.status_code) + "\n Razlog" + response.text
    
            error_message = _("There was a problem with the connection with eFaktura: %s", sefporuka)
            self.message_post(body=error_message)
            return xml, error_message
        dict_response = {}
        try:
            dict_response = response.json()
        except requests.exceptions.JSONDecodeError as e:
            error_message = _("Invalid response from eFaktura: %s", str(e))
        self.l10n_rs_edi_state = 'sending_failed' if error_message else 'sent'
        self.l10n_rs_edi_error = error_message
        self.l10n_rs_edi_invoice = dict_response.get('InvoiceId')
        self.l10n_rs_edi_purchase_invoice = dict_response.get('PurchaseInvoiceId')
        self.l10n_rs_edi_sales_invoice = dict_response.get('SalesInvoiceId')
        return xml, error_message
    
    #ilija
    @api.constrains('vat_liability_arising', 'invoice_line_ids')
    def _check_vat_obligation_zero_tax(self):
        for move in self:
            if not move.vat_liability_arising:
                for line in move.invoice_line_ids:
                    if line.tax_ids and any(t.amount != 0 for t in line.tax_ids):
                        raise ValidationError(
                            "Ako 'Ne nastaje PDV obaveza', sve stavke fakture moraju imati isključivo 0% PDV."
                        )
    
    @api.onchange('vat_liability_arising', 'invoice_line_ids')
    def _compute_show_vat_warning(self):
        for move in self:
            move.show_vat_warning = (
                not move.vat_liability_arising and
                any(line.tax_ids and any(t.amount != 0 for t in line.tax_ids)
                    for line in move.invoice_line_ids)
            )

    def _get_downpayment_invoices(self):
    #   Vraca listu avansnih faktura koje su povezane sa ovom regularnom fakturom
        downpayment_invoices = self.env['account.move']
        for line in self.invoice_line_ids:
            if any(sol.is_downpayment for sol in line.sale_line_ids):
                for sol in line.sale_line_ids:
                    if sol.invoice_lines:
                        inv = sol.invoice_lines.move_id.filtered(lambda m: m.id != self.id)
                        downpayment_invoices |= inv
            _logger.info("********************* INVOICE = %s", downpayment_invoices.mapped('name'))
        _logger.info("********************* INVOICE = %s", downpayment_invoices)
        return downpayment_invoices

    #def action_post(self):
    #    res = super().action_confirm()
    #    self._compute_l10n_rs_invoice_out_subtype
    #    return res
    
    # @api.model
    # def create(self, vals):
    #     record = super().create(vals)
    #     record._compute_l10n_rs_invoice_out_subtype()
    #     return record