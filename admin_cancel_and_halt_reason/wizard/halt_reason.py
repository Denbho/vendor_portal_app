from odoo import fields, models, api
from odoo.exceptions import Warning

class AdminHaltReason(models.TransientModel):
    _name = 'admin.halt.reason'
    _description = 'Admin Halt Reason'

    reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reason', required=True)
    description = fields.Text(string='Description')

    @api.onchange('reason_id')
    def onchange_reason_id(self):
        if self.reason_id:
            self.description = self.reason_id.description

    def btn_halt(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].sudo().browse(active_id)
        active_entry.write({
            'halt_reason_id': self.reason_id.id,
            'halt_description': self.description,
        })
        if active_model == 'purchase.bid.vendor':
            m_subject = 'Bidding Halted: '+ active_entry.bid_id.name
            active_entry.previous_status = active_entry.state
            active_entry.state = 'bidding_halt'
            active_entry.send_admin_email_notif('bid_halted', m_subject, active_entry.partner_id.email, 'purchase.bid.vendor')
        return {'type': 'ir.actions.act_window_close'}
