from odoo import fields, models, api
from datetime import datetime


class EDTSPaymentReferenceLineWizard(models.TransientModel):
    _name = 'edts.payment.reference.line.wizard'
    _description = 'EDTS Payment Reference Line Wizard'

    payment_reference_line_id = fields.Many2one('edts.payment.reference.line', string='Payment Reference Line')
    mode = fields.Selection([
        ('wire', 'Wire Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('check_writer', 'Check Writer'),
        ('debit_memo', 'Debit Memo'),
    ], string='Payment Mode', default=False, required=True)
    payment_received_by = fields.Char(string='Payment Received By')
    payment_received_date = fields.Date(string='Payment Received Date')

    def release_action_proceed(self):
        payment_reference_line = self.payment_reference_line_id
        account_move = self.payment_reference_line_id.account_move_id

        payment_reference_line.released = True
        payment_reference_line.payment_received_by = self.payment_received_by
        payment_reference_line.payment_received_date = self.payment_received_date

        if account_move.status not in ['partial_payment_released'] and account_move.total_payment_amount < account_move.amount:
            account_move.set_partial_payment_released_status()
        elif account_move.status not in ['fully_paid'] and account_move.total_payment_amount >= account_move.amount:
            account_move.set_fully_paid_status()

        payment_reference_line.released_date = datetime.now()
        payment_reference_line.released_by = self.env.user.name

        if account_move.vendor_id:
            payment_reference_line.send_payment_released_email()

        return {'type': 'ir.actions.act_window_close'}
