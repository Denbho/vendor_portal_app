# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class PaymentReferenceLineInherit(models.Model):
    _inherit = 'edts.payment.reference.line'

    def write(self, vals):
        record = super(PaymentReferenceLineInherit, self).write(vals)

        if 'released' in vals and vals['released']:
            self.edts_vendor_si_payment_released()

        return record

    def edts_vendor_si_payment_released(self):
        if self.released and self.account_move_id.admin_sales_invoice_id:
            admin_invoice_payment = self.env['admin.invoice.payment']

            vals = {
                'admin_si_id': self.account_move_id.admin_sales_invoice_id.id,
                'admin_si_number': self.account_move_id.admin_sales_invoice_id.vendor_si_number,
                'vendor_partner_id': self.account_move_id.admin_sales_invoice_id.vendor_partner_id.id,
                'purchase_id': self.account_move_id.admin_sales_invoice_id.purchase_id.id,
                'company_id': self.account_move_id.admin_sales_invoice_id.company_id.id,
                'company_code': self.account_move_id.admin_sales_invoice_id.company_id.code,
                'or_number': self.or_number,
                'or_date': self.or_date,
                'original_or_received': True,
                'original_or_received_date': datetime.now().date(),
                'edts_payment_reference': self.id,
                'name': self.payment_doc,
                'amount': self.payment_amount,
                'payment_release_date': datetime.now().date()
            }
            admin_invoice_payment.create(vals)
