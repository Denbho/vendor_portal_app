from odoo import fields, models, api


class EDTSSubmitWizard(models.TransientModel):
    _name = 'edts.submit.wizard'
    _description = 'EDTS Submit Wizard'

    account_move_id = fields.Many2one('account.move', string='Account Move')
    edts_subtype = fields.Selection([
        ('invoice_wo_po', 'Invoice w/o PO'),
        ('invoice_w_po', 'Invoice w/ PO'),
        ('advance_payment', 'Advance Payment'),
        ('rawland_acquisition', 'Rawland Acquisition'),
        ('reimbursement', 'Reimbursement'),
        ('cash_advance', 'Cash Advance'),
        ('stl', 'STL'),
        ('techserv_liaison', 'Techserv/Liaison'),
        ('setup', 'Setup'),
        ('return', 'Return'),
        ('agency_contracts_accruals', 'Agency Contracts Accruals'),
        ('agency_contracts_monthly', 'Agency Contracts Monthly'),
        ('recurring_transactions_accruals', 'Recurring Transactions Accruals'),
        ('recurring_transactions_monthly', 'Recurring Transactions Monthly'),
    ], string='EDTS Subtype', default=False)
    requestor = fields.Many2one('res.users', string='Requestor')
    approver = fields.Many2one('res.users', string='Approver')
    processor = fields.Many2one('res.users', string='Processor')

    def submit_edts_action_proceed(self):
        self.account_move_id.approver = self.approver
        self.account_move_id.processor = self.processor

        if self.account_move_id.edts_subtype in ['return']:
            self.account_move_id.set_waiting_for_accounting_status()
            self.account_move_id.send_edts_for_validation_acctg_email()
        else:
            self.account_move_id.set_waiting_for_head_status()
            self.account_move_id.send_edts_for_approval_dept_head_email()

        return {'type': 'ir.actions.act_window_close'}
