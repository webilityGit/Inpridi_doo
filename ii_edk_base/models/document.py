from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from .selection import (ApprovalMethods, DocumentState, ApproverState, ApprovalStep, DocumentVisibility,
                        DocumentSource, DocumentMove, SaveFormat, IzvorniOblik, DocumentArchiveState, DocumentGroupType)
from datetime import datetime
import requests
import base64
import logging

_logger = logging.getLogger(__name__)

_editable_states = {
    False: [('readonly', False)],
    'draft': [('readonly', False)],
}


class DocWorkBook(models.Model):
    _name = 'ii.edk.book'
    _inherit = ['mail.thread']
    _description = 'Collection of documents organised as Document Book'

    active = fields.Boolean(default=True)
    name = fields.Char(
        string='Work Book Name',  # Naziv DK'
        required=True,
        translate=True,
    )

    book_year = fields.Char(
        string='Year',
        required=True,
        translate=True,
        default="2023",
    )

    book_seq = fields.Char(
        string='Workbook number',
        copy='False',
        readonly=False,

        default=lambda self: _('New'),
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    document_ids = fields.One2many(
        string='Documents',
        comodel_name='ii.edk.document.package',
        inverse_name='book_id',
        readonly=True,
    )

    # definicija arhivske knjige

    @api.model
    def create(self, vals):
        if vals.get('book_seq', 'New') == 'New':
            vals['book_seq'] = self.env['ir.sequence'].next_by_code('ii.edk.book') or 'New'
        res = super(DocWorkBook, self).create(vals)
        return res


class DocApprovalDocumentPackage(models.Model):
    _name = 'ii.edk.document.package'
    _inherit = ['mail.thread']
    _description = 'Document Package'

    active = fields.Boolean(default=True)
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        readonly=True,
        states=_editable_states,
        tracking=True,
        default=lambda self: _('New'),
    )

    #  project_document_number= fields.Char(string='DB-PROJ')  Lubi TODO dodati u modulu ii_edk_project

    # Lubi dodao nova polja
    book_id = fields.Many2one("ii.edk.book", sring="Workbook")
    document_type = fields.Many2one("ii.edk.document.type", sring="Document Type")
    document_title = fields.Char(
        string='Ducument Title',
        required=False,
        states=_editable_states,
        tracking=True,
    )

    amount_total = fields.Float(
        string='Total amount',
        digits=0,
        readonly=False,
        states=_editable_states,
        tracking=True,
    )
    document_date = fields.Date(
        string='Document date',
        required=True,
        readonly=True,
        default=datetime.now(),
        states=_editable_states,
        tracking=True,
    )
    document_ref = fields.Char(
        string='Ducument reference:',
        required=False,
        readonly=True,
        states=_editable_states,
        tracking=True,
    )

    document_ref_internal = fields.Char(
        string='Inv. or Bill number in Odoo',
        required=False,
        readonly=False,
        states=_editable_states,
        tracking=True,
    )

    partner_id = fields.Many2one("res.partner", string="Partner")
    #   project_id = fields.Many2one("project.project", states=_editable_states, string="Project") Lubi TODO dodati u modulu ii_edk_project
    #   old_project_number = fields.Char(string="Broj iz starog sistema") Lubi TODO dodati u modulu ii_edk_project
    arh_position = fields.Many2one("archive.location", string="Arhivska pozicija")
    classification_number = fields.Many2one("ii.edk.lista.kag", string="Classification ID")
    # Lubi TODO dodati u modulu ii_edk_project
    # document_project_type_id = fields.Selection(
    #     string='Tip proj. dokumenta',
    #     selection=DocumentProjectType.list,
    #     required=False,
    #     default=DocumentProjectType.default,
    #     readonly=False,
    #     tracking=True,
    # )

    ###

    archive_state = fields.Selection(
        string='Archive Status',
        selection=DocumentArchiveState.list,
        required=True,
        default=DocumentArchiveState.default,
        readonly=True,
        tracking=True,

    )
    state = fields.Selection(
        string='Status',
        selection=DocumentState.list,
        required=True,
        default=DocumentState.default,
        readonly=True,
        tracking=True,
    )
    approval_state = fields.Selection(
        string='Approval Status',
        selection=ApproverState.list,
        compute='_compute_approval_state',
    )
    approval_step = fields.Selection(
        string='Approval Step',
        selection=ApprovalStep.list,
        compute='_compute_approval_step',
    )
    method = fields.Selection(
        string='Approval Method',
        selection=ApprovalMethods.list,
        required=True,
        default=ApprovalMethods.default,
        readonly=True,
        states=_editable_states,
    )
    visibility = fields.Selection(
        string='Visibility',
        selection=DocumentVisibility.list,
        required=True,
        default=DocumentVisibility.default,
    )
    workbook_main_user_id = fields.Many2one(
        string='Recorded by',
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        states=_editable_states,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        states=_editable_states,
    )
    approval_participant_id = fields.Many2one(
        string='Approval Team',
        comodel_name='ii.edk.participants',
        readonly=True,
        states=_editable_states,
        #     domain="[('company_id', '=', company_id)]",   Lubi Morao da zakomentarisem jer nece da prodje upgrade
    )
    participant_ids = fields.One2many(
        string='Approvers',
        comodel_name='ii.edk.document.participant',
        inverse_name='document_package_id',
        readonly=True,
        states=_editable_states,
    )
    document_ids = fields.One2many(
        string='Documents',
        comodel_name='ii.edk.document',
        inverse_name='document_package_id',
        readonly=True,
        states=_editable_states,
    )
    invoice_lines_ids = fields.One2many(
        'xf.document.invoice.lines', 'document_package_id', 'Invoice items/Fiscal Bill',
        states=_editable_states,
    )

    ###########    prosirenje za preuzimanje efaktura sa SEF-a
    source = fields.Selection(
        string='Reception/Sent Method',
        selection=DocumentSource.list,
        required=True,
        default=DocumentSource.default,
        readonly=False,
        tracking=True,
    )
    doc_move = fields.Selection(
        string='Move',
        selection=DocumentMove.list,
        required=True,
        default=DocumentMove.default,
        readonly=False,

    )

    datum_dospeca = fields.Date(
        string='Due Date',
        required=True,
        readonly=True,
        default=datetime.now(),
        states=_editable_states,
        tracking=True,
    )
    #############################
    # Grupa metapodataka elektronskog dokumenta prema uredbi RS o elektronskom arhiviranju
    broj_predmeta = fields.Many2one("ii.edk.lista.predmeta", string='Case number')
    kategorija_dokumenta = fields.Many2one("ii.edk.lista.kag", string="Document classification")
    #  vrsta_dokumenta =
    description = fields.Text(  # opis dokumenta
        string='Description',
        translate=True,
    )
    izvorni_oblik = fields.Selection(
        string='Source format',  # Izvorni format
        selection=IzvorniOblik.list,
        required=True,
        states=_editable_states,
        default=IzvorniOblik.default,
        tracking=True,
    )
    arh_format = fields.Selection(
        string='Storage format',  # Format ;uvanja dokumenta
        selection=SaveFormat.list,
        required=True,
        states=_editable_states,
        default=SaveFormat.default,
        tracking=True,
    )
    datum_nastanka = fields.Date(
        string='Signature date and/or stamp',  # Datum potpisivanja i/ili pečatiranja
        required=True,
        readonly=True,
        default=datetime.now(),
        states=_editable_states,
        tracking=True,
    )
    broj_sertifikata = fields.Char(
        string='Qualified certificate',  # Broj kvalifikovanog el. sertifikata
        readonly=True,
        states=_editable_states,
        tracking=True,
    )
    rok_cuvanja = fields.Integer(  # Rok cuvanja
        string='Storage period',
        readonly=True,
        states=_editable_states,
        tracking=True,
    )

    datum_arhiviranja = fields.Date(  # datum arhiviranja
        string='Date of Archiving',
        readonly=True,

        states=_editable_states,
        tracking=True,
    )
    datum_potvrde_integriteta = fields.Date(
        string='Date of integrity confirmation',  # datum potvrdjivanja integriteta
        readonly=True,

        states=_editable_states,
        tracking=True,
    )
    rok_za_obnovu = fields.Date(  # rok za obnovu integriteta dokumenta
        string='The deadline for renewing the integrity of the certificate',
        readonly=True,

        states=_editable_states,
        tracking=True,
    )

    ############################

    is_initiator = fields.Boolean('Is Initiator', compute='_compute_access')
    is_approver = fields.Boolean('Is Approver', compute='_compute_access')
    reject_reason = fields.Text('Reject Reason')

    #   x_doc_package_count = fields.Integer("Projet Document Package Counter", default = 0) Lubi TODO dodati u modulu ii_edk_project

    # Libi - auto sequencing polja name
    # Lubi TODO dodati u modulu ii_edk_project
    # def _compute_next_package(self, project_id, document_project_type_id, mod):
    # # Mod  0 - edituj zavodni broj bez povecanja sekvence  - koristiti kod promene  tipa dokumenta
    # # Mod  1 - dodaje se novi dikumenat uz neki projekat. sekvenca se povecava za 1
    #     _logger.info("Usao u kreiranje sekvence Mod = %s", mod)
    #     if mod == 1:
    #         next_id = project_id.x_doc_package_count + 1
    #     else:
    #         next_id = project_id.x_doc_package_count
    #     sequence_id = self.env['ir.sequence'].search([('code','=','xf.doc.project.package')])
    #     prefix = sequence_id[0].prefix
    #     if prefix:
    #         project_pack_sequence = prefix + "{:05d}".format(project_id.id) + "/" + str(document_project_type_id) + "/" + str(next_id)
    #     else:
    #         project_pack_sequence = "{:05d}".format(project_id.id) + "/" + str(document_project_type_id) + "/" + str(next_id)
    #     project_id.x_doc_package_count = next_id
    #     _logger.info("sekvenca za project _doc= %s", project_pack_sequence)
    #     return project_pack_sequence

    @api.onchange('classification_number')
    def classificatin_id(self):
        klase_dokumenata = self.env["ii.edk.lista.kag"].sudo().search([('name', '=', self.classification_number.name)])
        for klasa in klase_dokumenata:
            self.arh_position = klasa.default_arh_pozicija
            self.rok_cuvanja = klasa.rok_cuvanja_meseci

    @api.onchange('document_type')
    def classificatin_id(self):
        config_pravila = self.env["ii.edk.config"].sudo().search([('docType', '=', self.document_type.name)])
        if config_pravila:
            for config_pravilo in config_pravila:
                if self.doc_move == 'in':
                    self.classification_number = config_pravilo.classificationID_U
                if self.doc_move == 'out':
                    self.classification_number = config_pravilo.classificationID_I

    @api.model
    def create(self, vals):
        _logger.info("PPPPPPPPPPP  vrednosti vals %s", vals)
        if vals.get('partner_id') != False:

            kuf_id_sa_datim_brojem_fakture = self.env['ii.edk.document.package'].search(
                [('document_ref', '=', vals.get('document_ref')), ('partner_id', '=', vals.get('partner_id'))])
            _logger.info("PPPPPPPPPPP  fakture partnera koja sadrzi isti broj %s", kuf_id_sa_datim_brojem_fakture)
            if vals.get('document_ref') != False:
                for i in kuf_id_sa_datim_brojem_fakture:
                    _logger.info("PPPPPPPPPPP  i.broj_fakture %s", i.document_ref)
                    if i.document_ref == vals.get('document_ref'):
                        raise UserError(
                            _('Faktura sa brojem  %s za ovog dobavljaca već postoji u sistemu. Nije dozvoljen unos 2 dokumenta istog dobavljača sa istim brojem!') % (
                                i.document_ref), )

        bill_id_sa_datim_brojem_fakture = self.env['ii.edk.document.package'].search(
            [('document_ref_internal', '=', vals.get('document_ref_internal')),
             ('partner_id', '=', vals.get('partner_id'))])

        if vals.get('document_ref_internal') != False:
            for i in bill_id_sa_datim_brojem_fakture:
                _logger.info("PPPPPPPPPPP  i.bill ID %s", i.document_ref_internal)
                if i.document_ref_internal == vals.get('document_ref_internal'):
                    raise UserError(
                        _('Faktura sa internim brojem  %s za ovog dobavljaca već postoji u sistemu. Nije dozvoljen unos 2 dokumenta istog dobavljača sa istim brojem!') % (
                            i.document_ref), )
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ii.edk.document.package') or 'New'
            #    if vals.get('name', 'New') == 'New':
            #       vals['project_seq'] = self.env['ir.sequence'].next_by_code('ii.edk.document.package') or 'New'
            # naci tekucu delovodnu knjigu i upisati njen Id
            dks = self.env['ii.edk.book'].search([('active', '=', True)])
            for dk in dks:
                vals['book_id'] = dk.id
        # Lubi ToDO videti sta sa ovim
        #    if self.document_type == 'project':
        #        p_id=self.env['project.project'].search([('id','=',vals['project_id'])])

        #        _logger.info("Parametri za upis P = %s   TID=%s", vals['project_id'], vals['document_project_type_id'])
        # Lubi TODO dodati u modulu ii_edk_project
        #        project_document_number = self._compute_next_package(p_id[0], vals['document_project_type_id'], 1)
        #        self.sudo().project_document_number = project_document_number
        #        vals['project_document_number'] = project_document_number

        result = super(DocApprovalDocumentPackage, self).create(vals)
        return result

    # @api.model
    # def write(self, vals):
    #     # Check if name is set to default value
    #     if 'name' in vals and vals.get('name', _('New')) == _('New'):
    #         # Generate name from sequence
    #         vals['name'] = self.env['ir.sequence'].next_by_code('ii.edk.document.package')

    # Call parent write method

    # Compute fields
    # Lubi TODO dodati u modulu ii_edk_project
    # @api.onchange('document_project_type_id')
    # def _compute_db_document_project_type_id(self):
    #     for record in self:
    #         project_document_number = self._compute_next_package(record.project_id, record.document_project_type_id, 0)
    #         self.sudo().project_document_number = project_document_number

    # Lubi TODO dodati u modulu ii_edk_project
    #     @api.onchange('project_id')
    #     def _compute_db_project_id(self):
    #     #    _logger.info("self = %s, self_context = %s, origin = %s", self, self._context, self._origin)
    #     #    _logger.info("$$$$$$$  Usao u Change Project document ID = %s, ID dokumenta", self.project_document_number, self.id)
    #     #    _logger.info("$$$$$$$  Usao u Change  NEW Project ID = %s", self.project_id)
    #         # Sada treba naci old project_id
    #         new_project_id = self.project_id
    #         _logger.info("$$$$$$$ New Project ID = %s, broj=%s", new_project_id.name,new_project_id.x_doc_package_count)
    #         old_project_id = self._origin.project_id
    #
    #         self.partner_id = self.project_id.partner_id  # ako projekat ima dodeljenog kupca preuzima se u formi dokumenta
    #
    #         _logger.info("$$$$$$$ PARTNER ID = %s", self.partner_id)
    #         if old_project_id:
    #             _logger.info("$$$$$$$ OLD Project ID = %s", old_project_id.name, old_project_id.x_doc_package_count)
    #             old_project_id.write({'x_doc_package_count': old_project_id.x_doc_package_count - 1})
    #
    #             for record in self:
    #                 att_files_names=[]
    #                 record.partner_id = new_project_id.partner_id     # ako projekat ima dodeljenog kupca preuzima se u formi dokumenta
    #
    #                 for att_file_name in self.document_ids:
    #                     att_files_names.append(att_file_name.name)
    #                 _logger.info("#### Spisak atachovanih fajlova = %s izuceni iz %s", att_files_names, self.document_ids)
    #                 project_documents = self.env["ir.attachment"].search([('res_id','=', old_project_id.id), ('res_model','=', 'project.project')])
    #                 for project_document in project_documents:
    #                     _logger.info("#### Spisak fajlova iz projekta = %s", project_document.name)
    #                     if project_document.name in att_files_names:
    #                         project_document.res_name = self.project_id
    #                         project_document.res_id = self.project_id.id
    # #
    #                 if self._origin.project_document_number != "new":
    #                     project_document_number = self._compute_next_package(record.project_id, record.document_project_type_id, 1)
    #                     self.sudo().project_document_number = project_document_number
    #                 project_user = self.env["ir.attachment"].search(
    #                     [('res_id', '=', old_project_id.id), ('res_model', '=', 'project.project')])
    #         else:
    #             _logger.info("NE Postoji OLD Project ID = !!!!!!!")

    # Lubi TODO dodati u modulu ii_edk_project
    # @api.onchange('document_type')
    # def _compute_db_document_type(self):
    #
    #     old_project_document_number = self.project_document_number
    #     _logger.info("$$$$$$$ context - project %s", self.project_document_number)
    #     _logger.info("$$$$$$$ _context %s", self._context)
    #
    #     if self.document_type == "project":  # vazi samo ako je tip tokumenta projekat
    #
    #         if self.name == "New": # U pitanju je kreianje novogovog Paketa dokumenata
    #             if self.project_id:
    #                 project_document_number = self._compute_next_package(self.project_id)
    #                 self.sudo().project_document_number = project_document_number
    #             else:
    #                 self.project_document_number = "new"

    @api.depends('state', 'approval_participant_id')
    def _compute_access(self):
        for record in self:
            # Check if the current user is initiator (true for admin)
            record.is_initiator = self.env.user == record.workbook_main_user_id or self.env.user._is_admin()

            # Check if the document needs approval from current user (true for admin)
            current_approvers = record.get_current_approvers()
            responsible = self.env.user in current_approvers.mapped('user_id') or self.env.user._is_admin()
            record.is_approver = record.approval_state == 'pending' and responsible

    @api.depends('participant_ids.state')
    def _compute_approval_state(self):
        for record in self:
            approvers = record.participant_ids
            if len(approvers) == len(approvers.filtered(lambda a: a.state == 'approved')):
                record.approval_state = 'approved'
                # Ovo je mesto gde treba da se sinhroniziuje sa seffom potvrda da je faktura odobrena
                # curl - X
                # POST
                # "https://efaktura.mfin.gov.rs/api/publicApi/purchaseinvoice/acceptRejectPurchaseInvoice" - H
                # "accept: text/plain" - H
                # "ApiKey: 462d9282-22cf-4d0bafbe-17411d375a18" - H
                # "Content-Type: application/json" - d
                # "{\"invoiceId\":3730,\"accepted\":true,\"comment\":\"Accept test\"}"

                # if sef_sinhro:
                self.approve_invoice_on_safe()

            elif approvers.filtered(lambda a: a.state == 'rejected'):
                record.approval_state = 'rejected'
            elif approvers.filtered(lambda a: a.state == 'pending'):
                record.approval_state = 'pending'
            else:
                record.approval_state = 'to approve'

    @api.depends('participant_ids.state', 'participant_ids.step')
    def _compute_approval_step(self):
        for record in self:
            approval_step = None
            steps = record.participant_ids.mapped('step')
            steps.sort()
            for step in steps:
                if record.participant_ids.filtered(lambda a: a.step == step and a.state != 'approved'):
                    approval_step = step
                    break
            record.approval_step = approval_step

    # Onchange handlers

    @api.onchange('approval_participant_id')
    def onchange_approval_team(self):
        if self.approval_participant_id:

            team_approvers = []
            for team_approver in self.approval_participant_id.participant_ids:
                team_approvers += [{
                    'step': team_approver.step,
                    'user_id': team_approver.user_id.id,
                    'role': team_approver.role,
                }]
            approvers = self.participant_ids.browse([])
            for a in team_approvers:
                approvers += approvers.new(a)
            self.participant_ids = approvers

    @api.onchange('participant_ids')
    def onchange_approvers(self):
        if self.approval_participant_id:
            if self.approval_participant_id.participant_ids.mapped('user_id') != self.participant_ids.mapped('user_id'):
                self.approval_participant_id = None

    # Validation

    @api.constrains('company_id')
    def _validate_company(self):
        for record in self:
            record.participant_ids.validate_company(record.company_id)

    @api.constrains('state', 'participant_ids')
    def _check_approvers(self):
        for record in self:
            if record.state == 'approval' and not record.participant_ids:
                raise ValidationError(_('Please add at least one approver!'))

    @api.constrains('state', 'document_ids')
    def _check_documents(self):
        for record in self:
            if record.state == 'approval' and not record.document_ids:
                raise ValidationError(_('Please add at least one document!'))

    # Helpers
    def set_state(self, state, vals=None):
        if vals is None:
            vals = {}
        vals.update({'state': state})
        return self.write(vals)

    def get_next_approvers(self):
        self.ensure_one()
        next_approvers = self.participant_ids.filtered(lambda a: a.state == 'to approve').sorted('step')
        if not next_approvers:
            return next_approvers
        next_step = next_approvers[0].step
        return next_approvers.filtered(lambda a: a.step == next_step)

    def get_current_approvers(self):
        self.ensure_one()
        return self.participant_ids.filtered(lambda a: a.state == 'pending' and a.step == self.approval_step)

    def get_current_approver(self):
        self.ensure_one()
        current_approvers = self.get_current_approvers()
        if not current_approvers:
            raise UserError(_('There are not approvers for this document package!'))

        current_approver = current_approvers.filtered(lambda a: a.user_id == self.env.user)
        if not current_approver and self.env.user._is_admin():
            current_approver = current_approvers[0]
        if not current_approver:
            raise AccessError(_('You are not allowed to approve this document package!'))
        return current_approver

    def send_notification(self, view_ref, partner_ids):
        for record in self:
            record.message_post_with_view(
                view_ref,
                subject=_('Document Approval: %s') % record.name,
                composition_mode='mass_mail',
                partner_ids=[(6, 0, partner_ids)],
                auto_delete=False,
                auto_delete_message=False,
                parent_id=False,
                subtype_id=self.env.ref('mail.mt_note').id)

    # User actions

    def action_send_for_approval(self):
        for record in self:
            if record.state == 'draft' and record.participant_ids:
                # Subscribe approvers
                record.message_subscribe(partner_ids=record.participant_ids.mapped('user_id').mapped('partner_id').ids)
            if record.approval_state == 'pending':
                raise UserError(_('The document package have already been sent for approval!'))
            elif record.approval_state == 'approved':
                raise UserError(_('The document package have already been approved!'))
            elif record.approval_state == 'rejected':
                raise UserError(
                    _('The document package was rejected! To send it for approval again, please update document(s) first.'))
            elif record.approval_state == 'to approve':
                next_approvers = record.get_next_approvers()
                if next_approvers:
                    if record.state == 'draft':
                        record.state = 'approval'
                    next_approvers.write({'state': 'pending'})
                    partner_ids = next_approvers.mapped('user_id').mapped('partner_id').ids
                    record.send_notification('ii_edk.request_to_approve', partner_ids)
                else:
                    raise UserError(_('There are not approvers for this document package!'))

    def action_approve_wizard(self):
        self.ensure_one()
        current_approver = self.get_current_approver()
        return current_approver.action_wizard('action_approve_wizard', _('Approve'))

    ##   Dodao Lubi - zavrsna akcija knjizenja

    def action_post_wizard(self):
        _logger.info("$$$$$$$ action post_wizard  vrednosti vals %s", self)
        for record in self:
            if record.state == 'approved':
                if record.document_ref_internal:
                    broj_nadjenih_faktura = self.env['ii.edk.document.package'].search_count(
                        [('partner_id', '=', record.partner_id.id),
                         ('document_ref_internal', '=', record.document_ref_internal)])
                    if broj_nadjenih_faktura > 1:
                        raise UserError(
                            _('Faktura sa internim brojem  %s za ovog dobavljaca već postoji u sistemu. Nije dozvoljen unos 2 dokumenta istog dobavljača sa istim brojem!') % (
                                record.document_ref_internal), )

                    record.sudo().state = 'posted'
                    record.sudo().document_ref_internal = self.document_ref_internal
                    if record.source == 'sef':
                        ######SEF##################BOBAN za approve
                        ### definicije koje se izvlace iz settings!
                        #    apikey = '28b4d787-0ed4-414d-97db-8d891fe042cc'    demo APi
                        # apikey = '2d1e1218-0b1a-48a9-bbec-ec3e681fefc0'
                        #              url = self.company_id.efaktura_api_url
                        #              logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s headers = %s', url, self.company_id.efaktura_api_key)
                        # url = 'https://efaktura.mfin.gov.rs/api/publicApi/'

                        url = self.company_id.efaktura_api_url + "/"
                        apikey = self.company_id.efaktura_api_key

                        message_headers_json = {
                            'Content-Type': 'application/json',
                            'ApiKey': apikey,
                            'accept': 'application/json'
                        }

                        #            message_headers = {
                        #                'Content-Type': 'application/xml',
                        #                'ApiKey': self.company_id.efaktura_api_key,
                        #                'accept': 'text/plain'
                        #            }

                        ####
                        command = url + 'purchase-invoice/acceptRejectPurchaseInvoice';
                        data = "{'invoiceId': " + str(record.efaktura_id) + ", 'accepted': true, 'comment': '' }"
                        ##   data="{'invoiceId': " +record.efaktura_id +", 'accepted': false, 'comment': '' }"   odbijena faktura
                        _logger.info("ZZZZZZZZZZZZZZZZ %s", data)
                        r = requests.post(command, headers=message_headers_json, data=data)
                        ##  Ovde obraditi slucaj da operacija nije uspesna
                        _logger.info("ZZZZZZZZZZZZZZZZ %s", r.content)

                    ### Ovde treba verovatno ubaciti podobravanje na SEFF

                    record.sudo().document_ref_internal = self.document_ref_internal
                else:
                    raise UserError(_('Document posting is not allowed if the invoice number is not entered in Odoo'))
            else:
                raise UserError(_('It is not allowed to register a document if it has not been previously approved'))

        #######

    ###   -----------------
    def action_reject_wizard(self):
        self.ensure_one()
        current_approver = self.get_current_approver()
        return current_approver.action_wizard('action_reject_wizard', _('Reject'))

    def action_draft(self):
        for record in self:
            record.participant_ids.write({'state': 'to approve', 'notes': None})
            record.write({'state': 'draft', 'reject_reason': None})
        return True

    def action_cancel(self):
        if not self.env.user._is_admin() and self.filtered(lambda record: record.state == 'approved'):
            raise UserError(_("Cannot cancel a document package that is approved."))
        return self.set_state('cancelled')

    def action_finish_approval(self):
        for record in self:
            if record.approval_state == 'approved':
                record.state = 'approved'

            else:
                raise UserError(_('Document Package must be fully approved!'))

    # Built-in methods

    def unlink(self):
        if any(self.filtered(lambda record: record.state not in ('draft', 'cancelled'))):
            raise UserError(_('You cannot delete a record which is not draft or cancelled!'))
        return super(DocApprovalDocumentPackage, self).unlink()

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'approval':
            return self.env.ref('ii_edk_base.mt_document_package_approval')
        elif 'state' in init_values and self.state == 'approved':
            return self.env.ref('ii_edk_base.mt_document_package_approved')
        elif 'state' in init_values and self.state == 'cancelled':
            return self.env.ref('ii_edk_base.mt_document_package_cancelled')
        elif 'state' in init_values and self.state == 'rejected':
            return self.env.ref('ii_edk_base.mt_document_package_rejected')

        return super(DocApprovalDocumentPackage, self)._track_subtype(init_values)

    # sinhronizacija sa sefom
    def approve_invoice_on_safe(self):

        # "https://efaktura.mfin.gov.rs/api/publicApi/purchaseinvoice/acceptRejectPurchaseInvoice" - H
        # "accept: text/plain" - H
        # "ApiKey: 462d9282-22cf-4d0bafbe-17411d375a18" - H
        # "Content-Type: application/json" - d
        # "{\"invoiceId\":3730,\"accepted\":true,\"comment\":\"Accept test\"}"

        api_key_demo = '8ed00700-2e01-448e-950e-8839e7c3c98d'
        api_url_demo = 'https://demoefaktura.mfin.gov.rs/api/publicApi'

        # url = self.company_id.efaktura_api_url + "/"
        # apikey = self.company_id.efaktura_api_key

        url = api_url_demo + "/"  # samo za demo potrebe
        apikey = api_key_demo  # samo za demo potrebe

        _logger.info('!!!!!!!!!   ---   Ovo je URL koji smo procitali = %s headers = %s', url,
                     self.company_id.efaktura_api_key)
        message_headers_json = {
            'Content-Type': 'application/json',
            'ApiKey': apikey,
            'accept': 'application/json'
        }
        data = {
            "invoiceId": 2505983,
            "accepted": True,
            "comment": "string"
        }
        # invoiceId= self.efaktura_id
        # invoiceId = self.document_ref    # samo za potrebe testa
        # accepted_status="true"
        # comment="Faktura Odobrena"
        command = url + 'purchase-invoice/acceptRejectPurchaseInvoice/'
        response = requests.post(command, headers=message_headers_json, json=data)
        if response.status_code != 200:
            _logger.info('  ERRRROR pri slanju !!!!! ovako izgleda formirana komanda %s response=%s', command,
                         response.text)
            # self.x_sent_to_sef = "err_sent_to_sef"
            # sefporuka = ("Neuspesno slanje fakture na server PU! URL = %s \n Kod greske je = %s \n  razlog = %s")
            #                % ( url, response.status_code , response.text))
            sefporuka = "** SEF ERR ** Neuspesno ODOBRENJE fakture na server PU! URL = " + command + "\n Kod greske je =" + str(
                response.status_code) + "\n Razlog" + response.text
            self.generate_internal_message(sefporuka)

        else:
            #    self.x_sent_to_sef = "sent_to_sef"
            sefporuka = "** SEF OK ** faktura usposno ODOBRENA na SEF = " + str(
                response.status_code) + "\n odgovor" + response.text
            self.generate_internal_message(sefporuka)

        #    print(response)
        # x = json2obj(r.content)
        # _logger.info("80-ZZZZZZZZZZZZZZa za datum %s = %s", za_datum, r.content)

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


class DocApprovalDocument(models.Model):
    _name = 'ii.edk.document'
    _description = 'Document'

    document_package_id = fields.Many2one(
        string='Document Package',
        comodel_name='ii.edk.document.package',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    file = fields.Binary(
        string='File',
        required=True,
        attachment=True,
    )
    file_name = fields.Char(
        string='File Name'
    )

    @api.onchange('file_name')
    def _onchange_file_name(self):
        if self.file_name and not self.name:
            self.name = self.file_name

    @api.model
    def create(self, vals):
        _logger.info("FFFFFFFFF  IDE create attachmenta %s", vals)
        # A sada attachovati fajl za odgovarajuci projekat ako je u pitanju projektna dokumentacija
        _logger.info("FFFFFFFFF  nasao ID =  %s", vals['document_package_id'])
        p_ids = self.env['ii.edk.document.package'].search([('id', '=', vals['document_package_id'])])
        _logger.info("FFFFFFFFF  nasao packages %s", p_ids)
        if p_ids:
            p_id = p_ids[0]
            _logger.info("FFFFFFFFF  nasao package PRVI %s", p_id.document_type)
            # lubi TODO vezano za project
            # if p_id.document_type == "project":
            #     attachment = {'name': vals['name'],
            #               'type': 'binary',
            #               'datas': vals['file'],
            #               'res_model': 'project.project',
            #               'res_id': p_id.project_id.id}
            #     self.env['ir.attachment'].create(attachment)
        res = super(DocApprovalDocument, self).create(vals)
        return res

    def write(self, vals):
        _logger.info("FFFFFFFFF IDE write  vals= %s", vals)
        # ako se menja ime
        if 'name' in vals:
            _logger.info("FFFFFFFFF  treba promeniti ime attachmentu  %s ----> %s", self.name, vals['name'])
        if 'file' in vals:
            _logger.info("FFFFFFFFF  treba promeniti sadrzaj attachmentu  %s ----> %s", self.name, vals['name'])
        res = super(DocApprovalDocument, self).write(vals)
        return res


class DocumentInvoceLine(models.Model):
    _name = 'xf.document.invoice.lines'
    _description = 'Invoice or fiscal document detail lines'

    @api.onchange("price", "quantity")
    def _compute_line_total_price(self):
        """Method to compute total price."""
        for invoice_line in self:
            invoice_line.total_price = invoice_line.quantity * invoice_line.price

    invoice_line = fields.Char(string="Optional service or equipment")
    price = fields.Float(string="Price for option")
    quantity = fields.Float(string='Qty')
    vat = fields.Float(string='VAT')
    total_price = fields.Float(compute="_compute_option_total_price", store=True, string="Total Price")
    document_package_id = fields.Many2one('ii.edk.document.package', string='Rental options')

# Lubi TODO klasa koju treba dodati u modulu ii_edk_project
# class ProjectDocumentDocumentCount(models.Model):
#     _inherit = "project.project"
#     _description = "Project package document counter"
#     # ovo polje se koristi kao brojac za formiranje delovodnog broja projektne dokumentacije
#     x_doc_package_count = fields.Integer("Projet Document Package Counter")

