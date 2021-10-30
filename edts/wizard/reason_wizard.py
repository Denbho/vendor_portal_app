from odoo import fields, models, api
from datetime import datetime


class EDTSReasonWizard(models.TransientModel):
    _name = 'edts.reason.wizard'
    _description = 'EDTS Reason Wizard'

    account_move_id = fields.Many2one('account.move', string='Account Move')
    rejection_id = fields.Many2one('reject.reason', string='Rejection Reason')
    return_id = fields.Many2one('return.reason', string='Return Reason')
    extension_reason_id = fields.Many2one('extension.reason', string='Extension Reason')
    wizard_remarks = fields.Text(string='Wizard Remarks')
    is_remarks_required = fields.Boolean(string='Is Remarks Required', default=False, store=False)

    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')

    @api.onchange('return_id', 'rejection_id', 'extension_reason_id')
    def onchange_edts_check_extension_reason(self):
        for record in self:
            record.is_remarks_required = False

            if record.return_id:
                if record.return_id.name.lower() in ['others']:
                    record.is_remarks_required = True

            if record.rejection_id:
                if record.rejection_id.name.lower() in ['others']:
                    record.is_remarks_required = True

            if record.extension_reason_id:
                if record.extension_reason_id.name.lower() in ['others']:
                    record.is_remarks_required = True

    def reject_action_proceed(self):
        formatted_remarks = (' - ' + self.wizard_remarks) if self.wizard_remarks else ''
        wizard_reason = self.rejection_id.name + formatted_remarks

        self.account_move_id.wizard_reason = wizard_reason
        self.account_move_id.send_edts_reject_email()
        self.account_move_id.set_reject_status()
        return {'type': 'ir.actions.act_window_close'}

    def return_action_proceed(self):
        formatted_remarks = (' - ' + self.wizard_remarks) if self.wizard_remarks else ''
        wizard_reason = self.return_id.name + formatted_remarks

        self.account_move_id.wizard_reason = wizard_reason
        self.account_move_id.send_edts_return_email()
        self.account_move_id.set_draft_status()
        self.account_move_id.returned_or_recalled = True
        return {'type': 'ir.actions.act_window_close'}

    def extend_action_proceed(self):
        self.account_move_id.valid_to = self.valid_to
        vals = {
            'account_move_id': self.account_move_id.id,
            'transaction_extended_date': datetime.now(),
            'transaction_extended_by': self._uid,
            'extension_reason_id': self.extension_reason_id.id,
            'extension_remarks': self.wizard_remarks,
        }
        self.account_move_id.extension_reference_ids.create(vals)
        self.account_move_id.send_extended_notification_email()
        return {'type': 'ir.actions.act_window_close'}
