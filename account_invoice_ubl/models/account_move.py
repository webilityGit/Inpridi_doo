# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
import base64
import logging
from odoo import _, models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError
from lxml import etree
from json import dumps
from odoo.tools import float_is_zero, float_round

import requests
from collections import namedtuple
import datetime as dt
from datetime import datetime


logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "base.ubl"]

    tax_closing_show_multi_closing_warning = fields.Boolean(
        string="Show Multi Closing Warning",
        help="Check this box to show a warning for multiple closings."
    )

    def _ubl_add_header(self, parent_node, ns, version="2.1"):
        self.ensure_one()

    # TO DO na pocetku, treba utvrditi da li se radi o Konacnoj Fakturi. Ako jeste treba generisati xml kod za avansne fakture, pa tek onda nastaviti dalje.
    #    if self.move_type == 'out_invoice' and self.x_out_invoice_type == 'final':   # Znacu radi se o konacnoj fakturi
    #    Napisti posebnu metodu koja generise xml code predhodno izdate avansne fakture:
    #    for each avansna_faktura
    #          avansnaFaktura._add_header(avansna,parent_node, ns, version="2.1") koji treba da uradi:
    #     < xsd: InvoicedPrepaymentAmmount >
    #     < cbc: ID > Broj avansnog računa < / cbc: ID >
    #     < !-- Broj  avansnog  računa -->
    #     < cac: TaxTotal >
    #     < cbc: TaxAmount
    #     currencyID = "RSD" > 110 < / cbc: TaxAmount >
    #     < cac: TaxSubtotal >
    #     < cbc: TaxableAmount  currencyID = "RSD" > 400 < / cbc: TaxableAmount >
    #     < cbc: TaxAmount  currencyID = "RSD" > 80 < / cbc: TaxAmount >
    #     < cac: TaxCategory >
    #     < cbc: ID > S < / cbc: ID >
    #     < cbc: Percent > 20 < / cbc: Percent >
    #     < cac: TaxScheme >
    #     < cbc: ID > VAT < / cbc: ID >
    #     < / cac: TaxScheme >
    #     < / cac: TaxCategory >
    #     < / cac: TaxSubtotal >
    #     < cac: TaxSubtotal >
    #     < cbc: TaxableAmount  currencyID = "RSD" > 300 < / cbc: TaxableAmount >
    #     < cbc: TaxAmount  currencyID = "RSD" > 30 < / cbc: TaxAmount >
    #     < cac: TaxCategory >
    #     < cbc: ID > S < / cbc: ID >
    #     < cbc: Percent > 10 < / cbc: Percent >
    #     < cac: TaxScheme >
    #     < cbc: ID > VAT < / cbc: ID >
    #     < / cac: TaxScheme >
    #     < / cac: TaxCategory >
    #     < / cac: TaxSubtotal >
    #     < cac: TaxSubtotal >
    #     < cbc: TaxableAmount     currencyID = "RSD" > 200 < / cbc: TaxableAmount >
    #     < cbc: TaxAmount   currencyID = "RSD" > 0.0 < / cbc: TaxAmount >
    #     < cac: TaxCategory >
    #     < cbc: ID > E < / cbc: ID >
    #     < cbc: Percent > 0.0 < / cbc: Percent >
    #     < cac: TaxScheme >
    #     < cbc: ID > VAT < / cbc: ID >
    #     < / cac: TaxScheme >
    #     < / cac: TaxCategory >
    #     < / cac: TaxSubtotal >
    #     < / cac: TaxTotal >
    #     < / xsd: InvoicedPrepaymentAmmount >
    #
    # Posle ovoga treba generisati xml kod za redused Totals
    #     < xsd: ReducedTotals >
    #     < cac: TaxTotal >
    #     < cbc: TaxAmount  currencyID = "RSD" > 690 < / cbc: TaxAmount >
    #       < cac: TaxSubtotal >
    #           < cbc: TaxableAmount  currencyID = "RSD" > 800 < / cbc: TaxableAmount >
    #           < cbc: TaxAmount  currencyID = "RSD" > 160 < / cbc: TaxAmount >
    #           < cac: TaxCategory >
    #     < cbc: ID > S < / cbc: ID >
    #     < cbc: Percent > 20 < / cbc: Percent >
    #     < cac: TaxScheme >
    #     < cbc: ID > VAT < / cbc: ID >
    #     < / cac: TaxScheme >
    #     < / cac: TaxCategory >
    #     < / cac: TaxSubtotal >
    #     < cac: TaxSubtotal >
    #     < cbc: TaxableAmount  currencyID = "RSD" > 5300 < / cbc: TaxableAmount >
    #     < cbc: TaxAmount  currencyID = "RSD" > 530 < / cbc: TaxAmount >
    #     < cac: TaxCategory >
    #     < cbc: ID > S < / cbc: ID >
    #     < cbc: Percent > 10 < / cbc: Percent >
    #     < cac: TaxScheme >
    #     < cbc: ID > VAT < / cbc: ID >
    #     < / cac: TaxScheme >
    #     < / cac: TaxCategory >
    #     < / cac: TaxSubtotal >
    #     < cac: TaxSubtotal >
    #     < cbc: TaxableAmount currencyID = "RSD" > 3490 < / cbc: TaxableAmount >
    #     < cbc: TaxAmount  currencyID = "RSD" > 0.0 < / cbc: TaxAmount >
    #     < cac: TaxCategory >
    #     < cbc: ID > E < / cbc: ID >
    #     < cbc: Percent > 0.0 < / cbc: Percent >
    #     < cac: TaxScheme >
    #     < cbc: ID > VAT < / cbc: ID >
    #     < / cac: TaxScheme >
    #     < / cac: TaxCategory >
    #     < / cac: TaxSubtotal >
    #     < / cac: TaxTotal >
    #     < cac: LegalMonetaryTotal >
    #     < cbc: TaxExclusiveAmount  currencyID = "RSD" > 10490 < / cbc: TaxExclusiveAmount >
    #     < cbc: TaxInclusiveAmount  currencyID = "RSD" > 10280 < / cbc: TaxInclusiveAmount >
    #     < cbc: PayableAmount currencyID = "RSD" > 10280 < / cbc: PayableAmount >
    #     < / cac: LegalMonetaryTotal >
    #     < / xsd: ReducedTotals >
    #     < / sbt: SrbDtExt >
    #     < / cec: ExtensionContent >
    #     < / cec: UBLExtension >
    #     < / cec: UBLExtensions >

        #ubl_version = etree.SubElement(parent_node, ns["cbc"] + "UBLVersionID")
        ubl_version = etree.SubElement(parent_node, ns["cbc"] + "CustomizationID") # milan
        #ubl_version.text = version
    #    ubl_version.text = "urn: cen.eu:en16931: 2017  # compliant#urn:mfin.gov.rs:srbdt:2021" #milan
        ubl_version.text = "urn: cen.eu:en16931:2017#compliant#urn:mfin.gov.rs:srbdt:2022#conformant#urn:mfin.gov.rs:srbdtext:2022"  # lubi

        doc_id = etree.SubElement(parent_node, ns["cbc"] + "ID")
        doc_id.text = self.name
        issue_date = etree.SubElement(parent_node, ns["cbc"] + "IssueDate")
   #     issue_date.text = self.invoice_date.strftime("%Y-%m-%d")
        issue_date.text = datetime.today().strftime("%Y-%m-%d")  # datum slanja mora da bude aktuelni datum

   #
        #  -----
        if self.move_type == 'out_invoice':  # dueDate se ne salje kada je u pitanju knjizno odobrenje
            due_date = etree.SubElement(parent_node, ns['cbc'] + 'DueDate')
       #     due_date.text = datetime.today().strftime("%Y-%m-%d")
            due_date.text = self.invoice_date_due.strftime("%Y-%m-%d")
        # Lubi dodat cvor koji nije postojao

        if self.move_type == 'out_invoice':
            type_code = etree.SubElement(
                parent_node, ns['cbc'] + 'InvoiceTypeCode')

            if self.x_out_invoice_type == 'avans':
                type_code.text = '386'  # kod za avansne fakture   lubi 27.1.2023
    #        if any(l.product_id.product_tmpl_id.name == 'Down payment' and l.quantity > 0 for l in
    #               self.with_context({'lang': 'en_US'}).invoice_line_ids):
    #            type_code.text = '386'  # kod za avansne fakture
            else:
                type_code.text = '380'

            #        due_date = etree.SubElement(parent_node, ns['cbc'] + 'DueDate')
            #        due_date.text = self.date_due
        elif self.move_type == 'out_refund':
            type_code = etree.SubElement(
                parent_node, ns['cbc'] + 'CreditNoteTypeCode')
            type_code.text = '381'  # kod za knjizna odobrenja
    #    if self.comment:
    #        note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
    #        note.text = self.comment
        doc_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name
        # Lubi -proveravamo da li je korisnik budzeta i ako jeste dodajemo odgovarajuci tag.
        # Za budžetske korisnike je obavezno jedno od polja “broj narudžbine” ili “broj ugovora” ili
        # “broj sporazuma” kako bi SEF prihvatio e-Fakturu. Potrebno je da popunite jedno od ovih polja kako bi SEF prihvatio e-Fakturu.
        if self.partner_id.jbkjs and self.is_jn:
            buyer_reference = etree.SubElement(
                parent_node, ns['cbc'] + 'BuyerReference')
            buyer_reference.text = "JN-JBKJS:" + self.jbkjs

        #

        invoice_period = etree.SubElement(parent_node, ns["cac"] + "InvoicePeriod")
        descriptionCode = etree.SubElement(invoice_period, ns["cbc"] + "DescriptionCode")

        ## ToDo ovo treba doraditi da se koriste 3moguca koda:
        #    Начи одређивања када настаје пореска авеза, а може бити једна од три  вредности:
        #    35 – према датуму промета(BT72);
        #    432 – према  датуму плаћања(BT - 9);
        #    3 –  према  датуму издавања фактуре(BT - 2)
        ####


        # attachment = etree.SubElement(additional_document_reference, ns["cac"] + "Attachment")
        # #embeddedDocumentBinaryObject = etree.SubElement(attachment, ns["cbc"] + "EmbeddedDocumentBinaryObject")
        # #embeddedDocumentBinaryObject.text = "TEST"
        # binary_node = etree.SubElement(
        #     attachment,
        #     ns["cbc"] + "EmbeddedDocumentBinaryObject",
        #     mimeCode="application/pdf"
        # )
        # ctx = dict()
        # ctx["no_embedded_ubl_xml"] = True
        # ctx["force_report_rendering"] = True
        # pdf_inv = (
        #     self.with_context(ctx)
        #         .env.ref("account.account_invoices")
        #         ._render_qweb_pdf(self.ids)[0]
        # )
        # binary_node.text = base64.b64encode(pdf_inv)
        # AditionalDocumentReference

        # if self.invoice_payment_term_id:
        #     order_ref = etree.SubElement(parent_node, ns["cac"] + "OrderReference")
        #     order_ref_id = etree.SubElement(order_ref, ns["cbc"] + "ID")
        #     order_ref_id.text = sale_order_ref
        #milan
        # TODO: enable when below commit of 15.0 is back ported to 14.0
        # [IMP] account_edi(_*): Standalone UBL format + edi.format inheritance
        # https://github.com/odoo/odoo/commit/b58810a77bb4c432a6aef18413659b1ea7b25c71
        # or when migrating to 15.0
        # buyer_reference = etree.SubElement(parent_node, ns["cbc"] + "BuyerReference")
        # buyer_reference.text = self.ref or ""

        if self.move_type == 'out_invoice':

            if any(l.product_id.product_tmpl_id.name == 'Down payment' and l.quantity > 0 for l in
                   self.with_context({'lang': 'en_US'}).invoice_line_ids):
                descriptionCode.text = "432"


            else:
                if self.x_out_invoice_type == 'avans':
                    descriptionCode.text = "432"
                else:
                    descriptionCode.text = "35"

        if self.move_type == 'out_refund':
            descriptionCode.text = "0"

        #   Dodatak za tag ako je u pitanju knjizno odobrenje   Lubi jun 2022####
    def _ubl_add_billing_reference(self, parent_node, ns, version='2.1'):

        self.ensure_one()
        billing_ref = etree.SubElement(
            parent_node, ns['cac'] + '')
        if self.ref:
            invoice_ref_id = etree.SubElement(
                billing_ref, ns['cac'] + 'InvoiceDocumentReference')
            document_ref_id = etree.SubElement(invoice_ref_id, ns['cbc'] + 'ID')
            document_ref_id.text = self.ref
            issue_date = etree.SubElement(invoice_ref_id, ns['cbc'] + 'IssueDate')
            #     issue_date.text = self.date_invoice
            issue_date.text = datetime.today().strftime("%Y-%m-%d")  # datum slanja mora da bude aktuelni datum


    def _ubl_get_invoice_type_code(self):
        if self.move_type == "out_invoice":
            return "380"
        elif self.move_type == "out_refund":
            return "381"

    def _ubl_get_order_reference(self):
        """This method is designed to be inherited"""
 #       return self.invoice_origin
        if self.invoice_origin:
            return self.invoice_origin   # ovim se obezbedjuje veza sa sale orderom
        else:
            return self.ref      # Lubi, ovde bi trebalo da se nalazi broj porudjbenice kupca na osnovu koje se fakturise
    def _ubl_add_order_reference(self, parent_node, ns, version="2.1"):
        self.ensure_one()
        sale_order_ref = self._ubl_get_order_reference()
        if sale_order_ref:
            order_ref = etree.SubElement(parent_node, ns["cac"] + "OrderReference")
            order_ref_id = etree.SubElement(order_ref, ns["cbc"] + "ID")
            order_ref_id.text = sale_order_ref

    def _ubl_get_contract_document_reference_dict(self):
        """Result: dict with key = Doc Type Code, value = ID"""
        self.ensure_one()

        return {}
#####   LUbi preuzeto sa Nis ekspresa    ##################
    def _ubl_add_contract_document_reference(
            self, parent_node, ns, version='2.1'):

        self.ensure_one()
        if self.move_type == 'out_refund':
            cdr = etree.SubElement(parent_node, ns['cac'] + 'ContractDocumentReference')
            cdr_id = etree.SubElement(cdr, ns['cbc'] + 'ID')
            cdr_id.text = self.ref
        else:
            if self.x_broj_ugovora_jn:

                cdr = etree.SubElement(parent_node, ns['cac'] + 'ContractDocumentReference')
                cdr_id = etree.SubElement(cdr, ns['cbc'] + 'ID')
                cdr_id.text = self.x_broj_ugovora_jn
###################################################



  #  def _ubl_add_contract_document_reference(self, parent_node, ns, version="2.1"):
  #      self.ensure_one()
  #      cdr_dict = self._ubl_get_contract_document_reference_dict()
  #      for doc_type_code, doc_id in cdr_dict.items():
  #          cdr = etree.SubElement(parent_node, ns["cac"] + "ContractDocumentReference")
  #          cdr_id = etree.SubElement(cdr, ns["cbc"] + "ID")
  #          cdr_id.text = doc_id
  #          cdr_type_code = etree.SubElement(cdr, ns["cbc"] + "DocumentTypeCode")
  #          cdr_type_code.text = doc_type_code


   # original   v14 funkcija
    def _ubl_add_attachments(self, parent_node, ns, version="2.1"):
        self.ensure_one()
        if self.company_id.embed_pdf_in_ubl_xml_invoice and not self.env.context.get(
                "no_embedded_pdf"
        ):
    # provera , broja priloga koje treba poslati
            atts = self.env['ir.attachment'].search([('res_model', '=', 'account.move'), ('res_id', '=', self.id)])

            logger.info("ADD Attachements , nadjeni objekti %s %s ", len(atts), atts)
            if len(atts) > 2:
        #        raise UserError(_("Broj priloga je veci od 3! Smanjite broj priloga na dozvoljeni broj"))
                sefporuka = "** ODOO ERR ** Nije dozvoljeno slanje vise od 3 priloga. Visak priloga nije poslat"
                self.generate_internal_message(sefporuka)
            else:
                for prilog in atts:
                    #  Pripremamo ostale priloge za slanje
                    att_file_name = prilog.name
                    velicina_priloga = prilog.file_size
                    if velicina_priloga > 25165800:
        #                 raise UserError(_(
        #                     "Veličina bar jednog od priloga je je veća od 25 MB! Smanite veličinu i pokušajte ponovo"))
        #            sefporuka = "** SEF OK ** faktura usposno poslata na SEF = " + str(response.status_code)
                        sefporuka = "** ODOO Upozorenje ** Prilog " + str(prilog) + "Nije poslat jer je veci od 25165800 bajtova"
                        self.generate_internal_message(sefporuka)
        # prilog u xml
                    docu_reference = etree.SubElement(
                        parent_node, ns['cac'] + 'AdditionalDocumentReference')
                    docu_reference_id = etree.SubElement(docu_reference, ns['cbc'] + 'ID')
                    docu_reference_id.text = att_file_name
                    attach_node = etree.SubElement(docu_reference, ns['cac'] + 'Attachment')
                    binary_node = etree.SubElement(
                        attach_node, ns['cbc'] + 'EmbeddedDocumentBinaryObject', mimeCode="application/pdf", filename=att_file_name)
                    binary_node.text = prilog.datas


# A sada i prilog aktuelne fakture
            filename = "Invoice-" + self.name + ".pdf"
            docu_reference = etree.SubElement(
                parent_node, ns["cac"] + "AdditionalDocumentReference"
            )
            docu_reference_id = etree.SubElement(docu_reference, ns["cbc"] + "ID")
            docu_reference_id.text = filename
            attach_node = etree.SubElement(docu_reference, ns["cac"] + "Attachment")
            binary_node = etree.SubElement(
                attach_node,
                ns["cbc"] + "EmbeddedDocumentBinaryObject",
                mimeCode="application/pdf",
                filename=filename,
            )
            ctx = dict()
            ctx["no_embedded_ubl_xml"] = True
            ctx["force_report_rendering"] = True
        #    pdf_inv = (
        #        self.with_context(ctx)
        #        .env.ref("account.account_invoices")
        #        ._render_qweb_pdf(self.ids)[0]
        #    )
            pdf_env = self.with_context(ctx).env.ref("account.account_invoices")
            pdf_inv = (pdf_env._render_qweb_pdf(pdf_env.id, self.ids)[0])
            binary_node.text = base64.b64encode(pdf_inv)

  ################################################


    # def _ubl_add_attachments(self, parent_node, ns, version='2.1'):
    #     if (
    #             self.company_id.embed_pdf_in_ubl_xml_invoice and
    #             not self._context.get('no_embedded_pdf')):
    #         docu_reference = etree.SubElement(
    #             parent_node, ns['cac'] + 'AdditionalDocumentReference')
    #         docu_reference_id = etree.SubElement(
    #             docu_reference, ns['cbc'] + 'ID')
    #         docu_reference_id.text = 'Invoice-' + self.name + '.pdf'
    #         attach_node = etree.SubElement(
    #             docu_reference, ns['cac'] + 'Attachment')
    #         binary_node = etree.SubElement(
    #             attach_node, ns['cbc'] + 'EmbeddedDocumentBinaryObject',
    #             mimeCode="application/pdf")
    #         ctx = dict()
    #         ctx['no_embedded_ubl_xml'] = True
    #         pdf_inv = self.with_context(ctx).env.ref(
    #             'account.account_invoices').render_qweb_pdf(self.ids)[0]
    #         binary_node.text = base64.b64encode(pdf_inv)

    # def _ubl_add_attachments(self, parent_node, ns, version="2.1"):
    #     self.ensure_one()
    #     if self.company_id.embed_pdf_in_ubl_xml_invoice and not self.env.context.get(
    #         "no_embedded_pdf"
    #     ):
    #         atts = self.env['ir.attachment'].search([
    #             ('res_model', '=', 'account.move'),
    #             ('res_id', '=', self.id)
    #         ])
    #         if len(atts) > 3:
    #             raise UserError(_(
    #                 "Broj priloga je veci od 3! Smanjite broj priloga na dozvoljeni broj"))
    #
    #         for prilog in atts:
    #             # Pripremamo ostale priloge za slanje
    #             att_file_name = prilog.datas_fname
    #             velicina_priloga = prilog.file_size
    #             if velicina_priloga > 25165800:
    #                 raise UserError(_(
    #                     "Veličina bar jednog od priloga je je veća od 25 MB! Smanite veličinu i pokušajte ponovo"))
    #             docu_reference = etree.SubElement(
    #                 parent_node, ns['cac'] + 'AdditionalDocumentReference')
    #             docu_reference_id = etree.SubElement(docu_reference, ns['cbc'] + 'ID')
    #    #         docu_reference_id.text = att_file_name
    #             docu_reference_id.text = "TestFile.pdf"
    #             attach_node = etree.SubElement(docu_reference, ns['cac'] + 'Attachment')
    #             binary_node = etree.SubElement(
    #                 attach_node, ns['cbc'] + 'EmbeddedDocumentBinaryObject',
    #                 mimeCode="application/pdf", filename=att_file_name)
    #             ctx = self._context.copy()
    #             ctx['no_embedded_ubl_xml'] = False
    #             # binary_node.text = atts[0].datas.encode('base64')
    #             binary_node.text = prilog.datas
    #
    #         filename = "Invoice-" + self.name + ".pdf"
    #         docu_reference = etree.SubElement(
    #             parent_node, ns["cac"] + "AdditionalDocumentReference"
    #         )
    #         docu_reference_id = etree.SubElement(docu_reference, ns["cbc"] + "ID")
    #         docu_reference_id.text = filename
    #         attach_node = etree.SubElement(docu_reference, ns["cac"] + "Attachment")
    #         binary_node = etree.SubElement(
    #             attach_node,
    #             ns["cbc"] + "EmbeddedDocumentBinaryObject",
    #             mimeCode="application/pdf",
    #             filename=filename,
    #         )
    #         ctx = dict()
    #         ctx["no_embedded_ubl_xml"] = True
    #         ctx["force_report_rendering"] = True
    #         pdf_inv = (
    #             self.with_context(ctx)
    #             .env.ref("account.account_invoices")
    #             ._render_qweb_pdf(self.ids)[0]
    #         )
    #         binary_node.text = base64.b64encode(pdf_inv)

    def _ubl_add_legal_monetary_total(self, parent_node, ns, version="2.1"):
        self.ensure_one()
        monetary_total = etree.SubElement(parent_node, ns["cac"] + "LegalMonetaryTotal")
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        line_total = etree.SubElement(
            monetary_total, ns["cbc"] + "LineExtensionAmount", currencyID=cur_name
        )
        line_total.text = "%0.*f" % (prec, self.amount_untaxed)
        tax_excl_total = etree.SubElement(
            monetary_total, ns["cbc"] + "TaxExclusiveAmount", currencyID=cur_name
        )
        tax_excl_total.text = "%0.*f" % (prec, self.amount_untaxed)
        tax_incl_total = etree.SubElement(
            monetary_total, ns["cbc"] + "TaxInclusiveAmount", currencyID=cur_name
        )
        tax_incl_total.text = "%0.*f" % (prec, self.amount_total)
        prepaid_amount = etree.SubElement(
            monetary_total, ns["cbc"] + "PrepaidAmount", currencyID=cur_name
        )
        prepaid_value = self.amount_total - self.amount_residual
        prepaid_amount.text = "%0.*f" % (prec, prepaid_value)
        payable_amount = etree.SubElement(
            monetary_total, ns["cbc"] + "PayableAmount", currencyID=cur_name
        )
        payable_amount.text = "%0.*f" % (prec, self.amount_residual)

    def _ubl_add_invoice_line(self, parent_node, iline, line_number, ns, version="2.1"):
        self.ensure_one()
        cur_name = self.currency_id.name
        #  Dodato sa V10
        if self.move_type == 'out_invoice':
            line_root = etree.SubElement(
                parent_node, ns['cac'] + 'InvoiceLine')
        if self.move_type == 'out_refund':
            line_root = etree.SubElement(
                parent_node, ns['cac'] + 'CreditNoteLine')
        #   kraj

        # line_root = etree.SubElement(parent_node, ns["cac"] + "InvoiceLine")
        dpo = self.env["decimal.precision"]
        qty_precision = dpo.precision_get("Product Unit of Measure")
        price_precision = dpo.precision_get("Product Price")
        account_precision = self.currency_id.decimal_places
        line_id = etree.SubElement(line_root, ns["cbc"] + "ID")
        line_id.text = str(line_number)
        uom_unece_code = False
        # product_uom_id is not a required field on account.move.line
        # dodato sa V10
        if iline.product_uom_id and iline.product_uom_id.unece_code:
            uom_unece_code = iline.product_uom_id.unece_code
        if uom_unece_code:
            if self.move_type == 'out_invoice':
                quantity = etree.SubElement(line_root, ns['cbc'] + 'InvoicedQuantity',unitCode=uom_unece_code)
            if self.move_type == 'out_refund':
                quantity = etree.SubElement(line_root, ns['cbc'] + 'CreditedQuantity',unitCode=uom_unece_code)
        else:
            if self.move_type == 'out_invoice':
                quantity = etree.SubElement(line_root, ns['cbc'] + 'InvoicedQuantity')
            if self.move_type == 'out_refund':
                quantity = etree.SubElement(line_root, ns['cbc'] + 'CreditedQuantity',unitCode=uom_unece_code)
        # kraj

  # zamenjeno predhodnim

        # if iline.product_uom_id.unece_code:
        #     uom_unece_code = iline.product_uom_id.unece_code
        #     quantity = etree.SubElement(
        #         line_root, ns["cbc"] + "InvoicedQuantity", unitCode=uom_unece_code
        #     )
        # else:
        #     quantity = etree.SubElement(line_root, ns["cbc"] + "InvoicedQuantity")

   # kraj zamenjeno predhodnim

        qty = iline.quantity
        quantity.text = "%0.*f" % (qty_precision, qty)
        line_amount = etree.SubElement(
            line_root, ns["cbc"] + "LineExtensionAmount", currencyID=cur_name
        )
        line_amount.text = "%0.*f" % (account_precision, iline.price_subtotal)
        self._ubl_add_invoice_line_tax_total(iline, line_root, ns, version=version)
        logger.info("UBL_ADD_ITEM: parametri pre slanja %s %s %s", iline.name, iline.product_id, line_root)
        self._ubl_add_item(
            iline.name, iline.product_id, line_root, ns, type="sale", version=version
        )
        price_node = etree.SubElement(line_root, ns["cac"] + "Price")
        price_amount = etree.SubElement(
            price_node, ns["cbc"] + "PriceAmount", currencyID=cur_name
        )
        price_unit = 0.0
        # Use price_subtotal/qty to compute price_unit to be sure
        # to get a *tax_excluded* price unit
        if not float_is_zero(qty, precision_digits=qty_precision):
            price_unit = float_round(
                iline.price_subtotal / float(qty), precision_digits=price_precision
            )
        price_amount.text = "%0.*f" % (price_precision, price_unit)
        if uom_unece_code:
            base_qty = etree.SubElement(
                price_node, ns["cbc"] + "BaseQuantity", unitCode=uom_unece_code
            )
        else:
            base_qty = etree.SubElement(price_node, ns["cbc"] + "BaseQuantity")
        base_qty.text = "%0.*f" % (qty_precision, qty)

    def _ubl_add_invoice_line_tax_total(self, iline, parent_node, ns, version="2.1"):
        self.ensure_one()
        logger.info('USAO U 383 ****************  UBL_ADD_TAX_TOTAL  iline = %s', iline)
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        tax_total_node = etree.SubElement(parent_node, ns["cac"] + "TaxTotal")
        price = iline.price_unit * (1 - (iline.discount or 0.0) / 100.0)
        res_taxes = iline.tax_ids.compute_all(
            price,
            quantity=iline.quantity,
            product=iline.product_id,
            partner=self.partner_id,
        )
        logger.info('USAO U 394 **************** res_taxes = %s', res_taxes)
        tax_total = float_round(
            res_taxes["total_included"] - res_taxes["total_excluded"],
            precision_digits=prec,
        )
        logger.info('USAO U 399 **************** tax_total = %s', tax_total)
        tax_amount_node = etree.SubElement(
            tax_total_node, ns["cbc"] + "TaxAmount", currencyID=cur_name
        )
        tax_amount_node.text = "%0.*f" % (prec, tax_total)
        if not float_is_zero(tax_total, precision_digits=prec):
            for res_tax in res_taxes["taxes"]:
                tax = self.env["account.tax"].browse(res_tax["id"])
                # we don't have the base amount in res_tax :-(
                logger.info('USAO U 408 neposredno pred poziv subtotal **** res_tax["amount"] = %s', res_tax["amount"])
                self._ubl_add_tax_subtotal(
                    False,
                    res_tax["amount"],
                    tax,
                    cur_name,
                    tax_total_node,
                    ns,
                    version=version,
                )

    def _ubl_add_tax_total(self, xml_root, ns, version="2.1"):
        self.ensure_one()
        cur_name = self.currency_id.name
        tax_total_node = etree.SubElement(xml_root, ns["cac"] + "TaxTotal")
        tax_amount_node = etree.SubElement(
            tax_total_node, ns["cbc"] + "TaxAmount", currencyID=cur_name
        )
        prec = self.currency_id.decimal_places
        tax_amount_node.text = "%0.*f" % (prec, self.amount_tax)

        logger.info('****************  UBL_ADD_TAX_TOTAL  self = %s', self )
    #####   sledeci deo koda treba proveriti
        if not float_is_zero(self.amount_tax, precision_digits=prec): # Lubi 7.12.22 tax subtotal je obavezan
            tax_lines = self.line_ids.filtered(lambda line: line.tax_line_id)

            logger.info('****************  TAX LINES  = %s', tax_lines)
            logger.info('****************  TAX totals  = %s', self.tax_totals)
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            for line in tax_lines:
                res.setdefault(
                    line.tax_line_id.tax_group_id,
                    {"base": 0.0, "amount": 0.0, "tax": False},
                )
           #     logger.info('****************  res DEFAULTS = %s', res)

                res[line.tax_line_id.tax_group_id]["amount"] += line.price_subtotal
            #    logger.info('****************  res POSLE = %s', res)
            #    tax_key_add_base = tuple(self._get_tax_key_for_group_add_base(line))
                tax_key_add_base = line.tax_line_id.id
                if tax_key_add_base not in done_taxes:
                    res[line.tax_line_id.tax_group_id]["base"] += line.tax_base_amount
                    res[line.tax_line_id.tax_group_id]["tax"] = line.tax_line_id
                    done_taxes.add(tax_key_add_base)
            res = sorted(res.items(), key=lambda l: l[0].sequence)
        #    logger.info('****************  res = %s, tax=%s', res, tax_key_add_base)
            logger.info('****************  res = %s,', res)
            for _group, amounts in res:
                logger.info('USAO U 456 neposredno pred poziv subtotal **** amounts["amount"] = %s', amounts["amount"])
                self._ubl_add_tax_subtotal(
                    amounts["base"],
                    self.tax_totals["amount_total"] - self.tax_totals["amount_untaxed"],
                #    amounts["amount"],
                    amounts["tax"],
                    cur_name,
                    tax_total_node,
                    ns,
                    version=version,
                )
        else:    ##   Lubi 7.12.2022   - dodatak za slucaj kada je treba obraditi posebno slucajeve PDV 0%

            self._ubl_add_tax_subtotal(
                self.invoice_line_ids.price_subtotal,
                0,
                self.invoice_line_ids.tax_ids,
                cur_name,
                tax_total_node,
                ns,
                version=version,
            )


    ########################
    # na ver 10 prdehodni deo koda zamenjen je sa :
    #     for tline in self.tax_line_ids:
    #         self._ubl_add_tax_subtotal(
    #             tline.base, tline.amount, tline.tax_id, cur_name,
    #             tax_total_node, ns, version=version)
    #

    #############    Ovo je originalan method koji je zamenjen verzijom 10,   #####################
    # def generate_invoice_ubl_xml_etree(self, version="2.1"):
    #     self.ensure_one()
    #     nsmap, ns = self._ubl_get_nsmap_namespace("Invoice-2", version=version)
    #     xml_root = etree.Element("Invoice", nsmap=nsmap)
    #     self._ubl_add_header(xml_root, ns, version=version)
    #     self._ubl_add_order_reference(xml_root, ns, version=version)
    #     self._ubl_add_contract_document_reference(xml_root, ns, version=version)
    #     self._ubl_add_attachments(xml_root, ns, version=version)
    #     self._ubl_add_supplier_party(
    #         False,
    #         self.company_id,
    #         "AccountingSupplierParty",
    #         xml_root,
    #         ns,
    #         version=version,
    #     )
    #     self._ubl_add_customer_party(
    #         self.partner_id,
    #         False,
    #         "AccountingCustomerParty",
    #         xml_root,
    #         ns,
    #         version=version,
    #     )
    #     # the field 'partner_shipping_id' is defined in the 'sale' module
    #     if hasattr(self, "partner_shipping_id") and self.partner_shipping_id:
    #         self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)
    #     # Put paymentmeans block even when invoice is paid ?
    #     payment_identifier = self.get_payment_identifier()
    #     self._ubl_add_payment_means(
    #         self.partner_bank_id,
    #         self.payment_mode_id,
    #         self.invoice_date_due,
    #         xml_root,
    #         ns,
    #         payment_identifier=payment_identifier,
    #         version=version,
    #     )
    #     if self.invoice_payment_term_id:
    #         self._ubl_add_payment_terms(
    #             self.invoice_payment_term_id, xml_root, ns, version=version
    #         )
    #     self._ubl_add_tax_total(xml_root, ns, version=version)
    #     self._ubl_add_legal_monetary_total(xml_root, ns, version=version)
    #
    #     line_number = 0
    #     for iline in self.invoice_line_ids:
    #         line_number += 1
    #         self._ubl_add_invoice_line(
    #             xml_root, iline, line_number, ns, version=version
    #         )
    #     return xml_root
#########################################################################
 ##########   Preneto sa v10   ##########################################
    def generate_invoice_ubl_xml_etree(self, version='2.1'):
        if self.move_type == 'out_invoice':
            nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
            xml_root = etree.Element('Invoice', nsmap=nsmap)
            logger.info('****************  out INVOICE =  nsmap =%s, ns=%s', nsmap, ns)
        elif self.move_type == 'out_refund':
            nsmap, ns = self._ubl_get_nsmap_namespaceCN('CreditNote-2', version=version)
            logger.info('****************  out refund =  nsmap =%s, ns=%s', nsmap, ns)
            # nsmap.cbc = ' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:sbt="http://mfin.gov.rs/srbdt/srbdtext" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2">'
            xml_root = etree.Element('CreditNote', nsmap=nsmap)
        # nsmap.cbc = xml_root + ' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:sbt="http://mfin.gov.rs/srbdt/srbdtext" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2">'

        self._ubl_add_header(xml_root, ns, version=version)
        logger.info('****************  Prosao poziv add hedera  xmlroot =%s, ns=%s', xml_root, ns)
        if self.move_type == 'out_invoice':
            self._ubl_add_order_reference(xml_root, ns, version=version)
            logger.info('****************  Prosao poziv order reference  xmlroot =%s, ns=%s', xml_root, ns)
        elif self.move_type == 'out_refund':
            self._ubl_add_billing_reference(xml_root, ns, version=version)
            logger.info('****************  Prosao poziv referenca na fakturu  xmlroot =%s, ns=%s', xml_root, ns)

        self._ubl_add_contract_document_reference(
            xml_root, ns, version=version)
        logger.info('****************  Prosao contract reference  xmlroot =%s, ns=%s', xml_root, ns)
        self._ubl_add_attachments(xml_root, ns, version=version)
        logger.info('****************  Prosao poziv add add_ttachement  xmlroot =%s, ns=%s', xml_root, ns)
        self._ubl_add_supplier_party(
            False, self.company_id, 'AccountingSupplierParty', xml_root, ns,
            version=version)
        logger.info('****************  Prosao poziv add supplierParty self.company_id =%s, ns=%s', self.company_id, ns)
        self._ubl_add_customer_party(
            self.partner_id, False, 'AccountingCustomerParty', xml_root, ns,
            version=version)
        logger.info('****************  Prosao poziv add add_customer_party partner_id =%s, ns=%s', self.partner_id, ns)
        # the field 'partner_shipping_id' is defined in the 'sale' module

        if self.move_type != 'out_refund':  # Lubi , kada je knjizno odobrenje, ili avansna faktura  tag deliveri se ne koristi.

            if any(l.product_id.product_tmpl_id.name == 'Down payment' and l.quantity > 0 for l in
                   self.with_context({'lang': 'en_US'}).invoice_line_ids):
                pass
            if self.x_out_invoice_type == "avans":
                pass
            else:
                if hasattr(self, 'partner_shipping_id') and self.partner_shipping_id:
                    self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)
                    logger.info('****************  Prosao poziv add add_delivery =%s, ns=%s',
                                self.partner_shipping_id, ns)
                else:
                    self._ubl_add_delivery(self.partner_id, xml_root, ns)
                    logger.info('****************  Prosao poziv add add_delivery =%s, ns=%s',
                                self.partner_id, ns)
                    self.partner_shipping_id = self.partner_id

        # Put paymentmeans block even when invoice is paid ?
        payment_identifier = self.get_payment_identifier()
        logger.info('PRE POZIVA UBL_PAYEMENT partner_bank =%s, payement_mode=%s, invoice_date_due=%s, payement_identifier=%s',
                    self.partner_bank_id, self.payment_mode_id, self.invoice_date_due, payment_identifier)
        self._ubl_add_payment_means(
            self.partner_bank_id, self.payment_mode_id, self.invoice_date_due,
            xml_root, ns, payment_identifier=payment_identifier,
            version=version)

        #  -----   Lubi  Datum prometa  ----

        if self.invoice_payment_term_id:
            self._ubl_add_payment_terms(
                self.invoice_payment_term_id, xml_root, ns, version=version)
        self._ubl_add_tax_total(xml_root, ns, version=version)
        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        for iline in self.invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(
                xml_root, iline, line_number, ns, version=version)
        return xml_root
   ###############  Kraj prenetog sa V10   ###############################

    def generate_ubl_xml_string(self, version="2.1"):
        self.ensure_one()
        assert self.state == "posted"
        assert self.move_type in ("out_invoice", "out_refund")
        logger.debug("Starting to generate UBL XML Invoice file")
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        # xml_root = self.with_context(lang=lang).generate_invoice_ubl_xml_etree(
        #     version=version
        # )
        # xml_string = etree.tostring(
        #     xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        # )
        # self._ubl_check_xml_schema(xml_string, "Invoice", version=version)
        # logger.debug(
        #     "Invoice UBL XML file generated for account invoice ID %d " "(state %s)",
        #     self.id,
        #     self.state,
        # )
        # logger.debug(xml_string.decode("utf-8"))
        # return xml_string
    ##################### V10 #######################
        xml_root = self.with_context(lang=lang). \
            generate_invoice_ubl_xml_etree(version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
 #       if self.move_type == 'out_invoice':
 #           self._ubl_check_xml_schema(xml_string, 'Invoice', version=version)
 #       if self.move_type == 'out_refund':
 #           self._ubl_check_xml_schema(xml_string, 'CreditNote', version=version)
        logger.debug(
            'Invoice UBL XML file generated for account invoice ID %d '
            '(state %s)', self.id, self.state)
        logger.debug(xml_string.decode('utf-8'))
        return xml_string
    #####################END v10 ################################



    def get_ubl_filename(self, version="2.1"):
        """This method is designed to be inherited"""
        return "UBL-Invoice-%s.xml" % version

    def get_ubl_version(self):
        return self.env.context.get("ubl_version") or "2.1"

    def get_ubl_lang(self):
        self.ensure_one()
        return self.partner_id.lang or "en_US"

    def add_xml_in_pdf_buffer(self, buffer):
        self.ensure_one()
        if self.is_ubl_sale_invoice_posted():
            version = self.get_ubl_version()
            xml_filename = self.get_ubl_filename(version=version)
            xml_string = self.generate_ubl_xml_string(version=version)
            buffer = self._ubl_add_xml_in_pdf_buffer(xml_string, xml_filename, buffer)
        return buffer

    def embed_ubl_xml_in_pdf(self, pdf_content):
        self.ensure_one()
        if self.is_ubl_sale_invoice_posted():
            version = self.get_ubl_version()
            xml_filename = self.get_ubl_filename(version=version)
            xml_string = self.generate_ubl_xml_string(version=version)
            pdf_content = self.embed_xml_in_pdf(
                xml_string, xml_filename, pdf_content=pdf_content
            )
        return pdf_content

    def attach_ubl_xml_file_button(self):
        self.ensure_one()
        assert self.move_type in ("out_invoice", "out_refund")
        assert self.state == "posted"
        version = self.get_ubl_version()
        xml_string = self.generate_ubl_xml_string(version=version)
    ###### dODATAK ZA SLANJE NA SEF   ##############################
        url = self.company_id.efaktura_api_url
        logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s headers = %s', url,
                    self.company_id.efaktura_api_key)
        # Lubi 22.6.2022 - url za slanje fakture se razlikuje ako se szeli automatsko slanje u CRF.
        curr_dt = datetime.now()

        sec2 = str(int((curr_dt - dt.datetime(2020, 1, 1)).total_seconds()))
        if self.auto_crf:
            #     url = "https://demoefaktura.mfin.gov.rs/api/publicApi/sales-invoice/ubl?requestId=" + self.name +"&sendToCir=Yes"
            url = url + "/sales-invoice/ubl?requestId=" + self.name + sec2 + "&sendToCir=Yes"
            bot_message = {
                'text': 'Hello from a Python script!'}
        else:
            #         url = "https://demoefaktura.mfin.gov.rs/api/publicApi/sales-invoice/ubl?requestId=" + self.name +"&sendToCir=No"
            url = url + "/sales-invoice/ubl?requestId=" + self.name + sec2 + "&sendToCir=No"
            bot_message = {
                'text': 'Hello from a Python script!'}

    #    message_headers = {
    #       'Content-Type': 'application/xml',
    #       'ApiKey': self.env['account.config.settings'].efaktura_api_key,
    #       'accept': 'text/plain'
    #    }
        message_headers = {
            'Content-Type': 'application/xml',
            'ApiKey': self.company_id.efaktura_api_key,
         #   'ApiKey': "28b4d787-0ed4-414d-97db-8d891fe042cc",
            'accept': 'text/plain'}
        if self.x_sent_to_sef == "sent_to_sef":
            self.generate_internal_message("ODOO INFO - faktura je već poslata u SEF. Nije moguće ponovno slanje!")
    #        raise UserError(_(
    #             "Faktura %s je vec poslata u SEF. Nije moguće ponovno slanje!") % (self.name))
        else:
            logger.info('!!!!!!!!!   ---   Ovo je URL koji smo poslali = %s headers = %s', url, message_headers)
            response = requests.post(url, headers = message_headers, data = xml_string)
            logger.info('!!!!!!!!! ---Ovo smo dobili kao odgovor %s tekst = %s', response.status_code, response.text)
            if response.status_code != 200:
                logger.info('  ERRRROR pri slanju !!!!! ovako izgleda formirani xml %s', xml_string)
                self.x_sent_to_sef = "err_sent_to_sef"
                #sefporuka = ("Neuspesno slanje fakture na server PU! URL = %s \n Kod greske je = %s \n  razlog = %s")
                #                % ( url, response.status_code , response.text))
                sefporuka = "** SEF ERR ** Neuspesno slanje fakture na server PU! URL = " + url + "\n Kod greske je =" + str(response.status_code) + "\n Razlog" + response.text
                self.generate_internal_message(sefporuka)
   #              raise UserError(_(
   #                 "Neuspesno slanje fakture na server PU! URL = %s \n Kod greske je = %s \n  razlog = %s")
   #                             % ( url, response.status_code , response.text))
               # print(response)
            else:
                self.x_sent_to_sef = "sent_to_sef"
                sefporuka = "** SEF OK ** faktura usposno poslata na SEF = " + str(response.status_code)
                self.generate_internal_message(sefporuka)


                filename = self.get_ubl_filename(version=version)
                attach = (
                    self.env["ir.attachment"]
                    .with_context({})
                    .create(
                        {
                            "name": filename,
                            "res_id": self.id,
                            "res_model": self._name,
                            "datas": base64.b64encode(xml_string),
                            # If default_type = 'out_invoice' in context, 'type'
                            # would take 'out_invoice' value by default !
                            "type": "binary",
                        }
                    )
                )
            #    action = self.env["ir.attachment"].action_get()
            #    action.update({"res_id": attach.id, "views": False, "view_mode": "form,tree"})
            #    return action


    def is_ubl_sale_invoice_posted(self):
        self.ensure_one()
        is_ubl = self.company_id.xml_format_in_pdf_invoice == "ubl"
        if is_ubl and self.is_sale_document() and self.state == "posted":
            return True
        return False

    def generate_internal_message(self, sef_poruka):
        # This function will generate an internal message
        self.env['mail.message'].create({
            'subject': '**** SEF Poruka ' + self.name,
            'message_type': 'comment',
            'body': sef_poruka,
        # This type defines that it is an internal note (the boolean 'internal only' for the mail.message.subtype
        # record 'Note' is set to true)
            'subtype_id': self.env.ref('mail.mt_note').id,
        # Current model and current record id
            'model': 'account.move',
            'res_id': self.id
        })
        return
