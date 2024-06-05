from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from .selection import (DocumentSource, DocumentSefStatus, DocumentMove, SaveFormat, IzvorniOblik, ArhiveState)
from datetime import datetime
import requests
import base64
import logging
_logger = logging.getLogger(__name__)


class DocApprovalDocumentPackage(models.Model):
    _inherit = 'ii.edk.document.package'


    ###########    prosirenje za preuzimanje efaktura sa SEF-a
    source = fields.Selection(
        string='Način prijema',
        selection=DocumentSource.list,
        required=True,
        default=DocumentSource.default,
        readonly=False,
        tracking=True,
    )
    doc_move = fields.Selection(
        string='Aktivnost',
        selection=DocumentMove.list,
        required=True,
        default=DocumentMove.default,
        readonly=False,

    )
    sef_status = fields.Selection(
        string='SEFF status',
        selection=DocumentSefStatus.list,
        required=True,
        default=DocumentSefStatus.default,
        readonly=True,
        tracking=True,
    )

    crf_identifikator = fields.Char(
        string='CRF Identifikator',
        translate=True,
        readonly=True,
        tracking=True,
    )
    crf_status = fields.Char(
        string='CRF Status',
        translate=True,
        readonly=True,
        tracking=True,
    )
    efaktura_id = fields.Char(
        string='ID fakture u CRF',
        translate=True,
        readonly=True,
        tracking=True,
    )
    datum_dospeca = fields.Date(
        string='Datum dospeca',
        readonly=True,
        tracking=True,
    )
#############################

############################

    # Libi - auto sequencing polja name


    @api.model
    # def create(self, vals):
    #     _logger.info("PPPPPPPPPPP  vrednosti vals %s", vals)
    #     if vals.get('partner_id') != False:
    #      #   kuf_id_sa_datim_partnerom = self.env['kuf.kccg'].search([('partner', '=', vals.get('partner'))])
    #
    #         kuf_id_sa_datim_brojem_fakture = self.env['ii.edk.document.package'].search([('document_ref', '=', vals.get('document_ref')), ('partner_id', '=', vals.get('partner_id'))])
    #         _logger.info("PPPPPPPPPPP  fakture partnera koja sadrzi isti broj %s", kuf_id_sa_datim_brojem_fakture)
    #         if vals.get('document_ref') != False:
    #             for i in kuf_id_sa_datim_brojem_fakture:
    #                 _logger.info("PPPPPPPPPPP  i.broj_fakture %s", i.document_ref)
    #                 if i.document_ref == vals.get('document_ref'):
    #                     raise UserError(_('Faktura sa brojem  %s za ovog dobavljaca već postoji u sistemu. Nije dozvoljen unos 2 dokumenta istog dobavljača sa istim brojem!') % (i.document_ref),)
    #
    #     bill_id_sa_datim_brojem_fakture = self.env['ii.edk.document.package'].search(
    #         [('document_ref_internal', '=', vals.get('document_ref_internal')), ('partner_id', '=', vals.get('partner_id'))])
    #
    #     if vals.get('document_ref_internal') != False:
    #             for i in bill_id_sa_datim_brojem_fakture:
    #                 _logger.info("PPPPPPPPPPP  i.bill ID %s", i.document_ref_internal)
    #                 if i.document_ref_internal == vals.get('document_ref_internal'):
    #                     raise UserError(_('Faktura sa internim brojem  %s za ovog dobavljaca već postoji u sistemu. Nije dozvoljen unos 2 dokumenta istog dobavljača sa istim brojem!') % (i.document_ref),)
    #     if vals.get('name', 'New') == 'New':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('ii.edk.document.package') or 'New'
    # #    if vals.get('name', 'New') == 'New':
    # #       vals['project_seq'] = self.env['ir.sequence'].next_by_code('ii.edk.document.package') or 'New'
    # # naci tekucu delovodnu knjigu i upisati njen Id
    #         dks = self.env['ii.edk.book'].search([('active', '=', True)])
    #         for dk in dks:
    #             vals['book_id'] = dk.id
    #         # if self.document_type == 'project':
    #         #     p_id=self.env['project.project'].search([('id','=',vals['project_id'])])
    #         #
    #         #     _logger.info("Parametri za upis P = %s   TID=%s", vals['project_id'], vals['document_project_type_id'])
    #         #
    #         #     project_document_number = self._compute_next_package(p_id[0], vals['document_project_type_id'], 1)
    #         #     self.sudo().project_document_number = project_document_number
    #         #     vals['project_document_number'] = project_document_number
    #
    #     result = super(DocApprovalDocumentPackage, self).create(vals)
    #     return result


    def invoice_approve_on_sef(self, approver_notes):

        # api_key_demo = '8ed00700-2e01-448e-950e-8839e7c3c98d'
        # api_url_demo = 'https://demoefaktura.mfin.gov.rs/api/publicApi'

        url = self.company_id.efaktura_api_url + "/"
        apikey = self.company_id.efaktura_api_key

        # url = api_url_demo + "/"  # samo za test potrebe
        # apikey = api_key_demo  # samo za test potrebe

        _logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s headers = %s', url,
                     self.company_id.efaktura_api_key)
        message_headers_json = {
            'Content-Type': 'application/json',
            'ApiKey': apikey,
            'accept': 'application/json'
        }

        data = {
            "invoiceId": self.efaktura_id,
            "accepted": True,
            "comment": "eDK:" + approver_notes
        }
        # invoiceId= self.efaktura_id
        # invoiceId = self.document_ref    # samo za potrebe testa
        # accepted_status="true"
        # comment="Faktura Odobrena"
        command = url + 'purchase-invoice/acceptRejectPurchaseInvoice/'
        response = requests.post(command, headers=message_headers_json, json=data)

        response_object = json.loads(response.text)
        _logger.info('!!!!!!!!! Approve   ---   Ovo je Response object = %', response)

        if response.status_code != 200:
            _logger.info('  ERRRROR pri slanju !!!!! ovako izgleda formirana komanda %s response=%s', command,
                         response.text)

            sefporuka = "** SEF ERR ** Neuspesno ODOBRENJE fakture na server PU! URL = " + command + "\n Kod greske je =" + str(
                response.status_code) + "\n Razlog" + response.text
            self.generate_internal_message(sefporuka)
            return False

        else:    # Dobijen je odgovor od SEFa da je API uspesno poslat, ali  ...
            #    self.x_sent_to_sef = "sent_to_sef"
            if response_object["Success"]:    # API je uspesno izvrsn. Sad treba pitati kakav je status
                if response_object["Invoice"]:
                    sefporuka = "** SEF OK ** faktura usposno ODOBRENA na SEF = " + str(
                        response.status_code) + "\n odgovor" + response_object["Invoice"]
                    self.set_state("approved", vals=None)
                    self.sef_status = "Approved"
                    self.generate_internal_message(sefporuka)
                    return True
                else:
                    sefporuka = "** SEF NOT OK ** Operacija ODOBRAVANJA  na SEF NEUSPESNA " + str(
                        response.status_code) + "\n odgovor" + response_object["Message"]
                    self.generate_internal_message(sefporuka)
                    return False

            else:  # znaci odgovor nije success
                sefporuka = "** SEF NOT OK ** Operacija ODOBRAVANJA  na SEF NEUSPESNA " + str(
                    response.status_code) + "\n odgovor SEF-a: " + response_object["Message"]
                self.generate_internal_message(sefporuka)
                return False

        # x = json2obj(r.content)

        # Ne prihvatanje fakture

    def invoice_reject_on_sef(self, approver_notes):

        url = self.company_id.efaktura_api_url + "/"
        apikey = self.company_id.efaktura_api_key
        #
        _logger.info('************* REJECT  ---------   ---   Ovo je URL koji smo procitali = %s headers = %s', url,
                     self.company_id.efaktura_api_key)
        message_headers_json = {
            'Content-Type': 'application/json',
            'ApiKey': apikey,
            'accept': 'application/json'
        }
        data = {
            "invoiceId": self.efaktura_id,
            "accepted": False,
            "comment": "eDK:" + approver_notes
        }
        command = url + 'purchase-invoice/acceptRejectPurchaseInvoice/'
        response = requests.post(command, headers=message_headers_json, json=data)

        response_object = json.loads(response.text)
        _logger.info('!!!!!!! ODGOVR SEF-a   ---   Ovo je Response  = %s, a ovo response Object =%s', response, response_object)

        if response.status_code != 200:
            _logger.info('  ERRRROR pri slanju !!!!! ovako izgleda formirana komanda %s response=%s', command,
                         response.text)

            sefporuka = "** SEF ERR ** Neuspesno ODBIJANJE fakture na server PU! URL = " + command + "\n Kod greske je =" + str(
                response.status_code) + "\n Razlog" + response.text
            self.generate_internal_message(sefporuka)
            return False
        else:


            if response_object["Success"]:  # API je uspesno izvrsn. Sad treba pitati kakav je status
                if response_object["Invoice"]:
                    sefporuka = "** SEF OK ** faktura usposno ODBIJENA  na SEF = " + str(
                        response.status_code) + "\n odgovor" + response.text
                    self.set_state("approved", vals=None)
                    self.sef_status = "Rejected"
                    self.generate_internal_message(sefporuka)
                    return True
                else:
                    sefporuka = "** SEF NOT OK ** Operacija ODBIJANJA  na SEF NEUSPESNA " + str(
                        response.status_code) + "\n odgovor" + response_object["Message"]
                    self.generate_internal_message(sefporuka)
                    return False
            else:  # znaci odgovor nije success
                sefporuka = "** SEF NOT OK ** Operacija ODBIJANJA  na SEF NEUSPESNA " + str(
                    response.status_code) + "\n odgovor SEF-a: " + response_object["Message"]
                self.generate_internal_message(sefporuka)
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
            'model': 'ii.edk.document.package',
            'res_id': self.id
        })
        return


    # User actions

    # def action_send_for_approval(self):
    #     for record in self:
    #         if record.state == 'draft' and record.approver_ids:
    #             # Subscribe approvers
    #             record.message_subscribe(partner_ids=record.approver_ids.mapped('user_id').mapped('partner_id').ids)
    #         if record.approval_state == 'pending':
    #             raise UserError(_('The document package have already been sent for approval!'))
    #         elif record.approval_state == 'approved':
    #             raise UserError(_('The document package have already been approved!'))
    #         elif record.approval_state == 'rejected':
    #             raise UserError(_('The document package was rejected! To send it for approval again, please update document(s) first.'))
    #         elif record.approval_state == 'to approve':
    #             next_approvers = record.get_next_approvers()
    #             if next_approvers:
    #                 if record.state == 'draft':
    #                     record.state = 'approval'
    #                 next_approvers.write({'state': 'pending'})
    #                 partner_ids = next_approvers.mapped('user_id').mapped('partner_id').ids
    #                 record.send_notification('ii_edk.request_to_approve', partner_ids)
    #             else:
    #                 raise UserError(_('There are not approvers for this document package!'))


    def action_approve_wizard(self):
        self.ensure_one()
        current_approver = self.get_current_approver()
        return current_approver.action_wizard('action_approve_wizard', _('Approve'))

    ##   Dodao Lubi - zavrsna akcija knjizenja
    # def action_post_wizard(self):
    #     _logger.info("$$$$$$$ action post_wizard  vrednosti vals %s", self)
    #     for record in self:
    #         if record.state == 'approved':
    #             if record.document_ref_internal:
    #                 broj_nadjenih_faktura = self.env['ii.edk.document.package'].search_count(
    #                     [('partner_id', '=', record.partner_id.id), ('document_ref_internal','=',record.document_ref_internal)])
    #                 if broj_nadjenih_faktura > 1:
    #                         raise UserError(
    #                         _('Faktura sa internim brojem  %s za ovog dobavljaca već postoji u sistemu. Nije dozvoljen unos 2 dokumenta istog dobavljača sa istim brojem!') % (
    #                             record.document_ref_internal), )
    #
    #                 record.sudo().state = 'posted'
    #                 record.sudo().document_ref_internal = self.document_ref_internal
    #                 if record.source == 'sef':
    #                     ######SEF##################BOBAN za approve
    #                     ### definicije koje se izvlace iz settings!
    #                     #    apikey = '28b4d787-0ed4-414d-97db-8d891fe042cc'    demo APi
    #                     # apikey = '2d1e1218-0b1a-48a9-bbec-ec3e681fefc0'
    #                     #              url = self.company_id.efaktura_api_url
    #                     #              logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s headers = %s', url, self.company_id.efaktura_api_key)
    #                     # url = 'https://efaktura.mfin.gov.rs/api/publicApi/'
    #
    #                     url = self.company_id.efaktura_api_url + "/"
    #                     apikey = self.company_id.efaktura_api_key
    #
    #                     message_headers_json = {
    #                         'Content-Type': 'application/json',
    #                         'ApiKey': apikey,
    #                         'accept': 'application/json'
    #                     }
    #
    #                     #            message_headers = {
    #                     #                'Content-Type': 'application/xml',
    #                     #                'ApiKey': self.company_id.efaktura_api_key,
    #                     #                'accept': 'text/plain'
    #                     #            }
    #
    #                     ####
    #                     command = url + 'purchase-invoice/acceptRejectPurchaseInvoice';
    #                     data = "{'invoiceId': " + str(record.efaktura_id) + ", 'accepted': true, 'comment': '' }"
    #                     ##   data="{'invoiceId': " +record.efaktura_id +", 'accepted': false, 'comment': '' }"   odbijena faktura
    #                     _logger.info("ZZZZZZZZZZZZZZZZ %s", data)
    #                     r = requests.post(command, headers=message_headers_json, data=data)
    #                     ##  Ovde obraditi slucaj da operacija nije uspesna
    #                     _logger.info("ZZZZZZZZZZZZZZZZ %s", r.content)
    #
    # ### Ovde treba verovatno ubaciti podobravanje na SEFF
    #
    #                 record.sudo().document_ref_internal = self.document_ref_internal
    #             else:
    #                 raise UserError(_('Nije dozvoljeno knjiženje dokumenta ako nije unet broj fakture u Odoo'))
    #         else:
    #             raise UserError(_('Nije dozvoljeno knjiženje dokumenta ako predhodno nije odobren'))
    #
    #     #######
    # ###   -----------------
    def action_reject_wizard(self):
        self.ensure_one()
        current_approver = self.get_current_approver()
        return current_approver.action_wizard('action_reject_wizard', _('Reject'))



    def action_cancel(self):
        if not self.env.user._is_admin() and self.filtered(lambda record: record.state == 'approved'):
            raise UserError(_("Cannot cancel a document package that is approved."))
        return self.set_state('cancelled')



    # Built-in methods




# class DocumentInvoceLine(models.Model):
#     _name = 'xf.document.invoice.lines'
#     _description = 'Invoice or fiscal document detail lines'
#
#     @api.onchange("price", "quantity")
#     def _compute_line_total_price(self):
#         """Method to compute total price."""
#         for invoice_line in self:
#             invoice_line.total_price = invoice_line.quantity * invoice_line.price
#
#     invoice_line = fields.Char(string="Optional service or equipment")
#     price = fields.Float(string="Price for option")
#     quantity = fields.Float(string='Qty')
#     vat = fields.Float(string='PDV stopa')
#     total_price = fields.Float(compute="_compute_option_total_price", store=True, string="Total Price")
#     document_package_id = fields.Many2one('ii.edk.document.package', string='Rental options')


