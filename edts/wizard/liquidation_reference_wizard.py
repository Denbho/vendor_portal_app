from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import Warning

OVERAGE_OR_WARNING = 'Please provide OR Number for Overage Liquidations.\n'\
                     'It is Found in Overage/Shortage Details Tab.'


class EDTSLiquidationReferenceWizard(models.TransientModel):
    _name = 'edts.liquidation.reference.wizard'
    _description = 'EDTS Liquidation Reference Wizard'

    liquidation_reference_id = fields.Many2one('edts.liquidation.reference', string='Liquidation Reference')
    liquidation_status = fields.Selection([
        ('unliquidated', 'Unliquidated'),
        ('partially_liquidated', 'Partially Liquidated'),
        ('fully_liquidated', 'Fully Liquidated'),
    ], string='Liquidation Status', default='unliquidated', tracking=True)
    submission_status = fields.Selection([
        ('pending_for_submission', 'Pending For Submission'),
        ('partially_submitted', 'Partially Submitted'),
        ('fully_submitted', 'Fully Submitted'),
    ], string='Submission Status', default='pending_for_submission', tracking=True)

    def update_liquidation_status_action_proceed(self):
        if self.liquidation_status in ['fully_liquidated'] and \
                (self.liquidation_reference_id.total_liquidated_amount > self.liquidation_reference_id.amount and self.liquidation_reference_id.or_number_overage is False):
            raise Warning(OVERAGE_OR_WARNING)

        self.liquidation_reference_id.liquidation_status = self.liquidation_status

        if self.liquidation_reference_id.liquidation_status in ['fully_liquidated']:
            self.liquidation_reference_id.audited_by = self._uid
            self.liquidation_reference_id.audited_date = datetime.now()
        return {'type': 'ir.actions.act_window_close'}

    def update_submission_status_action_proceed(self):
        self.liquidation_reference_id.submission_status = self.submission_status

        if self.liquidation_reference_id.submission_status in ['fully_submitted']:
            self.liquidation_reference_id.received_by = self._uid
            self.liquidation_reference_id.received_date = datetime.now()
        return {'type': 'ir.actions.act_window_close'}
