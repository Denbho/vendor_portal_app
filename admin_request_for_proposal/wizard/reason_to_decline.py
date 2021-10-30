from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta

class AdminReasonToDeclineRFP(models.TransientModel):
    _name = 'admin.reason.to.decline.rfp'
    _description = 'Admin Reason to Decline RFP'

    rfp_mail_id = fields.Many2one('admin.request.for.proposal.line', string='RFP Line')
    declined_reason_id = fields.Many2one('admin.declined.reason', string='Declined Reason', required=True)
    declined_note = fields.Text(string='Declined Note')

    def btn_decline(self):
        if self.rfp_mail_id.rfp_id and self.rfp_mail_id.rfp_id.close_date < fields.Date.today():
            raise ValidationError('RFP has already lapsed the closing date, please coordinate with the Purchasing Team.')
        self.rfp_mail_id.write({
            'declined_reason_id': self.declined_reason_id.id,
            'declined_note': self.declined_note,
            'state': 'declined'
        })
        return {'type': 'ir.actions.act_window_close'}
