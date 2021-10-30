from odoo import fields, models, api
from datetime import datetime


class EDTSSignatureWizard(models.TransientModel):
    _name = 'edts.signature.wizard'
    _description = 'EDTS Signature Wizard'

    account_move_id = fields.Many2one('account.move', string='Account Move')
    liquidation_reference_id = fields.Many2one('edts.liquidation.reference', string='EDTS Liquidation Reference')
    action = fields.Selection([
        ('approve', 'Approve'),
        ('validate', 'Validate'),
    ], string='Action', default=False)
    dept_head_signature = fields.Binary(string="Department Head's Signature")
    accounting_signature = fields.Binary(string="Accounting Department's Signature")

    def signature_action_proceed(self):
        if self.account_move_id:
            if self.action in ['approve']:
                self.account_move_id.dept_head_signature = self.dept_head_signature
                self.account_move_id.set_waiting_for_accounting_status()
                self.account_move_id.send_edts_for_validation_acctg_email()
            elif self.action in ['validate']:
                self.account_move_id.accounting_signature = self.accounting_signature
                if self.account_move_id.edts_subtype in ['agency_contracts_accruals', 'recurring_transactions_accruals']:
                    self.account_move_id.set_ongoing_status()
                else:
                    self.account_move_id.set_processing_accounting_status()

        if self.liquidation_reference_id:
            if self.action in ['approve']:
                self.liquidation_reference_id.dept_head_signature = self.dept_head_signature
                self.liquidation_reference_id.status = 'waiting_for_accounting'
                self.liquidation_reference_id.approved_by = self._uid
                self.liquidation_reference_id.approved_date = datetime.now()
            elif self.action in ['validate']:
                self.liquidation_reference_id.accounting_signature = self.accounting_signature
                self.liquidation_reference_id.status = 'validated'
                self.liquidation_reference_id.validated_by = self._uid
                self.liquidation_reference_id.validated_date = datetime.now()

        return {'type': 'ir.actions.act_window_close'}
