from odoo import fields, models, api
from datetime import datetime


class EDTSCounteredWizard(models.TransientModel):
    _name = 'edts.countered.wizard'
    _description = 'EDTS Countered Wizard'

    account_move_id = fields.Many2one('account.move', string='Account Move')
    countering_notes = fields.Text(string='Countering Notes', required=True)

    def countered_action_proceed(self):
        self.account_move_id.countered = True
        self.account_move_id.countered_date = datetime.now()
        self.account_move_id.countered_by = self._uid
        self.account_move_id.countering_notes = self.countering_notes

        return {'type': 'ir.actions.act_window_close'}
