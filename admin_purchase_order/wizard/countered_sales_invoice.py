from odoo import fields, models, api
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError

class SalesInvoiceCountered(models.TransientModel):
    _name = 'admin.sales.invoice.countered'
    _description = 'Countered Sales Invoice'

    countering_notes = fields.Text(string="Countering Notes", required=True)
    sales_invoice_id = fields.Many2one('admin.sales.invoice', string="Vendor Sales Invoice")

    def btn_countered(self):
        self.sales_invoice_id.check_countering()
        self.sales_invoice_id.countered = True
        self.sales_invoice_id.countered_date = date.today()
        self.sales_invoice_id.countering_notes = self.countering_notes
        for line in self.sales_invoice_id.po_delivery_ids:
            line.countered_si_id = self.sales_invoice_id.id
        return {'type': 'ir.actions.act_window_close'}
