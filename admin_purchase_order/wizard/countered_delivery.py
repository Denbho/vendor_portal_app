from odoo import fields, models, api
from datetime import datetime, date, timedelta

class PODeliveryLineCountered(models.TransientModel):
    _name = 'po.delivery.line.countered'
    _description = 'Countered Delivery'

    countering_notes = fields.Text(string="Countering Notes", required=True)
    po_delivery_line_id = fields.Many2one('po.delivery.line', string="PO Delivery Line")

    def btn_countered(self):
        self.po_delivery_line_id.countered = True
        self.po_delivery_line_id.countered_date = date.today()
        self.po_delivery_line_id.countering_notes = self.countering_notes
        return {'type': 'ir.actions.act_window_close'}
