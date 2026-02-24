from odoo import api, models
import logging

from datetime import date

_logger = logging.getLogger(__name__)
class AccountEdiXmlUBL21RS(models.AbstractModel):
    _name = "account.edi.xml.ubl.rs"
    _inherit = 'account.edi.xml.ubl_21'
    _description = "UBL 2.1 (RS eFaktura)"

    @api.model
    def _get_customization_ids(self):
        vals = super()._get_customization_ids()
        vals['efaktura_rs'] = 'urn:cen.eu:en16931:2017#compliant#urn:mfin.gov.rs:srbdt:2022#conformant#urn:mfin.gov.rs:srbdtext:2022'
        return vals


    def _export_invoice_vals(self, invoice):
        # EXTENDS 'account_edi_ubl_cii'
        vals = super()._export_invoice_vals(invoice)
        doc_type, desc_code, subtype = self._get_l10n_rs_invoice_out_subtype(invoice) 


        vals['vals'].update({
            ##
            'issue_date': date.today(),
            ##
            'customization_id': self._get_customization_ids()['efaktura_rs'],
            'billing_reference_vals': self._l10n_rs_get_billing_reference(invoice), 
            'document_type_code': doc_type,  # Lubi
            'DescriptionCode': desc_code,    # lubi
            'document_subtype': subtype,
        })

        if not invoice.vat_liability_arising:
            vals['vals'].pop('DescriptionCode', None)
            vals['vals'].pop('invoice_period_vals_list', None)


        #values for final
        if subtype == 'final':
            down_lines = []
            downpayment_invoices = invoice._get_downpayment_invoices()
            billing_reference_vals = {}

            for dp_inv in downpayment_invoices:
                billing_reference_vals = {
                    'id': dp_inv.name,
                    'issue_date': dp_inv.invoice_date,
                }

                dp_lines = dp_inv.invoice_line_ids.filtered(lambda l: l.is_downpayment)
                for line in dp_lines:
                    ###
                    tax = line.tax_ids[:1]
                    percent = float(tax.amount) if tax else 0.0

                    taxable = float(line.price_subtotal or 0.0)
                    inclusive = float(line.price_total or 0.0)
                    tax_amount = inclusive - taxable
                    ###

                    down_lines.append({
                        'ref': dp_inv.name,
                        'taxable': taxable,
                        'tax_amount': tax_amount,
                        'percent': percent,
                        'currency': invoice.currency_id.name,
                        'exclusive': taxable,
                        'inclusive': inclusive,
                        'payable': inclusive, ####
                        'line_id': line.id,
                        'line_name': line.name or line.product_id.display_name,
                    })

            current_lines = invoice.invoice_line_ids.filtered(lambda l: not l.is_downpayment)
            
            line_extension_amount = sum(float(line.price_subtotal) for line in current_lines)
            total_tax_amount = sum(float(line.price_total - line.price_subtotal) for line in current_lines)
            total_inclusive_amount = sum(float(line.price_total) for line in current_lines)

            percents = {d['percent'] for d in down_lines}
            current_tax_percent = current_lines[0].tax_ids[:1].amount if current_lines and current_lines[0].tax_ids else 0.0
            percents.add(current_tax_percent)
            
            total_percent = percents.pop() if len(percents) == 1 else 0.0

            total_prepaid = sum(d['inclusive'] for d in down_lines)
            payable_amount = total_inclusive_amount - total_prepaid 

            ##!!!!!
            vals['vals']['monetary_total_vals'].update({
                'currency': invoice.currency_id,
                'currency_dp': 2,
                'line_extension_amount': line_extension_amount,
                'tax_exclusive_amount': line_extension_amount,
                'tax_inclusive_amount': total_inclusive_amount,
                'allowance_total_amount': 0.0,
                'charge_total_amount': 0.0,
                'prepaid_amount': total_prepaid,
                'payable_rounding_amount': 0.0,
                'payable_amount': payable_amount, 
            })

            # vals['vals']['tax_total_vals'] = [{
            #     'currency': invoice.currency_id,
            #     'currency_dp': 2,
            #     'tax_amount': total_tax_amount,
            #     'tax_subtotal_vals': [{
            #         'currency': invoice.currency_id,
            #         'currency_dp': 2,
            #         'taxable_amount': line_extension_amount,
            #         'tax_amount': total_tax_amount,
            #     }],
            # }]
            vals['vals']['tax_total_vals'][0].update({
                'currency': invoice.currency_id,
                'currency_dp': 2,
                'tax_amount': total_tax_amount,
            })

            vals['vals']['tax_total_vals'][0]['tax_subtotal_vals'][0].update({
                'currency': invoice.currency_id,
                'currency_dp': 2,
                'taxable_amount': line_extension_amount,
                'tax_amount': total_tax_amount,
            })

            total_untaxed = sum(d['taxable'] for d in down_lines)
            total_tax = sum(d['tax_amount'] for d in down_lines)
            total_inclusive = sum(d['inclusive'] for d in down_lines)
            total_payable = invoice.amount_residual

            percents = {d['percent'] for d in down_lines}
            total_percent = percent.pop() if (percents) == 1 else 0.0

            vals['vals'].update({
                'downpayment_lines': down_lines,
                'total_untaxed': total_untaxed,
                'total_tax': total_tax,
                'total_inclusive': total_inclusive,
                'total_payable': total_payable, ###
                'total_percent': total_percent,
                'currency': invoice.currency_id.name,
                'billing_reference_vals': billing_reference_vals
            })

            

            #otklanjanje cvora OrderReference
            vals['vals'].pop('order_reference', None)
            vals['vals'].pop('sales_order_id', None)

            #### uklanjanje linije avansne fakture
            if 'line_vals' in vals['vals']:
                vals['vals']['line_vals'] = [
                    line for line in vals['vals']['line_vals']
                    if 'down payment' not in line.get('item_vals', {}).get('description', '').lower()
                ]

        #_logger.info("!!!!!!!!!!!! Export Invoice  VALS=%s", vals)
        _logger.info("!!!!!!!!!!!! Export Invoice  VALS=%s", vals['vals'])

        return vals

    def _get_l10n_rs_invoice_out_subtype(self, invoice):   # Lubi
        _logger.info("##################  usao u odredjivanje koda %s", invoice.move_type)
        # invoice_type base on invoice subtype
        DescriptionCode = invoice.l10n_rs_tax_date_obligations_code
        if invoice.move_type == 'out_refund':
            invoice_type ='381'
        if invoice.move_type == 'out_invoice' and invoice.l10n_rs_invoice_out_subtype == 'avans' :
            invoice_type = '386'
            DescriptionCode = '432'
        if invoice.move_type == 'out_invoice' and invoice.l10n_rs_invoice_out_subtype in ['final', 'regular']:
            invoice_type = '380'
           
        _logger.info("*******************  Nadjen Invoice_type  isecription code %s", invoice_type)  

        subtype = invoice.l10n_rs_invoice_out_subtype 
         
        _logger.info("*******************  Nadjen SUBTYPE %s", subtype)  
# ovde sada treba ubaciti kod koji generise hml kao u nastavku
            # < cec: UBLExtensions >
            #   < cec: UBLExtension >
            #   < cec: ExtensionContent >
            #       < sbt: SrbDtExt >
            #       < sbt: InvoicedPrepaymentAmount >
            #           < cbc: ID > Broj      # avansne fakture
        #               < / cbc: ID >

                        # < cac: TaxTotal >
            #            < cbc: TaxAmount            #           currencyID = "RSD" > 300 < / cbc: TaxAmount >
            #           < cac: TaxSubtotal >
            #           < cbc: TaxableAmount
            #              currencyID = "RSD" > 1500 < / cbc: TaxableAmount >
            #           < cbc: TaxAmount
            #               currencyID = "RSD" > 300 < / cbc: TaxAmount >
            #           < cac: TaxCategory >
            #           < cbc: ID > S < / cbc: ID >
            #           < cbc: Percent > 20 < / cbc: Percent >
            #           < cac: TaxScheme >
            #           < cbc: ID > VAT < / cbc: ID >
            #           < / cac: TaxScheme >
            #           < / cac: TaxCategory >
            #           < / cac: TaxSubtotal >
            #           < / cac: TaxTotal >
            #       < / sbt: InvoicedPrepaymentAmount >

            # < sbt: ReducedTotals >
            #   < cac: TaxTotal >
            #   < cbc: TaxAmount
            #       currencyID = "RSD" > 0 < / cbc: TaxAmount >
            #   < cac: TaxSubtotal >
            #   < cbc: TaxableAmount
            #   currencyID = "RSD" > 0 < / cbc: TaxableAmount >
            #   < cbc: TaxAmount
            #   currencyID = "RSD" > 0 < / cbc: TaxAmount >
            #   < cac: TaxCategory >
            #   < cbc: ID > S < / cbc: ID >
            #   < cbc: Percent > 20 < / cbc: Percent >
            #   < cac: TaxScheme >
            #   < cbc: ID > VAT < / cbc: ID >
            #   < / cac: TaxScheme >
            #   < / cac: TaxCategory >
            #   < / cac: TaxSubtotal >
            #   < / cac: TaxTotal >
            #   < cac: LegalMonetaryTotal >
            #   < cbc: TaxExclusiveAmount
            #   currencyID = "RSD" > 1500 < / cbc: TaxExclusiveAmount >
            #   < cbc: TaxInclusiveAmount
            #   currencyID = "RSD" > 0 < / cbc: TaxInclusiveAmount >
            # < cbc: PayableAmount
            # currencyID = "RSD" > 0 < / cbc: PayableAmount >
            # < / cac: LegalMonetaryTotal >
            # < / sbt: ReducedTotals >

            # < / sbt: SrbDtExt >
            # < / cec: ExtensionContent >
            # < / cec: UBLExtension >
            # < / cec: UBLExtensions >
                
               
        return (invoice_type, DescriptionCode, subtype)

    def _l10n_rs_get_billing_reference(self, invoice):
        # Billing Reference values for Credit Note
        if invoice.move_type == 'out_refund' and invoice.reversed_entry_id:
            return {
                'id': invoice.reversed_entry_id.name,
                'issue_date': invoice.reversed_entry_id.invoice_date,
            }
        return {}

    def _get_invoice_period_vals_list(self, invoice):
        # EXTENDS account_edi_ubl_cii
        vals_list = super()._get_invoice_period_vals_list(invoice)
        vals_list.append({
            'description_code': '0' if invoice.move_type == 'out_refund' else invoice.l10n_rs_tax_date_obligations_code,
        })
        return vals_list

    def _get_partner_party_vals(self, partner, role):
        vals = super()._get_partner_party_vals(partner, role)
        vat_country, vat_number = partner._split_vat(partner.vat)
        if vat_country.isnumeric():
            vat_number = partner.vat
        vals.update({
            'endpoint_id': vat_number,
            'endpoint_id_attrs': {
                'schemeID': '9948',
            },
        })
        return vals

    def _get_partner_party_legal_entity_vals_list(self, partner):
        # EXTENDS 'account_edi_ubl_cii'
        vals_list = super()._get_partner_party_legal_entity_vals_list(partner)
        for vals in vals_list:
            vals['company_id'] = partner.l10n_rs_edi_registration_number
        return vals_list

    def _get_partner_party_tax_scheme_vals_list(self, partner, role):
        # EXTENDS 'account_edi_ubl_cii'
        vals_list = super()._get_partner_party_tax_scheme_vals_list(partner, role)

        for vals in vals_list:
            vat_country, vat_number = partner._split_vat(partner.vat)
            if vat_country.isnumeric():
                vat_country = 'RS'
                vat_number = partner.vat
            if vat_country == 'RS' and partner.simple_vat_check(vat_country, vat_number):
                vals['company_id'] = vat_country + vat_number
        return vals_list

    def _get_delivery_vals_list(self, invoice):
        # EXTENDS 'account_edi_ubl_cii'
        vals_list = super()._get_delivery_vals_list(invoice)
        for vals in vals_list:
            vals['actual_delivery_date'] = invoice.delivery_date or None
        return vals_list

    def _get_partner_party_identification_vals_list(self, partner):
        vals_list = super()._get_partner_party_identification_vals_list(partner)
        if partner.country_code == 'RS' and partner.l10n_rs_edi_public_funds:
            vals_list.append({
                'id': f'JBKJS: {partner.l10n_rs_edi_public_funds}',
            })
        return vals_list

    #def _get_invoice_node(self, vals):
    #    document_node = super()._get_invoice_node(vals)
    #    _logger.info("NOOODEEEE %s", document_node)
    #    return document_node