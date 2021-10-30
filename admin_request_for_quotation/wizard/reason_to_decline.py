from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta

class AdminReasonToDeclineRFQ(models.TransientModel):
    _name = 'admin.reason.to.decline.rfq'
    _description = 'Admin Reason to Decline RFQ'

    rfq_mail_id = fields.Many2one('admin.vendor.rfq', string='RFQ Mail')
    declined_reason_id = fields.Many2one('admin.declined.reason', string='Declined Reason', required=True)
    declined_note = fields.Text(string='Declined Note')

    def btn_decline(self):
        if self.rfq_mail_id.rfq_id and self.rfq_mail_id.rfq_id.close_date < fields.Date.today():
            raise ValidationError('RFQ has already lapsed the closing date, please coordinate with the Purchasing Team.')
        self.rfq_mail_id.write({
            'declined_reason_id': self.declined_reason_id.id,
            'declined_note': self.declined_note,
            'state': 'declined'
        })
        return {'type': 'ir.actions.act_window_close'}
