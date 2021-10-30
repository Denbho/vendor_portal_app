from odoo import fields, models, api
from datetime import datetime


class SalesInvoiceCounteredInherit(models.TransientModel):
    _inherit = 'admin.sales.invoice.countered'

    def btn_countered(self):
        self.sales_invoice_id.check_countering()
        self.sales_invoice_id.countered = True
        self.sales_invoice_id.countered_date = datetime.now()
        self.sales_invoice_id.countered_by = self._uid
        self.sales_invoice_id.countering_notes = self.countering_notes

        return {'type': 'ir.actions.act_window_close'}
