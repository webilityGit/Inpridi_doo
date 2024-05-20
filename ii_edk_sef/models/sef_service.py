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
from odoo.exceptions import UserError
from collections import namedtuple
import codecs
import time

import logging
_logger = logging.getLogger(__name__)


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
        _logger.info("Preuzimanje sa SEF-a self= %s API= %s", self, self.company_id.efaktura_api_url)
        if self.company_id.efaktura_api_url:
            url = self.company_id.efaktura_api_url + "/"
        else:
            raise UserError(_(
                "Neuspesan upit u SEFF! URL za pristup SEF-u nije postavljen. Obavesti adrministratora o ovome"))

        if self.company_id.efaktura_api_key:
            apikey = self.company_id.efaktura_api_key
        else:
            raise UserError(_(
                "Neuspesan upit u SEFF! API Key za pristup SEF-u nije postavljen. Obavesti adrministratora o ovome"))

        _logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s key = %s', url,
                    self.company_id.efaktura_api_key)

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
                        teamID = config_param.approval_team_id.id
                        visibility = config_param.visibility
                        docType = config_param.docType
                        classificationID = ""
                        if doc_move == 'in':
                            classificationID = config_param.classificationID_U
                        if doc_move == 'out':
                            classificationID = config_param.classificationID_I
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
                        "approval_team_id": teamID, # uzeti iz config fajla
                        "source": "sef",
                        "document_type": docType, # uzeti iz konfig fajla
                        "clasification_number": classificationID, # uzeti iz konfig fajla
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
            _logger.info("Zavrsena obrada jednog datuma %s", za_datum)
            time.sleep(3)

        return


