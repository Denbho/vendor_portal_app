from odoo import fields, models, api

class AdminReasonToDeclineRFQ(models.TransientModel):
    _name = 'admin.reason.to.decline.rfq'
    _description = 'Admin Reason to Decline RFQ'

    rfq_mail_id = fields.Many2one('admin.vendor.rfq', string='RFQ Mail')
    declined_reason_id = fields.Many2one('admin.declined.reason', string='Declined Reason', required=True)
    declined_note = fields.Text(string='Declined Note')

    def btn_decline(self):
        self.rfq_mail_id.declined_reason_id = self.declined_reason_id.id
        self.rfq_mail_id.declined_note = self.declined_note
        self.rfq_mail_id.state = 'declined'
        return {'type': 'ir.actions.act_window_close'}
