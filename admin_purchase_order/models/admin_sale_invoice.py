# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger("_name_")


class AdminInvoicePayment(models.Model):
    _name = 'admin.invoice.payment'
    _description = "SI Payment Documents"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_release_date desc'

    name = fields.Char(string="Payment Transaction No.", required=True, track_visibility="always", copy=False,
                       index=True)
    payment_release_date = fields.Date(string="Payment Date", required=True, track_visibility="always")
    amount = fields.Float(string="Amount", required=True, track_visibility="always")
    or_number = fields.Char(string="OR Number", track_visibility="always")
    or_date = fields.Date(string="OR Date", track_visibility="always")
    original_or_received = fields.Boolean(string="Original OR Received", track_visibility="always")
    original_or_received_date = fields.Date(string="Original OR Received Date", track_visibility="always")
    remark = fields.Text(string="Remarks", track_visibility="always")
    admin_si_id = fields.Many2one('admin.sales.invoice', string="Sales Invoice", track_visibility="always",
                                  domain="[('company_id', '=', company_id), ('vendor_partner_id', '=', vendor_partner_id)]")
    admin_si_number = fields.Char(string="SI Number")
    invoice_date = fields.Date(string="Invoice Date", store=True, related="admin_si_id.invoice_date")
    si_amount = fields.Float('SI Amount', store=True, related="admin_si_id.amount")
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", store=True,
                                  related="admin_si_id.purchase_id")
    vendor_partner_id = fields.Many2one('res.partner', string="Supplier/Vendor", required=True)
    universal_vendor_code = fields.Char(string="Universal Vendor Code")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, index=True)
    company_code = fields.Char(string='Company Code')
    si_multiple_po_id = fields.Many2one('admin.si.multiple.po', string="SI Multiple PO")

    @api.onchange('vendor_partner_id')
    def onchange_vendor_partner_id(self):
        if self.vendor_partner_id:
            self.universal_vendor_code = self.vendor_partner_id.universal_vendor_code

    @api.onchange('universal_vendor_code')
    def onchange_universal_vendor_code(self):
        if self.universal_vendor_code:
            vendor_partner_id = self.env['res.partner'].sudo().search([('universal_vendor_code', '=', self.universal_vendor_code)],
                                                                    limit=1)
            if vendor_partner_id[:1]:
                self.vendor_partner_id = vendor_partner_id.id

    @api.onchange('admin_si_id')
    def onchange_po_id(self):
        if self.admin_si_id:
            self.admin_si_number = self.admin_si_id.vendor_si_number

    @api.onchange('admin_si_number')
    def onchange_admin_si_number(self):
        if self.admin_si_number:
            admin_si_id = self.env['admin.sales.invoice'].sudo().search(
                [('vendor_si_number', '=', self.admin_si_number)], limit=1)
            if admin_si_id[:1]:
                self.admin_si_id = admin_si_id.id

    @api.onchange('original_or_received')
    def onchange_original_or_received(self):
        if self.original_or_received:
            self.original_or_received_date = date.today()

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    def check_amount_against_invoice(self, invoice_id, amount):
        r = self.env['admin.sales.invoice'].sudo().browse(invoice_id)
        inv_amount = r.amount
        payments = self.sudo().search([('admin_si_id', '=', invoice_id), ('id', 'not in', [self.id])])
        if inv_amount < (amount + sum([r.amount for r in payments])):
            raise ValidationError(
                _("You are releasing total (Current + Previous) payment greater than the Invoice Value"))

    @api.model
    def create(self, vals):
        if vals.get('admin_si_id'):
            self.check_amount_against_invoice(vals.get('admin_si_id'), vals.get('amount'))
        res = super(AdminInvoicePayment, self).create(vals)
        res.onchange_company_code()
        res.onchange_admin_si_number()
        res.onchange_universal_vendor_code()
        return res

    def write(self, vals):
        if (vals.get('admin_si_id') or self.admin_si_id) or (vals.get('amount') or self.amount):
            self.check_amount_against_invoice(vals.get('admin_si_id') or self.admin_si_id.id,
                                              vals.get('amount') or self.amount)
        super(AdminInvoicePayment, self).write(vals)
        return True


class AdminSalesInvoice(models.Model):
    _name = 'admin.sales.invoice'
    _description = 'Allocated SI'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vendor_si_number'
    _order = 'invoice_date desc'

    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Waiting For Head Approval', 'Waiting For Head Approval'),
        ('Waiting For Accounting Validation', 'Waiting For Accounting Validation'),
        ('Processing Accounting', 'Processing Accounting'),
        ('Payment Ready For Releasing', 'Payment Ready For Releasing'),
        ('Partial Payment Released', 'Partial Payment Released'),
        ('Fully Paid', 'Fully Paid'),
        ('Rejected', 'Rejected')
    ], string="Status", default="Draft")
    document_status = fields.Selection([
        ('Original Documents Received', 'Original Documents Received'),
        ('Original Documents Review', 'Original Documents Review'),
        ('Awaiting Original Documents', 'Awaiting Original Documents'),
        ('Returned to Vendor', 'Returned to Vendor')
    ], string="Document Submission Status", default='Awaiting Original Documents')
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", track_visibility="always",
                                  domain="[('company_id', '=', company_id), ('partner_id', '=', vendor_partner_id)]")
    po_reference = fields.Char(string='Puchase Order Ref.')
    po_references = fields.Char(string="PO References")
    service_order_number = fields.Char(string="Service Order Number", track_visibility="always")
    admin_si_type = fields.Selection([('with_po', 'PO Related'), ('no_po', 'None PO Related')], string="Document Type",
                                     required=True, track_visibility="always")
    vendor_partner_id = fields.Many2one('res.partner', string="Supplier/Vendor")
    vendor_si_number = fields.Char(string="Vendor SI Number", required=True, track_visibility="always", copy=False,
                                   index=True)
    company_id = fields.Many2one('res.company', string="Company", track_visibility="always")
    company_code = fields.Char(string='Company Code', track_visibility="always")
    amount = fields.Float(string="Amount", track_visibility="always")
    invoice_date = fields.Date(string="Date", track_visibility="always")
    vendor_remarks = fields.Text(string="Vendor Remarks", track_visibility="always")
    po_delivery_ids = fields.Many2many('po.delivery.line', 'admin_si_delivery_rel', string="Delivery Document")
    countered = fields.Boolean(string="Countered")
    countered_date = fields.Date(string="Countered Date")
    countering_notes = fields.Text(string="Countering Notes")
    universal_vendor_code = fields.Char(string="Universal Vendor Code")
    po_si_type = fields.Selection([
                                    ('Goods or Services', 'Goods or Services'),
                                    ('Hauler/Delivery Charge', 'Hauler/Delivery Charge')
                                  ], string="PO SI type")
    si_multiple_po_id = fields.Many2one('admin.si.multiple.po', string="SI Multiple PO")

    @api.onchange('admin_si_type')
    def onchange_admin_si_type(self):
        if self.admin_si_type and self.admin_si_type == 'no_po':
            self.po_si_type = False

    @api.onchange('vendor_partner_id')
    def onchange_vendor_partner_id(self):
        if self.vendor_partner_id:
            self.universal_vendor_code = self.vendor_partner_id.universal_vendor_code

    @api.onchange('universal_vendor_code')
    def onchange_universal_vendor_code(self):
        if self.universal_vendor_code:
            vendor_partner_id = self.env['res.partner'].sudo().search([('universal_vendor_code', '=', self.universal_vendor_code)],
                                                                      limit=1)
            if vendor_partner_id[:1]:
                self.vendor_partner_id = vendor_partner_id.id

    @api.onchange('purchase_id')
    def onchange_purchase_id(self):
        if self.purchase_id:
            self.po_reference = self.purchase_id.name

    @api.onchange('po_reference')
    def onchange_po_reference(self):
        if self.po_reference:
            purchase_id = self.env['purchase.order'].sudo().search([('name', '=', self.po_reference)], limit=1)
            if purchase_id[:1]:
                self.purchase_id = purchase_id.id

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.constrains('po_delivery_ids', 'countered', 'countered_date')
    def check_countering(self):
        if len(self.po_delivery_ids.ids) > 0:
            if any([self.countered, self.countered_date]):
                for dr in self.po_delivery_ids:
                    if not dr.countered:
                        raise ValidationError(_(
                            "Please make sure that all DR/GR related to this SI has been tagged as Countered, before tagging this SI as Countered"))

    def check_amount_against_invoice(self, purchase_id, amount, admin_si_type, po_si_type):
        r = self.env['purchase.order'].sudo().browse(purchase_id)
        po = r.amount_total
        invoice = self.sudo().search([('purchase_id', '=', purchase_id), ('id', 'not in', [self.id])])
        if admin_si_type == 'with_po' and po_si_type == 'Goods or Services' and po < (amount + sum([r.amount for r in invoice])):
            raise ValidationError(_("Your total (Current + Previous) SI Value is greater than the POValue"))

    @api.model
    def create(self, vals):
        if vals.get('purchase_id'):
            self.check_amount_against_invoice(vals.get('purchase_id'), vals.get('amount'), vals.get('admin_si_type'), vals.get('po_si_type'))
        res = super(AdminSalesInvoice, self).create(vals)
        res.onchange_company_code()
        res.onchange_po_reference()
        res.onchange_universal_vendor_code()
        res.onchange_vendor_partner_id()
        return res

    def write(self, vals):
        if (vals.get('purchase_id') or self.purchase_id) or (vals.get('amount') or self.amount):
            self.check_amount_against_invoice(vals.get('purchase_id') or self.purchase_id.id,
                                              vals.get('amount') or self.amount, vals.get('admin_si_type') or self.admin_si_type,
                                              vals.get('po_si_type') or self.po_si_type)
        super(AdminSalesInvoice, self).write(vals)
        return True

class AdminSIMultiplePO(models.Model):
    _name = 'admin.si.multiple.po'
    _description = 'Vendor SI'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vendor_si_number'
    _order = 'invoice_date desc'

    def _compute_unallocated_amount(self):
        for rec in self:
            allocated_amount = 0
            for line in self.env['admin.sales.invoice'].sudo().search([('si_multiple_po_id','=',rec.id)]):
                allocated_amount += line.amount
            rec.allocated_amount = allocated_amount
            rec.unallocated_amount = rec.amount - allocated_amount

    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Waiting For Head Approval', 'Waiting For Head Approval'),
        ('Waiting For Accounting Validation', 'Waiting For Accounting Validation'),
        ('Processing Accounting', 'Processing Accounting'),
        ('Payment Ready For Releasing', 'Payment Ready For Releasing'),
        ('Partial Payment Released', 'Partial Payment Released'),
        ('Fully Paid', 'Fully Paid'),
        ('Rejected', 'Rejected')
    ], string="Status", default="Draft")
    document_status = fields.Selection([
        ('Original Documents Received', 'Original Documents Received'),
        ('Original Documents Review', 'Original Documents Review'),
        ('Awaiting Original Documents', 'Awaiting Original Documents'),
        ('Returned to Vendor', 'Returned to Vendor')
    ], string="Document Submission Status", default='Awaiting Original Documents')
    purchase_ids = fields.Many2many('purchase.order', 'admin_si_multiple_po_rel', string="Purchase Orders", track_visibility="always")
    service_order_number = fields.Char(string="Service Order Number", track_visibility="always")
    admin_si_type = fields.Selection([('with_po', 'PO Related'), ('no_po', 'None PO Related')], string="Document Type",
                                     required=True, track_visibility="always")
    vendor_partner_id = fields.Many2one('res.partner', string="Supplier/Vendor")
    vendor_si_number = fields.Char(string="Vendor SI Number", required=True, track_visibility="always", copy=False,
                                   index=True)
    company_id = fields.Many2one('res.company', string="Company", track_visibility="always")
    company_code = fields.Char(string='Company Code', track_visibility="always")
    amount = fields.Float(string="Amount", track_visibility="always")
    unallocated_amount = fields.Float(string="Unallocated Amount", compute='_compute_unallocated_amount')
    allocated_amount = fields.Float(string="Allocated Amount", compute='_compute_unallocated_amount')
    invoice_date = fields.Date(string="Date", track_visibility="always")
    vendor_remarks = fields.Text(string="Vendor Remarks", track_visibility="always")
    po_delivery_ids = fields.Many2many('po.delivery.line', 'admin_si_multiple_po_delivery_rel', string="DRs/GRs")
    vendor_payment_count = fields.Integer(compute="_compute_vendor_payment_count")
    vendor_si_count = fields.Integer(compute="_compute_vendor_si_count", string="Related SI Count")
    universal_vendor_code = fields.Char(string="Universal Vendor Code")
    po_references = fields.Char(string="PO References")
    po_si_type = fields.Selection([
                                    ('Goods or Services', 'Goods or Services'),
                                    ('Hauler/Delivery Charge', 'Hauler/Delivery Charge')
                                  ], string="PO SI type")

    def allocate_si_amount(self):
        self.env['admin.sales.invoice'].sudo().create({
            'si_multiple_po_id': self.id,
            'po_delivery_ids': self.po_delivery_ids,
            'amount': self.amount,
            'universal_vendor_code': self.universal_vendor_code,
            'vendor_partner_id': self.vendor_partner_id and self.vendor_partner_id.id or False,
            'invoice_date': self.invoice_date,
            'vendor_remarks': self.vendor_remarks,
            'document_status': self.document_status,
            'company_code': self.company_code,
            'company_id': self.company_id.id,
            'po_si_type': self.po_si_type,
            'admin_si_type': self.admin_si_type,
            'vendor_si_number': self.vendor_si_number,
            'service_order_number': self.service_order_number,
        })

    @api.onchange('admin_si_type')
    def onchange_admin_si_type(self):
        if self.admin_si_type and self.admin_si_type == 'no_po':
            self.po_si_type = False

    @api.onchange('vendor_partner_id')
    def onchange_vendor_partner_id(self):
        if self.vendor_partner_id:
            self.universal_vendor_code = self.vendor_partner_id.universal_vendor_code

    @api.onchange('universal_vendor_code')
    def onchange_universal_vendor_code(self):
        if self.universal_vendor_code:
            vendor_partner_id = self.env['res.partner'].sudo().search([('universal_vendor_code', '=', self.universal_vendor_code)],
                                                                      limit=1)
            if vendor_partner_id[:1]:
                self.vendor_partner_id = vendor_partner_id.id

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    def _compute_vendor_payment_count(self):
        for r in self:
            r.vendor_payment_count = self.env['admin.invoice.payment'].sudo().search_count([('si_multiple_po_id', '=', r.id)])

    def action_open_admin_si_payment(self):
        self.ensure_one()
        return {
            'name': _('Payment Released'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,pivot',
            'res_model': 'admin.invoice.payment',
            'domain': [('si_multiple_po_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_si_multiple_po_id': self.id,
                'default_vendor_partner_id': self.vendor_partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    def _compute_vendor_si_count(self):
        for r in self:
            r.vendor_si_count =  self.env['admin.sales.invoice'].sudo().search_count([('si_multiple_po_id','=',r.id)])

    def action_open_admin_vendor_si(self):
        self.ensure_one()
        return {
            'name': _('Vendor Sales Invoice'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'admin.sales.invoice',
            'domain': [('si_multiple_po_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_si_multiple_po_id': self.id,
                'default_vendor_partner_id': self.vendor_partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    @api.model
    def create(self, vals):
        res = super(AdminSIMultiplePO, self).create(vals)
        res.onchange_company_code()
        res.onchange_universal_vendor_code()
        res.onchange_vendor_partner_id()
        return res
