from odoo import api, fields, models


from odoo import models, fields

class AccountTax(models.Model):
    _inherit = 'account.tax'

    ubl_cii_tax_category_code = fields.Selection(
        selection=[
            ('AE20', 'AE20 - Promet po stopi od 20% za koji je poreski dužnik primalac'),
            ('AE10', 'AE10 - Promet po stopi od 10% za koji je poreski dužnik primalac'),
            ('E', 'E - Poresko oslobođenje bez prava na odbitak prethodnog poreza'),
            ('S20', 'S20 - Promet po stopi od 20%'),
            ('S10', 'S10 - Promet po stopi od 10%'),
            ('Z', 'Z - Poresko oslobođenje sa pravom na odbitak prethodnog poreza'),
            ('R', 'R - Izuzimanje od PDV-a'),
            ('O', 'O - Nije predmet oporezivanja PDV-om'),
            ('OE', 'OE - Nije predmet oporezivanja PDV2'),
            ('SS', 'SS - Posebni postupci oporezivanja'),
            ('N', 'N - Anuliranje')
        ],
        string="Tax Category Code",
        help="The VAT category code used for electronic invoicing purposes."
    )

    ubl_cii_tax_exemption_reason_code = fields.Selection(
        help="The reason why the amount is exempted from VAT or why no VAT is being charged, used for electronic invoicing purposes.",
        string="Tax Exemption Reason Code",
        selection=[
            ('VATEX-EU-79-C', 'VATEX-EU-79-C - Exempt based on article 79, point c of Council Directive 2006/112/EC'),
            ('VATEX-EU-132', 'VATEX-EU-132 - Exempt based on article 132 of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1A', 'VATEX-EU-132-1A - Exempt based on article 132, section 1 (a) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1B', 'VATEX-EU-132-1B - Exempt based on article 132, section 1 (b) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1C', 'VATEX-EU-132-1C - Exempt based on article 132, section 1 (c) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1D', 'VATEX-EU-132-1D - Exempt based on article 132, section 1 (d) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1E', 'VATEX-EU-132-1E - Exempt based on article 132, section 1 (e) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1F', 'VATEX-EU-132-1F - Exempt based on article 132, section 1 (f) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1G', 'VATEX-EU-132-1G - Exempt based on article 132, section 1 (g) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1H', 'VATEX-EU-132-1H - Exempt based on article 132, section 1 (h) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1I', 'VATEX-EU-132-1I - Exempt based on article 132, section 1 (i) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1J', 'VATEX-EU-132-1J - Exempt based on article 132, section 1 (j) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1K', 'VATEX-EU-132-1K - Exempt based on article 132, section 1 (k) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1L', 'VATEX-EU-132-1L - Exempt based on article 132, section 1 (l) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1M', 'VATEX-EU-132-1M - Exempt based on article 132, section 1 (m) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1N', 'VATEX-EU-132-1N - Exempt based on article 132, section 1 (n) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1O', 'VATEX-EU-132-1O - Exempt based on article 132, section 1 (o) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1P', 'VATEX-EU-132-1P - Exempt based on article 132, section 1 (p) of Council Directive 2006/112/EC'),
            ('VATEX-EU-132-1Q', 'VATEX-EU-132-1Q - Exempt based on article 132, section 1 (q) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143', 'VATEX-EU-143 - Exempt based on article 143 of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1A', 'VATEX-EU-143-1A - Exempt based on article 143, section 1 (a) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1B', 'VATEX-EU-143-1B - Exempt based on article 143, section 1 (b) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1C', 'VATEX-EU-143-1C - Exempt based on article 143, section 1 (c) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1D', 'VATEX-EU-143-1D - Exempt based on article 143, section 1 (d) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1E', 'VATEX-EU-143-1E - Exempt based on article 143, section 1 (e) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1F', 'VATEX-EU-143-1F - Exempt based on article 143, section 1 (f) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1FA', 'VATEX-EU-143-1FA - Exempt based on article 143, section 1 (fa) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1G', 'VATEX-EU-143-1G - Exempt based on article 143, section 1 (g) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1H', 'VATEX-EU-143-1H - Exempt based on article 143, section 1 (h) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1I', 'VATEX-EU-143-1I - Exempt based on article 143, section 1 (i) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1J', 'VATEX-EU-143-1J - Exempt based on article 143, section 1 (j) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1K', 'VATEX-EU-143-1K - Exempt based on article 143, section 1 (k) of Council Directive 2006/112/EC'),
            ('VATEX-EU-143-1L', 'VATEX-EU-143-1L - Exempt based on article 143, section 1 (l) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148', 'VATEX-EU-148 - Exempt based on article 148 of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-A', 'VATEX-EU-148-A - Exempt based on article 148, section (a) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-B', 'VATEX-EU-148-B - Exempt based on article 148, section (b) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-C', 'VATEX-EU-148-C - Exempt based on article 148, section (c) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-D', 'VATEX-EU-148-D - Exempt based on article 148, section (d) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-E', 'VATEX-EU-148-E - Exempt based on article 148, section (e) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-F', 'VATEX-EU-148-F - Exempt based on article 148, section (f) of Council Directive 2006/112/EC'),
            ('VATEX-EU-148-G', 'VATEX-EU-148-G - Exempt based on article 148, section (g) of Council Directive 2006/112/EC'),
            ('VATEX-EU-151', 'VATEX-EU-151 - Exempt based on article 151 of Council Directive 2006/112/EC'),
            ('VATEX-EU-151-1A', 'VATEX-EU-151-1A - Exempt based on article 151, section 1 (a) of Council Directive 2006/112/EC'),
            ('VATEX-EU-151-1AA', 'VATEX-EU-151-1AA - Exempt based on article 151, section 1 (aa) of Council Directive 2006/112/EC'),
            ('VATEX-EU-151-1B', 'VATEX-EU-151-1B - Exempt based on article 151, section 1 (b) of Council Directive 2006/112/EC'),
            ('VATEX-EU-151-1C', 'VATEX-EU-151-1C - Exempt based on article 151, section 1 (c) of Council Directive 2006/112/EC'),
            ('VATEX-EU-151-1D', 'VATEX-EU-151-1D - Exempt based on article 151, section 1 (d) of Council Directive 2006/112/EC'),
            ('VATEX-EU-151-1E', 'VATEX-EU-151-1E - Exempt based on article 151, section 1 (e) of Council Directive 2006/112/EC'),
            ('VATEX-EU-309', 'VATEX-EU-309 - Exempt based on article 309 of Council Directive 2006/112/EC'),
            ('VATEX_EU_AE', 'VATEX-EU-AE - Reverse charge'),
            ('VATEX_EU_D', 'VATEX-EU-D - Intra-Community acquisition from second hand means of transport'),
            ('VATEX_EU_F', 'VATEX-EU-F - Intra-Community acquisition of second hand goods'),
            ('VATEX_EU_G', 'VATEX-EU-G - Export outside the EU'),
            ('VATEX_EU_I', 'VATEX-EU-I - Intra-Community acquisition of works of art'),
            ('VATEX_EU_IC', 'VATEX-EU-IC - Intra-Community supply'),
            ('VATEX_EU_O', 'VATEX-EU-O - Not subject to VAT'),
            ('VATEX_EU_J', 'VATEX-EU-J - Intra-Community acquisition of collectors items and antiques'),
            ('VATEX_FR-FRANCHISE', 'VATEX-FR-FRANCHISE - France domestic VAT franchise in base'),
            ('VATEX_FR-CNWVAT', 'VATEX-FR-CNWVAT - France domestic Credit Notes without VAT, due to supplier forfeit of VAT for discount'),
        ]
    )

    def _requires_exemption_reason(self):
        self.ensure_one()
        return self.ubl_cii_tax_category_code in ['AE10','AE20' 'E', 'Z', 'O', 'R' 'OE', 'SS', 'N']

    @api.onchange("ubl_cii_tax_category_code")
    def _onchange_ubl_cii_tax_category_code(self):
        for tax in self:
            if not tax._requires_exemption_reason():
                tax.ubl_cii_tax_exemption_reason_code = False