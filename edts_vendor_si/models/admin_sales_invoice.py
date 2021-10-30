# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AdminSalesInvoiceInherit(models.Model):
    _inherit = 'admin.sales.invoice'

    account_move_id = fields.Many2one('account.move', string='EDTS No.', ondelete='cascade', readonly=True)
    attention_to = fields.Many2one('res.users', string='Attention To')
    countered_by = fields.Many2one('res.users', string='Countered By')
    countered_date = fields.Datetime(string='Countered Date')
    edts_status = fields.Selection(string='EDTS Status', related='account_move_id.status')

    def write(self, vals):
        record = super(AdminSalesInvoiceInherit, self).write(vals)

        if self.account_move_id:
            self.update_edts_fields(vals)

        return record

    def create_edts(self):
        view_id = self.env.ref('edts_vendor_si.admin_sales_invoice_create_edts_view_form').id

        return {
            'name': 'Create EDTS',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'admin.sales.invoice.create.edts.wizard',
            'target': 'new',
            'context': {
                'default_admin_sales_invoice_id': self.id,
            }
        }

    def update_edts_fields(self, vals):
        if 'vendor_si_number' in vals:
            self.account_move_id.ref = self.vendor_si_number

        if ('universal_vendor_code' or 'vendor_partner_id') in vals:
            self.account_move_id.vendor_code_113 = self.vendor_partner_id.vendor_code_113
            self.account_move_id.vendor_code_303 = self.vendor_partner_id.vendor_code_303
            self.account_move_id.universal_vendor_code = self.universal_vendor_code
            self.account_move_id.vendor_id = self.vendor_partner_id.id

        if 'purchase_id' in vals:
            default_payment_term = self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')])
            self.account_move_id.edts_purchase_id = self.purchase_id.id
            self.account_move_id.payment_term_id = default_payment_term.id if default_payment_term[:1] and self.purchase_id and not self.purchase_id.payment_term_id else self.purchase_id.payment_term_id.id

        if 'amount' in vals:
            self.account_move_id.amount = self.amount

        if 'po_delivery_ids' in vals:
            self.account_move_id.po_delivery_ids = self.po_delivery_ids.ids if self.po_delivery_ids else vals['po_delivery_ids']

        return True

    @api.onchange('po_delivery_ids')
    def onchange_edts_vendor_si_amount_via_po_delivery_ids(self):
        for record in self:
            total_dr_gr_amount = 0
            for delivery_id in record.po_delivery_ids:
                total_dr_gr_amount += delivery_id.total_amount

            record.amount = total_dr_gr_amount

    def send_edts_invoice_created_notification_email(self):
        template_id = self.env.ref('edts_vendor_si.email_template_edts_invoice_created_notification').id
        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.account_move_id.id, view_id, 'account.move')

        context = {
            'url': url
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)


class AdminInvoicePaymentInherit(models.Model):
    _inherit = 'admin.invoice.payment'

    edts_payment_reference = fields.Many2one('edts.payment.reference.line', string='EDTS Payment Reference')