# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
#from odoo.exceptions import ValidationError
#from .selection import ApproverState, ApprovalMethods, ApprovalStep


class DocApprovalDocumentApprover(models.Model):
    _inherit = ['ii.edk.document.participant']

    # User actions
    def action_approve(self):
        for approver in self:
            document_package = approver.document_package_id
            # Najpre idemo da odobrimo fakturu na SEF
            if document_package.invoice_approve_on_sef(approver.notes):
                approver.state = 'approved'
            if document_package.approval_state == 'to approve':
                document_package.sudo().action_send_for_approval()
            elif document_package.approval_state == 'approved':
                document_package.sudo().action_finish_approval()

    def action_reject(self):
        for approver in self:
            document_package = approver.document_package_id
            if document_package.invoice_reject_on_sef(approver.notes):
                approver.state = 'rejected'
                approver.document_package_id.sudo().set_state('rejected', {'reject_reason': approver.notes})

        return
