from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from .selection import (DocumentSource, DocumentSefStatus, DocumentMove, SaveFormat, IzvorniOblik, ArhiveState)
from datetime import datetime
import requests
import base64
import logging
_logger = logging.getLogger(__name__)


class CreateNewDocumentPackage(models.Model):
    _inherit = 'ii.edk.document.package'
    def create_new_edk(self,record_data):
        newdocpcg_id = doc.create({
            "name": self.env['ir.sequence'].next_by_code('ii.edk.document.package'),
            "document_type": "invoice_in",
            "document_date": issdate,
            "state": "draft",
            "method": "button",
            "visibility": visibility,  # Uzeti iz config fajla
            "initiator_user_id": userID,  # uzeti iz config fajla
            "company_id": companyID,  # uzeti iz config fajla
            "approval_team_id": teamID,  # uzeti iz config fajla
            "source": "sef",
            "partner_id": partner.id if partner else False,
            "document_ref": docref,
            "sef_status": pid.NewInvoiceStatus,
            "efaktura_id": str(pid.PurchaseInvoiceId),
            "datum_dospeca": duedate,
            "amount_total": float(payableamaunt)
        })

        newdoc_id = docpdf.create({
            "document_package_id": newdocpcg_id.id,
            "name": "sef_faktura.pdf",
            "file_name": "sef_faktura.pdf"
        })

        attachmentPDF = {
            "name": "sef_faktura.pdf",
            "datas": node,
            "res_field": "file",
            "res_model": "ii.edk.document",
            "res_id": newdoc_id.id
        }
        attpdf.create(attachmentPDF)

