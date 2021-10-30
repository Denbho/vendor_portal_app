from odoo import fields, models, api


class AdminSalesInvoiceCreateEdtsWizard(models.TransientModel):
    _name = 'admin.sales.invoice.create.edts.wizard'
    _description = 'Admin Sales Invoice Create EDTS Wizard'

    admin_sales_invoice_id = fields.Many2one('admin.sales.invoice', string='Admin Sales Invoice Id')
    payment_description = fields.Text(string='Payment Description')
    attention_to = fields.Many2one('res.users', string='Attention To')

    def create_edts_action_proceed(self):
        view_id = self.env.ref('edts.view_move_form_inherit').id
        edts_subtype = 'invoice_w_po' if self.admin_sales_invoice_id.admin_si_type in ['with_po'] else 'invoice_wo_po'
        default_journal_id = self.env['account.journal'].search([('edts_subtype', 'in', [edts_subtype]), ('company_id', '=', self.admin_sales_invoice_id.company_id.id)], limit=1)
        default_payment_term = self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')])

        vals = {
            'admin_sales_invoice_id': self.admin_sales_invoice_id.id,
            'company_code': self.admin_sales_invoice_id.company_code,
            'edts_company_id': self.admin_sales_invoice_id.company_id.id,
            'edts_purchase_id': self.admin_sales_invoice_id.purchase_id.id,
            'payment_term_id': default_payment_term.id if default_payment_term[:1] and self.admin_sales_invoice_id.purchase_id and not self.admin_sales_invoice_id.purchase_id.payment_term_id else self.admin_sales_invoice_id.purchase_id.payment_term_id.id,
            'edts_subtype': edts_subtype,
            'journal_id': default_journal_id.id if default_journal_id[:1] else False,
            'ref': self.admin_sales_invoice_id.vendor_si_number,
            'vendor_id': self.admin_sales_invoice_id.vendor_partner_id.id,
            'vendor_code_113': self.admin_sales_invoice_id.vendor_partner_id.vendor_code_113,
            'vendor_code_303': self.admin_sales_invoice_id.vendor_partner_id.vendor_code_303,
            'universal_vendor_code': self.admin_sales_invoice_id.universal_vendor_code,
            'reason': self.payment_description,
            'balance': self.admin_sales_invoice_id.purchase_id.amount_total,
            'amount': self.admin_sales_invoice_id.amount,
            'po_delivery_ids': self.admin_sales_invoice_id.po_delivery_ids.ids,
            'countered': True,
            'countered_by': self.admin_sales_invoice_id.countered_by.id,
            'countered_date': self.admin_sales_invoice_id.countered_date,
            'countering_notes': self.admin_sales_invoice_id.countering_notes,
        }

        account_move = self.env['account.move'].create(vals)
        self.admin_sales_invoice_id.attention_to = self.attention_to
        self.admin_sales_invoice_id.account_move_id = account_move.id
        self.admin_sales_invoice_id.send_edts_invoice_created_notification_email()

        return {
            'name': 'Created EDTS',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': account_move.id,
            'target': 'current',
        }
