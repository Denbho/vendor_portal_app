from odoo import fields, models, api
from odoo.exceptions import ValidationError

class AdminAllocateSIAmount(models.TransientModel):
    _name = 'admin.allocate.si.amount'
    _description = 'Allocate SI Amount'

    si_multiple_po_id = fields.Many2one('admin.si.multiple.po', string="Vendor SI Multiple PO")
    vendor_partner_id = fields.Many2one(related='si_multiple_po_id.vendor_partner_id')
    company_id = fields.Many2one(related='si_multiple_po_id.company_id')
    po_id = fields.Many2one('purchase.order', string="PO #")
    amount = fields.Float(string="Amount", required=True)
    unallocated_amount = fields.Float(string="Unallocated Amount")
    po_delivery_ids = fields.Many2many('po.delivery.line', 'admin_allocate_si_delivery_rel', string="DRs/GRs")
    show_warning = fields.Boolean(string="Show Warning")
    drgr_total_amount = fields.Float(string="DRs/GRs Total Amount", store=True, compute='_drgr_total_amount')

    @api.depends('po_delivery_ids.amount', 'po_delivery_ids')
    def _drgr_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in self.po_delivery_ids:
                total_amount += line.total_amount
            rec.drgr_total_amount = total_amount
            if total_amount != rec.amount:
                rec.show_warning = True
            else:
                rec.show_warning = False

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount and self.amount != self.drgr_total_amount:
            self.show_warning = True
        else:
            self.show_warning = False

    @api.onchange('si_multiple_po_id')
    def onchange_si_multiple_po_id(self):
        if self.si_multiple_po_id:
            allocated_amount = 0
            for line in self.env['admin.sales.invoice'].sudo().search([('si_multiple_po_id','=',self.si_multiple_po_id.id)]):
                allocated_amount += line.amount
            self.unallocated_amount = self.si_multiple_po_id.amount - allocated_amount

    @api.onchange('po_id')
    def onchange_po_id(self):
        if self.po_id:
            return {'domain': { 'po_delivery_ids':  [('po_id','=',self.po_id.id), ('countered_si_id', '=', False)] }}
        else:
            return {'domain': { 'po_delivery_ids':  [('partner_id', '=', self.vendor_partner_id.id), ('company_id', '=', self.company_id.id), ('countered_si_id', '=', False)] }}

    def btn_allocate(self):
        # raise ValidationError(str(self.si_multiple_po_id.purchase_ids.ids))
        if self.amount < 1:
            raise ValidationError("Amount must be higher than zero.")
        if self.unallocated_amount < self.amount:
            raise ValidationError("Amount should not be higher than unallocated amount.")
        if self.po_id:
            self.si_multiple_po_id.purchase_ids = [(4, self.po_id.id)]
        for line in self.po_delivery_ids:
            self.si_multiple_po_id.po_delivery_ids = [(4, line.id)]
        self.env['admin.sales.invoice'].sudo().create({
            'si_multiple_po_id': self.si_multiple_po_id.id,
            'po_delivery_ids': self.po_delivery_ids,
            'amount': self.amount,
            'purchase_id': self.po_id.id,
            'universal_vendor_code': self.si_multiple_po_id.universal_vendor_code,
            'vendor_partner_id': self.si_multiple_po_id.vendor_partner_id and self.si_multiple_po_id.vendor_partner_id.id or False,
            'invoice_date': self.si_multiple_po_id.invoice_date,
            'vendor_remarks': self.si_multiple_po_id.vendor_remarks,
            'document_status': self.si_multiple_po_id.document_status,
            'company_code': self.si_multiple_po_id.company_code,
            'company_id': self.si_multiple_po_id.company_id and self.si_multiple_po_id.company_id.id or False,
            'po_si_type': self.si_multiple_po_id.po_si_type,
            'admin_si_type': self.si_multiple_po_id.admin_si_type,
            'vendor_si_number': self.si_multiple_po_id.vendor_si_number,
            'service_order_number': self.si_multiple_po_id.service_order_number,
            'po_references': self.si_multiple_po_id.po_references,
        })
        return {'type': 'ir.actions.act_window_close'}
