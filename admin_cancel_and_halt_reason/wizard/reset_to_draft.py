from odoo import fields, models, api
from odoo.exceptions import Warning

class AdminResetToDraftReason(models.TransientModel):
    _name = 'admin.reset.to.draft.reason'
    _description = 'Admin Reset to Draft Reason'

    reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reason', required=True)
    description = fields.Text(string='Description')

    @api.onchange('reason_id')
    def onchange_reason_id(self):
        if self.reason_id:
            self.description = self.reason_id.description

    def btn_reset_to_draft(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].sudo().browse(active_id)
        active_entry.write({
            'rtd_reason_id': self.reason_id.id,
            'rtd_description': self.description,
            'state': 'draft',
        })
        return {'type': 'ir.actions.act_window_close'}
