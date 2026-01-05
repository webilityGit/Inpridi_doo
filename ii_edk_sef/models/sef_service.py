# -*- coding: utf-8 -*-
from datetime import datetime as dt
import datetime

from odoo import _, models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import string
from lxml import etree
from json import dumps
from datetime import datetime
from datetime import timedelta
# from httplib2 import Http
import requests
import json
import base64
from odoo.exceptions import UserError
from collections import namedtuple
import codecs
import time
import re
from lxml import etree as ET

import logging
_logger = logging.getLogger(__name__)
DEMO_EFAKTURA_URL = 'https://demoefaktura.mfin.gov.rs/api/publicApi'
EFAKTURA_URL = 'https://efakturadev.mfin.gov.rs/api/publicApi'

from odoo.exceptions import ValidationError as Alert


class SEFServiceGetInvoiceWizard(models.TransientModel):
    # _name = 'ii.sef.getinvoice.wizard'
    #
    # date_start = fields.Date(string='Datum od',default=fields.Date.today)
    # date_end = fields.Date(string='Datum do', default=fields.Date.today)
    # company_id = fields.Many2one(
    #     "res.company",
    #     "Company",
    #     default=lambda self: self.env.company,
    # )
    _inherit = 'ii.sef.getinvoice.wizard'
    #_description = 'Config Parameters for electronic workbook of received and sent documents '

    @api.model
    def create_vendor_bill_from_xml(self, xml_filename, journal_code='BILL'):
        # 1️⃣ Pronađi attachment po imenu fajla
        attachment = self.env['ir.attachment'].search([('name', '=', xml_filename)], limit=1)
        if not attachment:
            raise ValueError(f"Nije pronađen attachment sa nazivom: {xml_filename}")

        # 2️⃣ Pronađi odgovarajući journal (vendor bills)
        journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('code', '=', journal_code)
        ], limit=1)
        if not journal:
            raise ValueError(f"Nije pronađen purchase journal sa kodom '{journal_code}'")

        # 3️⃣ Kreiraj bill pomoću interne Odoo funkcije
        invoices = journal._create_document_from_attachment(attachment_ids=attachment.ids)

        # 4️⃣ Ako želiš da vratiš ID fakture ili akciju
        return invoices and invoices[0] or False


    def _strip_namespace(self, xml_bytes):
        xml_bytes = re.sub(b'xmlns(:[a-zA-Z0-9]+)?="[^"]+"', b'', xml_bytes)
        xml_bytes = re.sub(b'<(/?)([a-zA-Z0-9]+):', b'<\\1', xml_bytes)
        return xml_bytes
    
    def _find_invoice_node(self, cleaned_data):
        _logger.info("!!! ETfid1 tree = %s", cleaned_data[:200])
        
        parsed = etree.fromstring(cleaned_data) ######## XML shema 
        nodes = parsed.xpath('//env:DocumentBody', namespaces={
                          'env': 'urn:eFaktura:MinFinrs:envelop:schema'
                    })
        for node in nodes:
            n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice")
            for n2 in n1:
                invoice_xml = ET.tostring(n2)
                return invoice_xml
                ##_logger.info("!!! ETfid2222 tree = %s", n2)
            
        
        tree = ET.ElementTree(ET.fromstring(cleaned_data))
        ##tree = cleaned_data
        _logger.info("!!! ETfid2  tree = %s", tree)
        root = tree.getroot()
  
        invoice_elem = root.find('.//Invoice')
        if invoice_elem is None:
          raise UserError("No <Invoice> node found in the XML.")

        
        invoice_xml = ET.tostring(invoice_elem, encoding='utf-8')
        return invoice_xml
  
      #return untangle.parse(io.BytesIO(invoice_xml))

    def _add_attachment(self, dockument_package_id, file_name, data):
        _logger.info("!!!USAO u  AddATT data = %s", data)
        encoded_data = base64.b64encode(data)
       # use_namespace = True
       # raw_data = base64.b64decode(data)
        _logger.info("!!!USAO u  ATT1 encoded data = %s", encoded_data)
       # cleaned_data = self._strip_namespace(data)
       # _logger.info("!!!USAO u  ATT2 cleaneddata = %s", cleaned_data)
        invoice_xml = self._find_invoice_node(data)
        _logger.info("!!!USAO u  ATT3 invoiceXML = %s", invoice_xml)
        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "res_model": "ii.edk.document.package",
                "res_id": dockument_package_id,
                "datas": base64.b64encode(invoice_xml),
                "store_fname": file_name,
                "type": "binary",
            }
        )
        _logger.info("!!!ATTACHEMENt %s ", attachment)
        return attachment

    def check_invoices(self):
        httpclient_logger = logging.getLogger("http.client")
        logging.basicConfig(level=logging.DEBUG)

        #### potrebno za dekodiranje json u python object ---------RADI za python 2.x
        def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
        def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

        ### definicije koje se izvlace iz settings!
        # apikey = '28b4d787-0ed4-414d-97db-8d891fe042cc'  # api za demo
        #apikey = '2d1e1218-0b1a-48a9-bbec-ec3e681fefc0'   # api za live
        #url = 'https://efaktura.mfin.gov.rs/api/publicApi/'

        ###### dODATAK ZA SLANJE i PRIJEM NA SEF   ##############################
        #_logger.info("Preuzimanje sa SEF-a self= %s API= %s", self, self.company_id.efaktura_api_url)
        
        #if self.company_id.efaktura_api_url:
        #    url = self.company_id.efaktura_api_url + "/"
        #else:
        #    raise UserError(_(
        #        "Neuspesan upit u SEFF! URL za pristup SEF-u nije postavljen. Obavesti adrministratora o ovome"))
        if self.company_id.l10n_rs_edi_demo_env:
            #url = self.env["account.move"].company_id.l10n_rs_edi_demo_env + "/"
            url = DEMO_EFAKTURA_URL if self.company_id.l10n_rs_edi_demo_env else EFAKTURA_URL
            url = url + "/"
        else:
            raise UserError(_(
                "Neuspesan upit u SEFF! URL za pristup SEF-u nije postavljen. Obavesti adrministratora o ovome"))

        if self.company_id.l10n_rs_edi_api_key:
            apikey = self.company_id.l10n_rs_edi_api_key
        else:
            raise UserError(_(
                "Neuspesan upit u SEFF! API Key za pristup SEF-u nije postavljen. Obavesti adrministratora o ovome"))

        _logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s key = %s', url,
                    self.company_id.l10n_rs_edi_api_key)

        message_headers_json = {
           'Content-Type': 'application/xml',
           'ApiKey': apikey,
           'accept': 'application/json'
        }
        ####  

        
        date_generated = [self.date_start + timedelta(days=x) for x in range(0, (self.date_end-self.date_start).days)]
        ############# za svaki datum iz opsega    
        doc =  self.env['ii.edk.document.package']
        docpdf =  self.env['ii.edk.document']
        attpdf =  self.env['ir.attachment']
        for za_datum in date_generated:
            command = url + 'purchase-invoice/changes?date=' + za_datum.strftime("%Y-%m-%d");
            r = requests.post(command, headers = message_headers_json, data = '')
            if r.status_code != 200:
                _logger.info('Neuspesan poziv = status = %s, naredba= %s', r.status_code, command)

                raise UserError(_(
                    "Neuspesan upit u SEFF! Kod greske je = %s  razlog = %s")
                                % (r.status_code, r.text))
            #    print(response)
            x = json2obj(r.content)
            _logger.info("80-ZZZZZZZZZZZZZZa za datum %s = %s", za_datum, r.content)


            for pid in x:
                postoji = doc.search([
                    ('efaktura_id', '=', str(pid.PurchaseInvoiceId))
                ])
                if postoji: ######### raditi update
                    _logger.info("88-ZZZZZZZZZZZZZZa datum %s ---- nasao POSTOJECI PurchaseID %s with status = %s -- u bazi %s",za_datum, pid.PurchaseInvoiceId, pid.NewInvoiceStatus, postoji)
                    postoji.sudo().sef_status = pid.NewInvoiceStatus
                    continue
                else: ### raditi insert
                    _logger.info("92-ZZZZZZZZZZZZZZa za datum %s ---- nasao NOVI PurchaseID %s with status = %s ",za_datum, pid.PurchaseInvoiceId, pid.NewInvoiceStatus)
                    command = url + 'purchase-invoice/xml?invoiceId=' + str(pid.PurchaseInvoiceId)
                    r2 = requests.get(command, headers = message_headers_json)
                    parsed = etree.fromstring(r2.content) ######## XML shema 

                    #_logger.info("************************* XML = %s", r2.content)
                    nodes = parsed.xpath('//env:DocumentBody', namespaces={
                          'env': 'urn:eFaktura:MinFinrs:envelop:schema'
                    })
                
                    
                    for node in nodes:
                        ### PayableAmount
                        n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount")
                        for n2 in n1:
                            payableamaunt = n2.text ### iznos za placanje

                        n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DueDate")
                        for n2 in n1:
                            duedate = n2.text

                        ### datum izdavanja
                        n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate")    
                        for n2 in n1:
                            issdate = n2.text
                        ### document ref
                        n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")    
                        for n2 in n1:
                            docref = n2.text
                            break ### samo prvi nam treba!!!
                        #### partner PIB
                        n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID")
                        _logger.info("TEST TEST Sadrzaju ukome treba da se nadje PIB, sadrzaj od n1 %s  ", n1)

                        for n2 in n1:
                            partner_pib = n2.text
                            is_rs_in = partner_pib.find('RS')
                            _logger.info("TEST TEST Ovo bi trebalo da bude partner_pib =  %s  ", partner_pib)
                            if is_rs_in == -1:

                                partner = self.env['res.partner'].search([
                                    ('vat','=',partner_pib), ('is_company', '=', True)
                                ])
                                if not partner:
                                    partner_pib_rs = 'RS' + str(partner_pib)
                                    _logger.info("TEST TEST Sada trazimo partnera po %s", partner_pib_rs)
                                    partner = self.env['res.partner'].search([
                                        ('vat', '=', partner_pib_rs), ('is_company', '=', True)
                                    ])
                                _logger.info("TEST TEST Nije nadjen RS u tekstu PIB-a, pretraga dala rezultat za partnera=%s ", partner)

                            else:   # ako nije pronadjen partner sa PIB-om trazimo partnera sa RSPIB-om
                                partner_pib_rs = partner_pib
                                _logger.info("TEST TEST Sada trazimo partnera po %s", partner_pib_rs)
                                partner = self.env['res.partner'].search([
                                    ('vat', '=', partner_pib_rs), ('is_company', '=', True)
                                ])
                                _logger.info(
                                    "TEST TEST Nadjen RS u tekstu PIB-a, pretraga dala rezultat za partnera=%s ",
                                    partner)

                            break ### samo prvi nam treba!!!

                    ##############
                    _logger.info("ZZZZZZZZZZZZZZa PROCITAO due=%s iss=%s  docref=%s, pib=%s, iznos=%s", duedate, issdate, docref, partner_pib,payableamaunt)
                    context = self._context
                    current_uid = context.get('uid')
                    l_korisnik = self.env['res.users'].browse(current_uid)
                    userID= l_korisnik.id
                    # kompanija = self.env.context['allowed_company_ids'][0]
                    kompanija = 1
                    config_params = self.env['ii.edk.config'].search([], limit=1)
                    _logger.info("TEST TEST sada dobijamo slogove config params %s", config_params)
                    config_param = config_params[0]
                    _logger.info("TEST TEST sada dobijamo konkretan slog config params %s", config_param)
                    companyID = 1
                    teamID = ""
                    visibility = "approvers"
                    if config_param:
                        companyID = config_param.company_id.id
                        teamID = config_param.approval_participant_id.id
                        visibility = config_param.visibility
                        docType = config_param.docType
                        classificationID = config_param.classificationID_U
                    if pid.NewInvoiceStatus == 'Cancelled':
                        docref=docref + '/C'
                    newdocpcg_id = doc.create({
                        "name": self.env['ir.sequence'].next_by_code('ii.edk.document.package'),
                        "document_type": "invoice_in",
                        "document_date": issdate,
                        "state": "draft",
                        "method": "button",
                        "visibility": visibility,   #Uzeti iz config fajla
                        "initiator_user_id": userID,         #uzeti iz config fajla
                        "company_id": companyID,    # uzeti iz config fajla
                        "approval_participant_id": teamID, # uzeti iz config fajla
                        "source": "sef",
                        "document_type": docType.id if docType else False, # uzeti iz konfig fajla
                        "classification_number": classificationID, # uzeti iz konfig fajla
                        "partner_id": partner.id if partner else False,
                        "document_ref": docref,
                        "sef_status": pid.NewInvoiceStatus,
                        "efaktura_id": str(pid.PurchaseInvoiceId),
                        "datum_dospeca": duedate,
                        "amount_total": float(payableamaunt)
                    })
                    ####            ################### document PDF
                    newdoc_id =  docpdf.create({
                        "document_package_id": newdocpcg_id.id,
                        "name": "sef_faktura.pdf",
                        "file_name":"sef_faktura.pdf"
                    })
                    #   
                    # newxmldoc_id =  docpdf.create({
                    #     "document_package_id": newdocpcg_id.id,
                    #     "name": "sef_faktura.xml",
                    #     "file_name":"sef_ubl_faktura.xml"
                    # })
                    # #                    
#  Sada treba sacuvati procitani xml kao attachement uz dokumenat ulazne fakture

                    self._add_attachment(newdocpcg_id.id, "sef_faktura.xml", r2.content) 
    # sada treba zapisati xml file
                    # i kreirati BILL
                    self.create_vendor_bill_from_xml("sef_faktura.xml", journal_code='BILL')

                    # attachmentXML = self.env['ir.attachment'].create({
                    #     'name': 'sef_ubl_faktuta.xml',
                    #     'type': 'binary',
                    #     'datas': base64.b64encode(r2.content),
                    #     'res_model': 'ii.edk.document',   # model na koji se odnosi
                    #     'res_id': newdocpcg_id.id,                 # ID zapisa u tom modelu
                    #     'mimetype': 'application/xml', # opcionalno
                    # })
#
                    # attachmentXML = {
                    #     "name":"sef_ubl_faktuta.xml",
                    #     "datas":r2.content,
                    #     "res_field": "file",
                    #     "res_model":"ii.edk.document",
                    #     "res_id":newxmldoc_id.id
                    #     }        
                    # attpdf.create(attachmentXML)

                    nodes = parsed.xpath('//env:DocumentPdf//text()', namespaces={
                         'env': 'urn:eFaktura:MinFinrs:envelop:schema'
                    })
                    for node in nodes:
                        attachmentPDF = {
                        "name":"sef_faktura.pdf",
                        "datas":node,
                        "res_field": "file",
                        "res_model":"ii.edk.document",
                        "res_id":newdoc_id.id
                        }        
                        attpdf.create(attachmentPDF)

                    ####            ################### Attacmenti
                    nodes = parsed.xpath('//env:DocumentBody', namespaces={
                              'env': 'urn:eFaktura:MinFinrs:envelop:schema'
                    })
                    for node in nodes:
                        n1 = node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AdditionalDocumentReference")
                        for n2 in n1:
                             for element in n2.getiterator('{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID'):
                                  attname = element.text
                             for element in n2.getiterator('{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}EmbeddedDocumentBinaryObject'):
                                  attcont = element.text
                             newdoc_id =  docpdf.create({
                                  "document_package_id": newdocpcg_id.id,
                                   "name": attname,
                                   "file_name":attname
                             })
                             attachmentPDF = {
                                 "name":attname,
                                 "datas":attcont,
                                 "res_field": "file",
                                 "res_model":"ii.edk.document",
                                 "res_id":newdoc_id.id
                             }
                             attpdf.create(attachmentPDF)
                             
                    
                    namespace = {
                        'env': 'urn:eFaktura:MinFinrs:envelop:schema',
                        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
                        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
                    }
                    
                    
                    #########################################
                    
                    #  PROVERITI DA LI JE "parsed" XML fajl #
                    
                    #########################################

                    # Load and parse the XML file
                    #tree = ET.ElementTree(parsed)
                    #root = tree.getroot()

                    # Extracting invoice lines
                    invoice_lines = []

                    #ne prolazi
                    #for line in root.findall('cac:InvoiceLine', namespace):
                    #    line_id = line.find('cbc:ID', namespace).text
                    #    quantity = line.find('cbc:InvoicedQuantity', namespace).text
                    #    line_amount = line.find('cbc:LineExtensionAmount', namespace).text
                    #
                    #    # TaxTotal
                    #    tax_amount = line.find('cac:TaxTotal/cbc:TaxAmount', namespace).text
                    #
                    #    tax_category_id = line.find('cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:ID', namespace).text
                    #    tax_category_name = line.find('cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Name', namespace).text
                    #    tax_category_percentage = line.find('cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent', namespace).text
                    #    tax_category_scheme = line.find('cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID', namespace).text
                    #
                    #    item_description = line.find('cac:Item/cbc:Description', namespace).text
                    #    item_name = line.find('cac:Item/cbc:Name', namespace).text
                    #    sellers_item_id = line.find('cac:Item/cac:SellersItemIdentification/cbc:ID', namespace).text
                    #
                    #    
                    #    classified_tax_category_id = line.find('cac:Item/cac:ClassifiedTaxCategory/cbc:ID', namespace).text
                    #    classified_tax_category_name = line.find('cac:Item/cac:ClassifiedTaxCategory/cbc:Name', namespace).text
                    #    classified_tax_category_percent = line.find('cac:Item/cac:ClassifiedTaxCategory/cbc:Percent', namespace).text
                    #    classified_tax_category_tax_scheme_id = line.find('cac:Item/cac:ClassifiedTaxCategory/cac:TaxScheme/cbc:ID', namespace).text
                    #
                    #    price_amount = line.find('cac:Price/cbc:PriceAmount', namespace).text
                    #    base_quantity = line.find('cac:Price/cbc:BaseQuantity', namespace).text
#
                    #    invoice_lines.append({
                    #        'line_id': line_id,
                    #        'quantity': quantity,
                    #        'line_amount': line_amount,
                    #        'tax_amount': tax_amount,
                    #        'tax_category_id': tax_category_id,
                    #        'tax_category_name': tax_category_name,
                    #        'tax_category_percentage': tax_category_percentage,
                    #        'tax_category_scheme': tax_category_scheme,
                    #        'item_description': item_description,
                    #        'item_name': item_name,
                    #        'sellers_item_id': sellers_item_id,
                    #        'classified_tax_category_id': classified_tax_category_id,
                    #        'classified_tax_category_name': classified_tax_category_name,
                    #        'classified_tax_category_percent': classified_tax_category_percent,
                    #        'classified_tax_category_tax_scheme_id': classified_tax_category_tax_scheme_id,
                    #        'price_amount': price_amount,
                    #        'base_quantity': base_quantity
                    #    })
                    
                    #Pronalazenje podataka za invoice_lines
                    body_nodes = parsed.xpath('//env:DocumentBody', namespaces={'env': namespace['env']})

                    for body_node in body_nodes:
                        for line_node in body_node.getiterator("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine"):
                            #InvoiceLine
                            line_id = line_node.xpath('string(.//cbc:ID)', namespaces=namespace)
                            line_quantity = line_node.xpath('string(.//cbc:InvoicedQuantity)', namespaces=namespace)
                            line_ext_amount = line_node.xpath('string(.//cbc:LineExtensionAmount)', namespaces=namespace)
                            #TaxTotal
                            tax_total_amount = line_node.xpath('string(.//cac:TaxTotal/cbc:TaxAmount)', namespaces=namespace)
                            #TaxSubtotal
                            tax_subtotal_taxable_amount = line_node.xpath('string(.//cac:TaxSubtotal/cbc:TaxableAmount)', namespaces=namespace)
                            tax_subtotal_tax_amount = line_node.xpath('string(.//cac:TaxSubtotal/cbc:TaxAmount)', namespaces=namespace)
                            tax_subtotal_percent = line_node.xpath('string(.//cac:TaxSubtotal/cbc:Percent)', namespaces=namespace)
                            #TaxCategory
                            tax_category_id = line_node.xpath('string(.//cac:TaxCategory/cbc:ID)', namespaces=namespace)
                            tax_category_percent = line_node.xpath('string(.//cac:TaxCategory/cbc:Percent)', namespaces=namespace)
                            #TaxScheme
                            tax_scheme_id = line_node.xpath('string(.//cac:TaxScheme/cbc:ID)', namespaces=namespace)
                            #Item
                            item_description = line_node.xpath('string(.//cbc:Description)', namespaces=namespace)
                            item_name = line_node.xpath('string(.//cbc:Name)', namespaces=namespace)
                            #ClassifiedTaxCategory
                            classified_tax_category_id = line_node.xpath('string(.//cac:ClassifiedTaxCategory/cbc:ID)', namespaces=namespace)
                            classified_tax_category_percent = line_node.xpath('string(.//cac:ClassifiedTaxCategory/cbc:Percent)', namespaces=namespace)
                            #ClassifiedTaxCategory -> TaxScheme
                            classified_tax_category_tax_scheme_id = line_node.xpath('string(.//cac:ClassifiedTaxCategory/cac:TaxScheme/cbc:ID)', namespaces=namespace)
                            #Price
                            price_amount = line_node.xpath('string(.//cac:Price/cbc:PriceAmount)', namespaces=namespace)

                            invoice_lines.append({
                                'line_id': line_id,
                                'line_quantity': line_quantity,
                                'line_ext_amount': line_ext_amount,
                                'tax_total_amount': tax_total_amount,
                                'tax_subtotal_taxable_amount': tax_subtotal_taxable_amount,
                                'tax_subtotal_tax_amount': tax_subtotal_tax_amount,
                                'tax_subtotal_percent': tax_subtotal_percent,
                                'tax_category_id': tax_category_id,
                                'tax_category_percent': tax_category_percent,
                                'tax_scheme_id': tax_scheme_id,
                                'item_description': item_description,
                                'item_name': item_name,
                                'classified_tax_category_id': classified_tax_category_id,
                                'classified_tax_category_percent': classified_tax_category_percent,
                                'classified_tax_category_tax_scheme_id': classified_tax_category_tax_scheme_id,
                                'price_amount': price_amount,
                            })

                    #####################
                    #Kreiranje linija na osnovu invoice_lines
                    #########################################

                    invoice_line_model = self.env['xf.document.invoice.lines']

                    for line in invoice_lines:
                        #priprema podataka
                        tax_cat_code = line.get('classified_tax_category_id')
                        tax_cat_percent = float(line.get('classified_tax_category_percent') or 0.0)
                        tax_cat_id = False
                        if tax_cat_code == 'S':
                            combined_code = f"{tax_cat_code}{int(tax_cat_percent)}"
                        if combined_code:
                            tax_cat_id = self.env['ii.pdv.category'].search([('code', '=', combined_code)], limit=1).id
                        
                        _logger.info("LINEE: %s %s %s", tax_cat_code, tax_cat_percent, combined_code)
                        try:
                            invoice_line_model.create({
                                'invoice_line': line.get('item_name') or line.get('item_description') or 'Unnamed item',
                                'quantity': float(line.get('line_quantity') or 0.0),
                                'vat': float(tax_cat_percent or line.get('tax_category_percent') or 0.0),
                                'document_package_id': newdocpcg_id.id,
                                'tax_category_code': tax_cat_id if tax_cat_id else None,
                                'price': float(line.get('price_amount') or 0.0),
                                'total_price': float(line.get('line_ext_amount') or 0.0),
                            })
                        except Exception as e:
                            _logger.error("Ne uspelo kreiranje linija na osnovu dokumenta. ERROR: %s", e)

                    _logger.info("LOGGEERRRR %s", invoice_lines)
                    
                    ###########################################
                    
                    #  PROVERITI podatke za ubacivanje u odoo #
                    
                    ###########################################
                    
                    #for line in invoice_lines:
                    #    print(line)
                    
                    
            _logger.info("Zavrsena obrada jednog datuma %s", za_datum)
            time.sleep(3)

        return
