# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .selection import ApproverState, ApprovalMethods, ApprovalStep


class eDKParticipants(models.Model):
    _name = 'ii.edk.participants'
    _description = 'Electronic workbook participants'

    active = fields.Boolean('Active', default=True)

    name = fields.Char(
        string='Name',
        required=True,
    )
    user_id = fields.Many2one(
        string='Participants Leader',
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user,
        index=True
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company.id,
        index=True,
    )
    participant_ids = fields.One2many(
        string='Participants',
        comodel_name='ii.edk.participants.approver',
        inverse_name='participant_id',
    )
    pratioci_ids = fields.One2many(
        string='Followers',
        comodel_name='ii.edk.participants.pratilac',
        inverse_name='participant_id',
    )

    # Validation

    @api.constrains('company_id')
    def _check_team_company(self):
        for team in self:
            team.participant_ids.validate_company(team.company_id)

###   Dodao lubi novu abstractnu klasu
class eDKParticipantAbstract(models.Model):
    _name = 'ii.edk.participant.abstract'
    _description = 'Abstract Participant'
    _order = 'step'
    _rec_name = 'user_id'
    step = fields.Selection(
        string='Step',
        selection=ApprovalStep.list,
        required=True,
        default=ApprovalStep.default,
    )
    user_id = fields.Many2one(
        string='Participant',
        comodel_name='res.users',
        required=True
    )
    role = fields.Char(
        string='Role/Position',
        required=True,
        default="Participant"
    )

    # Onchange handlers

    @api.onchange('user_id')
    def _detect_user_role(self):
        for approver in self:
            # if user related to employee, try to get job title for hr.employee
            employee = hasattr(approver.user_id, 'employee_ids') and getattr(approver.user_id, 'employee_ids')
            employee_job_id = hasattr(employee, 'job_id') and getattr(employee, 'job_id')
            employee_job_title = employee_job_id.name if employee_job_id else False
            if employee_job_title:
                approver.role = employee_job_title
                continue
            # if user related partner, try to get job title for res.partner
            partner = approver.user_id.partner_id
            partner_job_title = hasattr(partner, 'function') and getattr(partner, 'function')
            if partner_job_title:
                approver.role = partner_job_title

    # Validation

    @api.constrains('user_id')
    def _check_users(self):
        for approver in self:
            if not approver.user_id.has_group('ii_edk_base.group_ii_edk_user'):
                raise ValidationError(_('%s does not have access to the Doc Approval module.') % (approver.user_id.name,)
                                      + '\n' +
                                      _('Please ask system administrator to add him/her to the Doc Approval module group first.'))

    def validate_company(self, company):
        if not company:
            return
        for approver in self:
            if company not in approver.user_id.company_ids:
                raise ValidationError(
                    _('%s does not have access to the company %s') % (approver.user_id.name, company.name))


class eDKPTeamApprover(models.Model):
    _name = 'ii.edk.participants.approver'
    _inherit = ['ii.edk.participant.abstract']
    _description = 'Approval Team Member'

    participant_id = fields.Many2one(
        string='Team',
        comodel_name='ii.edk.participants',
        required=True,
        ondelete='cascade'
    )

    # Validation

    @api.constrains('user_id', 'participant_id')
    def _check_users(self):
        for approver in self:
            approver.validate_company(approver.participant_id.company_id)
        return super(eDKPTeamApprover, self)._check_users()

###   Dodao lubi
class eDKTeamPratilac(models.Model):
    _name = 'ii.edk.participants.pratilac'
    _inherit = ['ii.edk.participant.abstract']
    _description = 'Pratilac dokumenata odredjenog Tima'

    participant_id = fields.Many2one(
        string='Team',
        comodel_name='ii.edk.participants',
        required=True,
        ondelete='cascade'
    )

    # Validation

    @api.constrains('user_id', 'participant_id')
    def _check_users(self):
        for approver in self:
            approver.validate_company(approver.participant_id.company_id)
        return super(eDKTeamPratilac, self)._check_users()



class eDKDocumentApprover(models.Model):
    _name = 'ii.edk.document.participant'
    _inherit = ['ii.edk.participant.abstract']
    _description = 'Document Participant'

    team_approver_id = fields.Many2one(
        string='Doc Team Approver',
        comodel_name='ii.edk.participants.approver',
        ondelete='set null'
    )
    document_package_id = fields.Many2one(
        string='Document Package',
        comodel_name='ii.edk.document.package',
        required=True,
        ondelete='cascade',
    )
    method = fields.Selection(
        string='Method',
        selection=ApprovalMethods.list,
        related='document_package_id.method',
        readonly=True,
    )
    state = fields.Selection(
        string='Status',
        selection=ApproverState.list,
        readonly=True,
        required=True,
        default=ApproverState.default
    )
    notes = fields.Text(
        string='Notes',
        readonly=True,
    )

    # Validation

    @api.constrains('user_id', 'document_package_id')
    def _check_users(self):
        for approver in self:
            approver.validate_company(approver.document_package_id.company_id)
        return super(eDKDocumentApprover, self)._check_users()

    # User actions

    def action_wizard(self, view_ref, window_title):
        self.ensure_one()
        view = self.env.ref('ii_edk_base.' + view_ref)
        return {
            'name': window_title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new'
        }

    def action_approve(self):
        for approver in self:
            document_package = approver.document_package_id
            approver.state = 'approved'
            if document_package.approval_state == 'to approve':
                document_package.sudo().action_send_for_approval()
            elif document_package.approval_state == 'approved':
                document_package.sudo().action_finish_approval()



    def action_reject(self):
        for approver in self:
            approver.state = 'rejected'
            approver.document_package_id.sudo().set_state('rejected', {'reject_reason': approver.notes})
