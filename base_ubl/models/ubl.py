# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from io import BytesIO
from lxml import etree
from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import file_open, float_is_zero, float_round
from datetime import datetime
import requests
logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.generic import NameObject
except ImportError:
    logger.debug('Cannot import PyPDF2')


class BaseUbl(models.AbstractModel):
    _name = 'base.ubl'
    _description = 'Common methods to generate and parse UBL XML files'

    # ==================== METHODS TO GENERATE UBL files

    @api.model
    def _ubl_add_country(self, country, parent_node, ns, version='2.1'):
        country_root = etree.SubElement(parent_node, ns['cac'] + 'Country')
        country_code = etree.SubElement(country_root, ns['cbc'] + 'IdentificationCode')
        country_code.text = country.code
        country_name = etree.SubElement(country_root, ns['cbc'] + 'Name')
        country_name.text = country.name

    @api.model
    def _ubl_add_address(
            self, partner, node_name, parent_node, ns, version='2.1'):
        address = etree.SubElement(parent_node, ns['cac'] + node_name)
        if partner.street:
            streetname = etree.SubElement(address, ns['cbc'] + 'StreetName')
            streetname.text = partner.street
        if partner.street2:
            addstreetname = etree.SubElement(
                address, ns['cbc'] + 'AdditionalStreetName')
            addstreetname.text = partner.street2
        if hasattr(partner, 'street3') and partner.street3:
            blockname = etree.SubElement(
                address, ns['cbc'] + 'BlockName')
            blockname.text = partner.street3
        if partner.city:
            city = etree.SubElement(address, ns['cbc'] + 'CityName')
            city.text = partner.city
        if partner.zip:
            zip = etree.SubElement(address, ns['cbc'] + 'PostalZone')
            zip.text = partner.zip
        if partner.state_id:
            state = etree.SubElement(address, ns['cbc'] + 'CountrySubentity')
            state.text = partner.state_id.name
            state_code = etree.SubElement(address, ns['cbc'] + 'CountrySubentityCode')
            state_code.text = partner.state_id.code
        if partner.country_id: self._ubl_add_country(partner.country_id, address, ns, version=version)
        else:
            logger.info('UBL: missing country on partner %s', partner.name)

    @api.model
    def _ubl_get_contact_id(self, partner):
        return False

    @api.model
    def _ubl_add_contact(
            self, partner, parent_node, ns, node_name='Contact',version='2.1'):
        contact = etree.SubElement(parent_node, ns['cac'] + node_name)
        contact_id_text = self._ubl_get_contact_id(partner)
        if contact_id_text:
            contact_id = etree.SubElement(contact, ns['cbc'] + 'ID')
            contact_id.text = contact_id_text
        if partner.parent_id:
            contact_name = etree.SubElement(contact, ns['cbc'] + 'Name')
            contact_name.text = partner.name
        phone = partner.phone or partner.commercial_partner_id.phone
        if phone:
            telephone = etree.SubElement(contact, ns['cbc'] + 'Telephone')
            telephone.text = phone
    #    fax = partner.fax or partner.commercial_partner_id.fax
    #    if fax:                                                      # Lubi dodat telefax
    #        telefax = etree.SubElement(contact, ns['cbc'] + 'Telefax')
    #        telefax.text = fax
        email = partner.email or partner.commercial_partner_id.email
        if email:
            electronicmail = etree.SubElement(contact, ns['cbc'] + 'ElectronicMail')
            electronicmail.text = email

    @api.model
    def _ubl_add_language(self, lang_code, parent_node, ns, version='2.1'):
        langs = self.env['res.lang'].search([('code', '=', lang_code)])
        if not langs:
            return
        lang = langs[0]
        lang_root = etree.SubElement(parent_node, ns['cac'] + 'Language')
        lang_name = etree.SubElement(lang_root, ns['cbc'] + 'Name')
        lang_name.text = lang.name
        lang_code = etree.SubElement(lang_root, ns['cbc'] + 'LocaleCode')
        lang_code.text = lang.code

    @api.model
    def _ubl_get_party_identification(self, commercial_partner):   # Lubi doradjeno
        '''This method is designed to be inherited in localisation modules
        Should return a dict with key=SchemeName, value=Identifier'''
        party_identification_dic = {}
        if commercial_partner.jbkjs:
            party_identification_dic = {
                'jbkjs': 'JBKJS:' + str(commercial_partner.jbkjs),
            }

        elif commercial_partner.category_id.name == "JP":
            party_identification_dic = {
                'value': str(commercial_partner.l10n_rs_company_registry),
            }
        else:
            party_identification_dic = {}

        return party_identification_dic

    @api.model
    def _ubl_add_party_identification(
            self, commercial_partner, parent_node, ns, version='2.1'):
        id_dict = self._ubl_get_party_identification(commercial_partner)
        if id_dict:
            # Lubi provera da li se radi o budzetskom korisniku. ako jeste, formira se odgovarajuci tag
            logger.info('Usao u id_dict = %s', id_dict)
            for scheme_name, party_id_text in id_dict.items():
                logger.info('scheme_name= %s', scheme_name)
                logger.info('party_id_text= %s', party_id_text)
            #    party_identification = etree.SubElement(parent_node, ns['cac'] + 'PartyIdentification')
            #    party_identification_id = etree.SubElement(party_identification, ns['cbc'] + 'ID',
            #    schemeName=id_dict[key])
            #party_identification_id.text = party_id_text
            for scheme_name, party_id_text in id_dict.items():
                party_identification = etree.SubElement(parent_node, ns['cac'] + 'PartyIdentification')
                party_identification_id = etree.SubElement(party_identification, ns['cbc'] + 'ID')
                party_identification_id.text = party_id_text
        return

    @api.model
    def _ubl_get_tax_scheme_dict_from_partner(self, commercial_partner):
        tax_scheme_dict = {
            'id': 'VAT',
            'name': False,
            'type_code': False,
        }
        return tax_scheme_dict

    @api.model
    def _ubl_add_party_tax_scheme(
            self, commercial_partner, parent_node, ns, version='2.1'):
        if commercial_partner.vat:
            party_tax_scheme = etree.SubElement(
                parent_node, ns['cac'] + 'PartyTaxScheme')
            registration_name = etree.SubElement(
                party_tax_scheme, ns['cbc'] + 'RegistrationName')
            registration_name.text = commercial_partner.name
            company_id = etree.SubElement(
                party_tax_scheme, ns['cbc'] + 'CompanyID')
            company_id.text = commercial_partner.vat
            tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_partner(
                commercial_partner)
            self._ubl_add_tax_scheme(
                tax_scheme_dict, party_tax_scheme, ns, version=version)

    @api.model
    def _ubl_add_party_legal_entity(
            self, commercial_partner, parent_node, ns, version='2.1'):
        party_legal_entity = etree.SubElement(
            parent_node, ns['cac'] + 'PartyLegalEntity')

        registration_name = etree.SubElement(
            party_legal_entity, ns['cbc'] + 'RegistrationName')
        registration_name.text = commercial_partner.name
        # Lubi dodat tag za Company_Id
        company_id = etree.SubElement(
            party_legal_entity, ns['cbc'] + 'CompanyID')
        company_id.text = str(commercial_partner.company_registry)

        self._ubl_add_address(
            commercial_partner, 'RegistrationAddress', party_legal_entity,
            ns, version=version)

    @api.model
    def _ubl_add_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        commercial_partner = partner.commercial_partner_id
        party = etree.SubElement(parent_node, ns['cac'] + node_name)
        # --- Dodao LUBI -------
        if commercial_partner.vat:
            endpoint = etree.SubElement(party, ns["cbc"] + "EndpointID", schemeID="9948")
            endpoint.text = commercial_partner.vat[2:]
        # ---------------------

        #if commercial_partner.website:
        #    website = etree.SubElement(party, ns['cbc'] + 'WebsiteURI')
        #    website.text = commercial_partner.website
        self._ubl_add_party_identification(
            commercial_partner, party, ns, version=version)
        party_name = etree.SubElement(party, ns['cac'] + 'PartyName')
        name = etree.SubElement(party_name, ns['cbc'] + 'Name')
        name.text = commercial_partner.name
        if partner.lang:
            self._ubl_add_language(partner.lang, party, ns, version=version)
        self._ubl_add_address(
            partner, 'PostalAddress', party, ns, version=version)
        self._ubl_add_party_tax_scheme(
            commercial_partner, party, ns, version=version)
        if commercial_partner.is_company or company:
            self._ubl_add_party_legal_entity(
                commercial_partner, party, ns, version='2.1')
        self._ubl_add_contact(partner, party, ns, version=version)

    @api.model
    def _ubl_add_customer_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        """Please read the docstring of the method _ubl_add_supplier_party"""
        if company:
            if partner:
                assert partner.commercial_partner_id == company.partner_id, \
                    'partner is wrong'
            else:
                partner = company.partner_id
        customer_party_root = etree.SubElement(
            parent_node, ns['cac'] + node_name)
        if not company and partner.commercial_partner_id.ref:
            customer_ref = etree.SubElement(
                customer_party_root, ns['cbc'] + 'SupplierAssignedAccountID')
            customer_ref.text = partner.commercial_partner_id.ref
        self._ubl_add_party(
            partner, company, 'Party', customer_party_root, ns,
            version=version)


        # TODO: rewrite support for AccountingContact + add DeliveryContact
        # Additionnal optional args
        if partner and not company and partner.parent_id:
            self._ubl_add_contact(
                partner, customer_party_root, ns,
                node_name='AccountingContact', version=version)

    @api.model
    def _ubl_add_supplier_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        """The company argument has been added to properly handle the
        'ref' field.
        In Odoo, we only have one ref field, in which we are supposed
        to enter the reference that our company gives to its
        customers/suppliers. We unfortunately don't have a native field to
        enter the reference that our suppliers/customers give to us.
        So, to set the fields CustomerAssignedAccountID and
        SupplierAssignedAccountID, I need to know if the partner for
        which we want to build the party block is our company or a
        regular partner:
        1) if it is a regular partner, call the method that way:
            self._ubl_add_supplier_party(partner, False, ...)
        2) if it is our company, call the method that way:
            self._ubl_add_supplier_party(False, company, ...)
        """
        if company:
            if partner:
                assert partner.commercial_partner_id == company.partner_id, \
                    'partner is wrong'
            else:
                partner = company.partner_id
        supplier_party_root = etree.SubElement(
            parent_node, ns['cac'] + node_name)
        if not company and partner.commercial_partner_id.ref:
            supplier_ref = etree.SubElement(
                supplier_party_root, ns['cbc'] + 'CustomerAssignedAccountID')
            supplier_ref.text = partner.commercial_partner_id.ref
        self._ubl_add_party(
            partner, company, 'Party', supplier_party_root, ns,
            version=version)

    @api.model
    def _ubl_add_delivery(
            self, delivery_partner, parent_node, ns, version='2.1'):
        delivery = etree.SubElement(parent_node, ns['cac'] + 'Delivery')

        logger.info('UBL: Dodat tag Delivery %s', delivery)


        delivery_date = etree.SubElement(
            delivery, ns['cbc'] + 'ActualDeliveryDate')
        if self.l10n_rs_turnover_date:
            delivery_date.text = self.l10n_rs_turnover_date.strftime("%Y-%m-%d")
        else:
            delivery_date.text = self.invoice_date.strftime("%Y-%m-%d")

        #logger.warning('UBL: dodat tag Actual delivery date %s', delivery_date)
        delivery_location = etree.SubElement(
            delivery, ns['cac'] + 'DeliveryLocation')

        self._ubl_add_address(
            delivery_partner, 'Address', delivery_location, ns,
            version=version)
        self._ubl_add_party(
            delivery_partner, False, 'DeliveryParty', delivery, ns,
            version=version)

    @api.model
    def _ubl_add_delivery_terms(
            self, incoterm, parent_node, ns, version='2.1'):
        delivery_term = etree.SubElement(
            parent_node, ns['cac'] + 'DeliveryTerms')
        delivery_term_id = etree.SubElement(
            delivery_term, ns['cbc'] + 'ID',
            schemeAgencyID='6', schemeID='INCOTERM')
        delivery_term_id.text = incoterm.code
    @api.model
    def _ubl_add_delivery_date(
            self, date, parent_node, ns, version='2.1'):
        delivery = etree.SubElement(parent_node, ns['cac'] + 'Delivery')
        delivery_date = etree.SubElement(
            parent_node, ns['cac'] + 'ActualDeliveryDate' + date)

    @api.model
    def _ubl_add_payment_terms(
            self, payment_term, parent_node, ns, version='2.1'):
        pay_term_root = etree.SubElement(
            parent_node, ns['cac'] + 'PaymentTerms')
        pay_term_note = etree.SubElement(
            pay_term_root, ns['cbc'] + 'Note')
        pay_term_note.text = payment_term.name

    @api.model
    def _ubl_add_line_item(
            self, line_number, name, product, type, quantity, uom, parent_node,
            ns, seller=False, currency=False, price_subtotal=False,
            qty_precision=3, price_precision=2, version='2.1'):
        line_item = etree.SubElement(
            parent_node, ns['cac'] + 'LineItem')
        line_item_id = etree.SubElement(line_item, ns['cbc'] + 'ID')
        line_item_id.text = str(line_number)
        if not uom.unece_code:
            raise UserError(_(
                "Missing UNECE code on unit of measure '%s'")
                            % uom.name)
        quantity_node = etree.SubElement(
            line_item, ns['cbc'] + 'Quantity',
            unitCode=uom.unece_code)
        quantity_node.text = str(quantity)
        if currency and price_subtotal:
            line_amount = etree.SubElement(
                line_item, ns['cbc'] + 'LineExtensionAmount',
                currencyID=currency.name)
            line_amount.text = str(price_subtotal)
            price_unit = 0.0
            # Use price_subtotal/qty to compute price_unit to be sure
            # to get a *tax_excluded* price unit
            if not float_is_zero(quantity, precision_digits=qty_precision):
                price_unit = float_round(
                    price_subtotal / float(quantity),
                    precision_digits=price_precision)
            price = etree.SubElement(
                line_item, ns['cac'] + 'Price')
            price_amount = etree.SubElement(
                price, ns['cbc'] + 'PriceAmount',
                currencyID=currency.name)
            price_amount.text = str(price_unit)
            base_qty = etree.SubElement(
                price, ns['cbc'] + 'BaseQuantity',
                unitCode=uom.unece_code)
            base_qty.text = '1'  # What else could it be ?
        logger.info("UBL_ADD_ITEM: pre slanja name =%s line_item=%s type=%s", name, line_item, type)
        self._ubl_add_item(
            name, product, line_item, ns, type=type, seller=seller,
            version=version)

    @api.model
    def _ubl_add_item(
            self, name, product, parent_node, ns, type='purchase',
            seller=False, version='2.1'):
        logger.info("UBL_ADD_ITEM: primljeni parametri %s %s %s", self, name, parent_node)
        '''Beware that product may be False (in particular on invoices)'''
        assert type in ('sale', 'purchase'), 'Wrong type param'
        assert name, 'name is a required arg'
        item = etree.SubElement(parent_node, ns['cac'] + 'Item')
        product_name = False
        seller_code = False
        if product:
            if type == 'purchase':
                if seller:
                    sellers = product._select_seller(
                        partner_id=seller, quantity=0.0, date=None,
                        uom_id=False)
                    if sellers:
                        product_name = sellers[0].product_name
                        seller_code = sellers[0].product_code
            if not seller_code:
                seller_code = product.default_code
            if not product_name:
                variant = ", ".join(
                    [v.name for v in product.product_template_attribute_value_ids])
                product_name = variant and "%s (%s)" % (product.name, variant) \
                               or product.name
        description = etree.SubElement(item, ns['cbc'] + 'Description')
        description.text = name
        name_node = etree.SubElement(item, ns['cbc'] + 'Name')
        name_node.text = name     # Lubi zbog sefa u polje name unosime  opis a ne product_name or name.split('\n')[0]
        #name_node.text = product_name or name.split('\n')[0]
        if seller_code:
            seller_identification = etree.SubElement(
                item, ns['cac'] + 'SellersItemIdentification')
            seller_identification_id = etree.SubElement(
                seller_identification, ns['cbc'] + 'ID')
            seller_identification_id.text = seller_code
        if product:
            if product.barcode:
                std_identification = etree.SubElement(
                    item, ns['cac'] + 'StandardItemIdentification')
                std_identification_id = etree.SubElement(
                    std_identification, ns['cbc'] + 'ID',
                    schemeAgencyID='6', schemeID='GTIN')
                std_identification_id.text = product.barcode
            # I'm not 100% sure, but it seems that ClassifiedTaxCategory
            # contains the taxes of the product without taking into
            # account the fiscal position
            logger.info('-----UBL ADD_ITEM: type =%s product.taxes_id= %s product.supplier_taxes_id= %s', type, product.taxes_id, product.supplier_taxes_id)
            if type == 'sale':
                taxes = product.taxes_id
            else:
                taxes = product.supplier_taxes_id
            if taxes:
                for tax in taxes:
                    self._ubl_add_tax_category(
                        tax, item, ns, node_name='ClassifiedTaxCategory',
                        version=version)
            for attribute_value in product.product_template_attribute_value_ids:
                item_property = etree.SubElement(
                    item, ns['cac'] + 'AdditionalItemProperty')
                property_name = etree.SubElement(
                    item_property, ns['cbc'] + 'Name')
                property_name.text = attribute_value.attribute_id.name
                property_value = etree.SubElement(
                    item_property, ns['cbc'] + 'Value')
                property_value.text = attribute_value.name

    @api.model
    def _ubl_add_tax_subtotal(
            self, taxable_amount, tax_amount, tax, currency_code,
            parent_node, ns, version='2.1'):
        logger.info('****************  UBL_ADD_TAX_SUBTOTAL self =%s, taxable_amount = %s, tax_amount=%s tax =%s', self, taxable_amount, tax_amount, tax)
        prec = self.env['decimal.precision'].precision_get('Account')
        tax_subtotal = etree.SubElement(parent_node, ns['cac'] + 'TaxSubtotal')
        if not float_is_zero(taxable_amount, precision_digits=prec):
            taxable_amount_node = etree.SubElement(
                tax_subtotal, ns['cbc'] + 'TaxableAmount',
                currencyID=currency_code)
            taxable_amount_node.text = '%0.*f' % (prec, taxable_amount)
        tax_amount_node = etree.SubElement(
            tax_subtotal, ns['cbc'] + 'TaxAmount', currencyID=currency_code)
        tax_amount_node.text = '%0.*f' % (prec, tax_amount)
        logger.info('****************  UBL_ADD_TAX_SUBTOTAL tax_amount_node.text =%s', tax_amount_node.text)
        if (
                tax.amount_type == 'percent' and
                not float_is_zero(tax.amount, precision_digits=prec+3)):
            percent = etree.SubElement(
                tax_subtotal, ns['cbc'] + 'Percent')
            percent.text = str(
                float_round(tax.amount, precision_digits=2))
        self._ubl_add_tax_category(tax, tax_subtotal, ns, version=version)

    @api.model
    def _ubl_add_tax_category(
            self, tax, parent_node, ns, node_name='TaxCategory',
            version='2.1'):

        logger.info('-----UBL ADD_TAX_CATEGORY: self =%s', self)
        logger.info('-----UBL ADD_TAX_CATEGORY: tax =%s  %s', tax.unece_categ_id, tax.unece_categ_code)
        logger.info('-----UBL ADD_TAX_CATEGORY: InvoiceLine =%s', self.invoice_line_ids.tax_ids)
        i = 0
   #     for line in self.tax_line_ids:
            #           logger.info('-----UBL ADD_TAX_CATEGORY: taxLine ID =%s, tTAX_ID =%s RAZLOG = %s', line[i].id, line[i].tax_id, line[i].x_pdv_sifra_razloga)
    #        ++i
        tax_category = etree.SubElement(parent_node, ns['cac'] + node_name)
        if not tax.unece_categ_id:
            raise UserError(_(
                "Missing UNECE Tax Category on tax '%s'" % tax.name))
        # tax_category_id = etree.SubElement(
        #     tax_category, ns['cbc'] + 'ID', schemeID='UN/ECE 5305',
        #     schemeAgencyID='6')
        tax_category_id = etree.SubElement(
            tax_category, ns['cbc'] + 'ID')
        tax_category_id.text = tax.unece_categ_code  # ovde se preuzima jedna od kategorija
        tax_name = etree.SubElement(
            tax_category, ns['cbc'] + 'Name')
        tax_name.text = tax.name
        if tax.amount_type == 'percent':
            tax_percent = etree.SubElement(
                tax_category, ns['cbc'] + 'Percent')
            tax_percent.text = str(tax.amount)
        i = 0
        for line in self.invoice_line_ids:
            if line[i].unece_categ_id == tax:
                logger.info('-----UBL Tax kategorija na proizvodu i liniji su jednaki : line[i].tax_ids =%s', line[i].unece_categ_id)
                if tax_category_id.text != 'S':  # Ima neko oslobodjenje
                    tax_exemption_code = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
                    if line[i].x_pdv_sifra_razloga:
                        tax_exemption_code.text = line[i].x_pdv_sifra_osnova.code
                    else:
                        tax_exemption_code.text = "NIJE NADEN RAZLOG"
            else:
                logger.info('-----UBL Tax kategorija na proizvodu i liniji  Nisu jednaki : line[i].tax_ids =%s',
                            line[i].tax_ids)
                if line[i].unece_categ_id.code != 'S':  # Ima neko oslobodjenje
                    if tax_category_id.text != 'S':  # Ima neko oslobodjenje
                        tax_exemption_code = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
                        if line[i].x_pdv_sifra_osnova:
                            tax_exemption_code.text = line[i].x_pdv_sifra_osnova.code
                        else:
                            tax_exemption_code.text = "NIJE NADEN RAZLOG"

            ++i

        #    tax_exemption_code.text = 16    # ovde treba preuzeti razlog koji se nalazi na
        tax_exemption_text = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReason')
        if self.x_broj_odluke:
            tax_exemption_text.text = self.x_broj_odluke
        else:
            tax_exemption_text.text = ""

        tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
        self._ubl_add_tax_scheme(
            tax_scheme_dict, tax_category, ns, version=version)




 #    @api.model
 #    def _ubl_add_tax_category(
 #            self, tax, parent_node, ns, node_name='TaxCategory',
 #            version='2.1'):
 #
 #        logger.info('-----UBL ADD_TAX_CATEGORY: self =%s', self)
 #        logger.info('-----UBL ADD_TAX_CATEGORY: tax =%s', tax)
 #        logger.info('-----UBL ADD_TAX_CATEGORY: taxLine =%s', self.invoice_line_ids)
 #        i=0
 #        for line in self.invoice_line_ids:
 # #           logger.info('-----UBL ADD_TAX_CATEGORY: taxLine ID =%s, tTAX_ID =%s RAZLOG = %s', line[i].id, line[i].tax_id, line[i].x_pdv_sifra_razloga)
 #            ++i
 #        tax_category = etree.SubElement(parent_node, ns['cac'] + node_name)
 #        if not tax.unece_categ_id:
 #            raise UserError(_(
 #                "Missing UNECE Tax Category on tax '%s'" % tax.name))
 #       # tax_category_id = etree.SubElement(
 #       #     tax_category, ns['cbc'] + 'ID', schemeID='UN/ECE 5305',
 #       #     schemeAgencyID='6')
 #        tax_category_id = etree.SubElement(
 #            tax_category, ns['cbc'] + 'ID')
 #        tax_category_id.text = tax.unece_categ_code  # ovde se preuzima jedna od kategorija
 #        tax_name = etree.SubElement(
 #            tax_category, ns['cbc'] + 'Name')
 #        tax_name.text = tax.name
 #        if tax.amount_type == 'percent':
 #            tax_percent = etree.SubElement(
 #                tax_category, ns['cbc'] + 'Percent')
 #            tax_percent.text = str(tax.amount)
 #
 #
 #
 #
 #        ################     Original na V10 #############################################
 #        # i=0
 #        # for line in self.tax_line_ids:
 #        #     if line[i].tax_id == tax:
 #        #         if tax_category_id.text != 'S':    # Ima neko oslobodjenje
 #        #             tax_exemption_code = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
 #        #             if line[i].x_pdv_sifra_razloga:
 #        #                 tax_exemption_code.text = line[i].x_pdv_sifra_razloga
 #        #             else:
 #        #                 tax_exemption_code.text = "NIJE NADEN RAZLOG"
 #        #
 #        #     ++i
 #
 #        #    tax_exemption_code.text = 16    # ovde treba preuzeti razlog koji se nalazi na
 #        #    tax_exemption_text = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReason')
 #        #    tax_exemption_text.text = 'Oslob.po clanu 24 - promet bez naknade'
 #        ##############   Ovo je original na V10     ##############################################
 #
 #

    @api.model
    def _ubl_get_tax_scheme_dict_from_tax(self, tax):
        if not tax.unece_type_id:
            raise UserError(_(
                "Missing UNECE Tax Type on tax '%s'" % tax.name))
        tax_scheme_dict = {
            'id': tax.unece_type_code,
            'name': False,
            'type_code': False,
        }
        return tax_scheme_dict

    @api.model
    def _ubl_add_tax_scheme(
            self, tax_scheme_dict, parent_node, ns, version='2.1'):
        tax_scheme = etree.SubElement(parent_node, ns['cac'] + 'TaxScheme')
        if tax_scheme_dict.get('id'):
            tax_scheme_id = etree.SubElement(
                tax_scheme, ns['cbc'] + 'ID', schemeID='UN/ECE 5153',
                schemeAgencyID='6')
            tax_scheme_id.text = tax_scheme_dict['id']
        if tax_scheme_dict.get('name'):
            tax_scheme_name = etree.SubElement(tax_scheme, ns['cbc'] + 'Name')
            tax_scheme_name.text = tax_scheme_dict['name']
        if tax_scheme_dict.get('type_code'):
            tax_scheme_type_code = etree.SubElement(
                tax_scheme, ns['cbc'] + 'TaxTypeCode')
            tax_scheme_type_code.text = tax_scheme_dict['type_code']

    @api.model
    def _ubl_get_nsmap_namespace(self, doc_name, version="2.1"):
        nsmap = {
            None: "urn:oasis:names:specification:ubl:schema:xsd:" + doc_name,
            "cec":  "urn:oasis:names:specification:ubl:"
                    "schema:xsd:CommonExtensionComponents-2",
            "cac": "urn:oasis:names:specification:ubl:"
                   "schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:"
                   "CommonBasicComponents-2",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsd": "http://www.w3.org/2001/XMLSchema",
            "sbt": "http://mfin.gov.rs/srbdt/srbdtext"
                   '',
            "urn": "oasis:names:specification:ubl:schema:xsd:Invoice-2",
        }
        ns = {
            "cac": "{urn:oasis:names:specification:ubl:schema:xsd:"
                   "CommonAggregateComponents-2}",
            "cac": "{urn:oasis:names:specification:ubl:"
                   "schema:xsd:CommonAggregateComponents-2}",
            "cbc": "{urn:oasis:names:specification:ubl:schema:xsd:"
                   "CommonBasicComponents-2}",
            "xsi": "{http://www.w3.org/2001/XMLSchema-instance}",
            "xsd": "{http://www.w3.org/2001/XMLSchema}",
            "sbt": "{http://mfin.gov.rs/srbdt/srbdtext}"
                   '',
            "urn": "{oasis:names:specification:ubl:schema:xsd:Invoice-2}",
        }
        return nsmap, ns
# Izmena hederu za refundacije
    @api.model
    def _ubl_get_nsmap_namespaceCN(self, doc_name, version='2.1'):
        nsmap = {
            None: 'urn:oasis:names:specification:ubl:schema:xsd:' + doc_name,
            'cec': 'urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonExtensionComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:'
                   'schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonBasicComponents-2',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                   '',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
                   '',
            'sbt': 'http://mfin.gov.rs/srbdt/srbdtext'
                   '',
            }
        ns = {
            'cec': 'urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonExtensionComponents-2',
            'cac': '{urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonAggregateComponents-2}',
            'cbc': '{urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonBasicComponents-2}',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                   '',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
                   '',
            'sbt': 'http://mfin.gov.rs/srbdt/srbdtext'
                   '',
        }
        return nsmap, ns

    def _ubl_check_xml_schema(self, xml_string, document, version="2.1"):
        """Validate the XML file against the XSD"""
        xsd_file = "base_ubl/data/xsd-{}/maindoc/UBL-{}-{}.xsd".format(
            version, document, version
        )
        xsd_etree_obj = etree.parse(file_open(xsd_file))
        official_schema = etree.XMLSchema(xsd_etree_obj)
        try:
            t = etree.parse(BytesIO(xml_string))
            official_schema.assertValid(t)
        except Exception as e:
            # if the validation of the XSD fails, we arrive here
            logger = logging.getLogger(__name__)
            logger.info("The XML file is invalid against the XML Schema Definition")
            logger.info(xml_string)
            logger.info(e)
            raise UserError(
                _(
                    "The UBL XML file is not valid against the official "
                    "XML Schema Definition. The XML file and the "
                    "full error have been written in the server logs. "
                    "Here is the error, which may give you an idea on the "
                    "cause of the problem : %s."
                )
                % str(e)
            )
        return True

    @api.model
    def _ubl_add_xml_in_pdf_buffer(self, xml_string, xml_filename, buffer):
        # Add attachment to PDF content.
        reader = PdfFileReader(buffer)
        writer = PdfFileWriter()
        writer.appendPagesFromReader(reader)
        writer.addAttachment(xml_filename, xml_string)
        # show attachments when opening PDF
        writer._root_object.update(
            {NameObject("/PageMode"): NameObject("/UseAttachments")}
        )
        new_buffer = BytesIO()
        writer.write(new_buffer)
        return new_buffer

    @api.model
    def _embed_ubl_xml_in_pdf_content(self, xml_string, xml_filename, pdf_content):
        """Add the attachments to the PDF content.
        Use the pdf_content argument, which has the binary of the PDF
        -> it will return the new PDF binary with the embedded XML
        (used for qweb-pdf reports)
        """
        self.ensure_one()
        logger.debug("Starting to embed %s in PDF", xml_filename)

        with BytesIO(pdf_content) as reader_buffer:
            buffer = self._ubl_add_xml_in_pdf_buffer(
                xml_string, xml_filename, reader_buffer
            )
        pdf_content = buffer.getvalue()
        buffer.close()

        logger.info("%s file added to PDF content", xml_filename)
        return pdf_content

    @api.model
    def embed_xml_in_pdf(
            self, xml_string, xml_filename, pdf_content=None, pdf_file=None
    ):
        """
        2 possible uses:
        a) use the pdf_content argument, which has the binary of the PDF
        -> it will return the new PDF binary with the embedded XML
        (used for qweb-pdf reports)
        b) OR use the pdf_file argument, which has the full path to the
        original PDF file
        -> it will re-write this file with the new PDF
        (used for py3o reports, *_ubl_py3o modules in this repo)
        """
        assert pdf_content or pdf_file, "Missing pdf_file or pdf_content"
        if pdf_file:
            with open(pdf_file, "rb") as f:
                pdf_content = f.read()
        updated_pdf_content = self._embed_ubl_xml_in_pdf_content(
            xml_string, xml_filename, pdf_content
        )
        if pdf_file:
            with open(pdf_file, "wb") as f:
                f.write(updated_pdf_content)
        return updated_pdf_content
    # ==================== METHODS TO PARSE UBL files

    @api.model
    def ubl_parse_customer_party(self, customer_party_node, ns):
        ref_xpath = customer_party_node.xpath(
            'cac:SupplierAssignedAccountID', namespaces=ns)
        party_node = customer_party_node.xpath('cac:Party', namespaces=ns)[0]
        partner_dict = self.ubl_parse_party(party_node, ns)
        partner_dict['ref'] = ref_xpath and ref_xpath[0].text or False
        return partner_dict

    @api.model
    def ubl_parse_supplier_party(self, customer_party_node, ns):
        ref_xpath = customer_party_node.xpath(
            'cac:CustomerAssignedAccountID', namespaces=ns)
        party_node = customer_party_node.xpath('cac:Party', namespaces=ns)[0]
        partner_dict = self.ubl_parse_party(party_node, ns)
        partner_dict['ref'] = ref_xpath and ref_xpath[0].text or False
        return partner_dict

    @api.model
    def ubl_parse_party(self, party_node, ns):
        partner_name_xpath = party_node.xpath(
            'cac:PartyName/cbc:Name', namespaces=ns)
        vat_xpath = party_node.xpath(
            'cac:PartyTaxScheme/cbc:CompanyID', namespaces=ns)
        email_xpath = party_node.xpath(
            'cac:Contact/cbc:ElectronicMail', namespaces=ns)
        phone_xpath = party_node.xpath(
            'cac:Contact/cbc:Telephone', namespaces=ns)
        fax_xpath = party_node.xpath(
            'cac:Contact/cbc:Telefax', namespaces=ns)
        website_xpath = party_node.xpath(
            'cbc:WebsiteURI', namespaces=ns)
        partner_dict = {
            'vat': vat_xpath and vat_xpath[0].text or False,
            'name': partner_name_xpath and partner_name_xpath[0].text or False,
            'email': email_xpath and email_xpath[0].text or False,
            'website': website_xpath and website_xpath[0].text or False,
            'phone': phone_xpath and phone_xpath[0].text or False,
            'fax': fax_xpath and fax_xpath[0].text or False,
        }
        address_xpath = party_node.xpath('cac:PostalAddress', namespaces=ns)
        if address_xpath:
            address_dict = self.ubl_parse_address(address_xpath[0], ns)
            partner_dict.update(address_dict)
        return partner_dict

    @api.model
    def ubl_parse_address(self, address_node, ns):
        country_code_xpath = address_node.xpath(
            'cac:Country/cbc:IdentificationCode',
            namespaces=ns)
        country_code = country_code_xpath and country_code_xpath[0].text \
                       or False
        state_code_xpath = address_node.xpath(
            'cbc:CountrySubentityCode', namespaces=ns)
        state_code = state_code_xpath and state_code_xpath[0].text or False
        zip_xpath = address_node.xpath('cbc:PostalZone', namespaces=ns)
        zip = zip_xpath and zip_xpath[0].text and \
              zip_xpath[0].text.replace(' ', '') or False
        address_dict = {
            'zip': zip,
            'state_code': state_code,
            'country_code': country_code,
        }
        return address_dict

    @api.model
    def ubl_parse_delivery(self, delivery_node, ns):
        party_xpath = delivery_node.xpath('cac:DeliveryParty', namespaces=ns)
        if party_xpath:
            partner_dict = self.ubl_parse_party(party_xpath[0], ns)
        else:
            partner_dict = {}
        delivery_address_xpath = delivery_node.xpath(
            'cac:DeliveryLocation/cac:Address', namespaces=ns)
        if not delivery_address_xpath:
            delivery_address_xpath = delivery_node.xpath(
                'cac:DeliveryAddress', namespaces=ns)
        if delivery_address_xpath:
            address_dict = self.ubl_parse_address(
                delivery_address_xpath[0], ns)
        else:
            address_dict = {}
        delivery_dict = {
            'partner': partner_dict,
            'address': address_dict,
        }
        return delivery_dict

    def ubl_parse_incoterm(self, delivery_term_node, ns):
        incoterm_xpath = delivery_term_node.xpath("cbc:ID", namespaces=ns)
        if incoterm_xpath:
            incoterm_dict = {'code': incoterm_xpath[0].text}
            return incoterm_dict
        return {}

    def ubl_parse_product(self, line_node, ns):
        barcode_xpath = line_node.xpath(
            "cac:Item/cac:StandardItemIdentification/cbc:ID[@schemeID='GTIN']",
            namespaces=ns)
        code_xpath = line_node.xpath(
            "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=ns)
        product_dict = {
            'barcode': barcode_xpath and barcode_xpath[0].text or False,
            'code': code_xpath and code_xpath[0].text or False,
        }
        return product_dict

    # ======================= METHODS only needed for testing

    # Method copy-pasted from edi/base_business_document_import/
    # models/business_document_import.py
    # Because we don't depend on this module
    def get_xml_files_from_pdf(self, pdf_file):
        """Returns a dict with key = filename, value = XML file obj"""
        logger.info('Trying to find an embedded XML file inside PDF')
        res = {}
        try:
            fd = StringIO(pdf_file)
            pdf = PdfFileReader(fd)
            logger.debug('pdf.trailer=%s', pdf.trailer)
            pdf_root = pdf.trailer['/Root']
            logger.debug('pdf_root=%s', pdf_root)
            embeddedfiles = pdf_root['/Names']['/EmbeddedFiles']['/Names']
            i = 0
            xmlfiles = {}  # key = filename, value = PDF obj
            for embeddedfile in embeddedfiles[:-1]:
                mime_res = mimetypes.guess_type(embeddedfile)
                if mime_res and mime_res[0] in ['application/xml', 'text/xml']:
                    xmlfiles[embeddedfile] = embeddedfiles[i+1]
                i += 1
            logger.debug('xmlfiles=%s', xmlfiles)
            for filename, xml_file_dict_obj in xmlfiles.items():
                try:
                    xml_file_dict = xml_file_dict_obj.getObject()
                    logger.debug('xml_file_dict=%s', xml_file_dict)
                    xml_string = xml_file_dict['/EF']['/F'].getData()
                    xml_root = etree.fromstring(xml_string)
                    logger.debug(
                        'A valid XML file %s has been found in the PDF file',
                        filename)
                    res[filename] = xml_root
                except:
                    continue
        except:
            pass
        logger.info('Valid XML files found in PDF: %s', res.keys())
        return res
