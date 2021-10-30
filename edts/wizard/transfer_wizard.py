from odoo import fields, models, api


class EDTSSubmitWizard(models.TransientModel):
    _name = 'edts.transfer.wizard'
    _description = 'EDTS Transfer Wizard'

    account_move_id = fields.Many2one('account.move', string='Account Move')
    edts_status = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_head', 'Waiting for Head Approval'),
        ('waiting_for_accounting', 'Waiting for Accounting Validation'),
        ('ongoing', 'Ongoing'),
        ('processing_accounting', 'Processing Accounting'),
        ('processing_finance', 'Processing Finance'),
        ('partial_payment_released', 'Partial Payment Released'),
        ('fully_paid', 'Fully Paid'),
        ('done', 'Done'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')], string='EDTS Status')
    requestor_from = fields.Many2one('res.users', string='Requestor From')
    requestor_to = fields.Many2one('res.users', string='Requestor To')
    approver_from = fields.Many2one('res.users', string='Approver From')
    approver_to = fields.Many2one('res.users', string='Approver To')
    processor_from = fields.Many2one('res.users', string='Processor From')
    processor_to = fields.Many2one('res.users', string='Processor To')

    def transfer_edts_action_proceed(self):
        if self.requestor_to:
            self.account_move_id.requestor = self.requestor_to

        if self.approver_to:
            self.account_move_id.approver = self.approver_to

        if self.processor_to:
            self.account_move_id.processor = self.processor_to

        return {'type': 'ir.actions.act_window_close'}
