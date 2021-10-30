# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning
import re

_SAP_DELIVERY_STATUS = [
    ('undelivered', 'Undelivered'),
    ('partially_delivered', 'Partially Delivered'),
    ('fully_delivered', 'Fully Delivered'),
]

READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sap_delivery_status = fields.Selection(selection=_SAP_DELIVERY_STATUS, string='SAP Delivery Status', store=True,
                                           compute='_sap_delivery_status')
    delivery_line = fields.One2many('po.delivery.line', 'po_id', string='Delivery Information')
    invoice_payment_line = fields.One2many('po.invoices.and.payments', 'po_id', string='Invoices and Payments')
    delivery_count = fields.Integer(compute="_compute_dr_count")
    vendor_si_count = fields.Integer(compute="_compute_vendor_si_count")
    vendor_payment_count = fields.Integer(compute="_compute_vendor_payment_count")
    po_doc_type_id = fields.Many2one('admin.po.document.type', string='PO Document Type',
                                     domain="[('company_id','=',company_id)]")
    po_doc_type_code = fields.Char(string='PO Document Type Code')
    company_code = fields.Char(string='Company Code')
    total_tax_amount = fields.Monetary(string='Taxed Amount', store=True, readonly=True, compute='_po_amount_all')
    charge_amount = fields.Float(string='Charge Amount')
    acceptance_status = fields.Selection(selection=[('accepted', 'Accepted'), ('declined', 'Declined')],
                                         string='Vendor Acceptance Status')
    acceptance_date = fields.Date(string='Acceptance Date')
    declined_date = fields.Date(string='Declined Date')
    declined_reason_id = fields.Many2one('admin.declined.reason', string='Declined Reason')
    declined_note = fields.Text(string='Declined Note')
    universal_vendor_code = fields.Char(string="Universal Vendor Code")
    contractor_name = fields.Char(string="Contractor")
    model = fields.Char(string="Model")
    model_remarks = fields.Text(string="Model Remarks")
    plant_id = fields.Many2one('location.plant', 'Plant', domain="[('company_id','=',company_id)]")
    plant_code = fields.Char(string='Plant Code')
    location_id = fields.Many2one('stock.location', string='Delivery Location',
                                  domain="[('company_id','=',company_id), ('plant_id', '=', plant_id)]")
    location_code = fields.Char(string='Delivery Location Code')
    expected_delivery_date = fields.Date(string='Expected Delivery Date')
    unloading_point = fields.Char(string='Unloading Point')
    recipient = fields.Char(string='Recipient')
    other_instructions = fields.Char(string='Other Instructions')
    payment_term_code = fields.Char(string='Payment Terms Code')
    release_indicator = fields.Selection(selection=[('unreleased', 'Unreleased'), ('released', 'Released')],
                                         string='SAP PO Status', default='unreleased')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, states=READONLY_STATES,
                                 change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    sap_line_items_count = fields.Integer(string='SAP Line Items Count', copy=False)
    active_line_items_count = fields.Integer(string='Active Line Items Count',
                                             compute="_active_line_items_count")
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the PO without removing it.")
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_po_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_po_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_po_amount_all')

    def button_confirm(self):
        for order in self:
            # Add vendor to follower
            if order.partner_id:
                if not self.env['mail.followers'].search([('res_id','=',order.id),('res_model','=','purchase.order'),('partner_id','=',order.partner_id.id)]):
                    self.env['mail.followers'].create({
                       'res_id': order.id,
                       'res_model': 'purchase.order',
                       'partner_id': order.partner_id.id,
                    })
        return super(PurchaseOrder, self).button_confirm()

    def cron_confirm_complete_po(self):
        po = self.search([('state', 'not in', ['purchase', 'done', 'cancel', False]), ('partner_id', '!=', False)])
        for r in po:
            if r.active_line_items_count >= r.sap_line_items_count:
                r.sudo().button_confirm()

    def _active_line_items_count(self):
        for rec in self:
            rec.active_line_items_count = self.env['purchase.order.line'].sudo().search_count(
                [('order_id', '=', rec.id), ('active', '=', True)])

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        if 'acceptance_status' in vals and vals['acceptance_status'] == 'accepted':
            self.acceptance_date = fields.Date.today()
        return res

    @api.depends('order_line.sap_delivery_status', 'order_line')
    def _sap_delivery_status(self):
        for order in self:
            status = 'undelivered'
            with_partially_delivered = False
            with_fully_delivered = False
            with_undelivered = False
            for line in order.order_line:
                if line.sap_delivery_status == 'partially_delivered':
                    with_partially_delivered = True
                elif line.sap_delivery_status == 'fully_delivered':
                    with_fully_delivered = True
                else:
                    with_undelivered = True
            if with_partially_delivered:
                status = 'partially_delivered'
            else:
                if with_fully_delivered and not with_undelivered:
                    status = 'fully_delivered'
            order.update({
                'sap_delivery_status': status,
            })

    @api.onchange('payment_term_id')
    def onchange_payment_term_id(self):
        if self.payment_term_id:
            self.payment_term_code = self.payment_term_id.code

    @api.onchange('payment_term_code')
    def onchange_payment_term_code(self):
        if self.payment_term_code:
            payment_term_id = self.env['account.payment.term'].sudo().search([('code', '=', self.payment_term_code)],
                                                                             limit=1)
            if payment_term_id[:1]:
                self.payment_term_id = payment_term_id.id

    @api.onchange('plant_id')
    def onchange_plant_id(self):
        if self.plant_id:
            self.plant_code = self.plant_id.code

    @api.onchange('plant_code')
    def onchange_plant_code(self):
        if self.plant_code:
            plant_id = self.env['location.plant'].sudo().search([('code', '=', self.plant_code)], limit=1)
            if plant_id[:1]:
                self.plant_id = plant_id.id

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            self.location_code = self.location_id.code

    # needed to add sap_client_id
    @api.onchange('location_code')
    def onchange_location_code(self):
        if self.location_code:
            location_id = self.env['stock.location'].sudo().search([('code', '=', self.location_code)], limit=1)
            if location_id[:1]:
                self.location_id = location_id.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.universal_vendor_code = self.partner_id.universal_vendor_code

    @api.onchange('universal_vendor_code')
    def onchange_universal_vendor_code(self):
        if self.universal_vendor_code:
            partner_id = self.env['res.partner'].sudo().search(
                [('universal_vendor_code', '=', self.universal_vendor_code)], limit=1)
            if partner_id[:1]:
                self.partner_id = partner_id.id

    @api.depends('order_line.price_total', 'charge_amount')
    def _po_amount_all(self):
        for order in self:
            tax_amount = amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                tax_amount += line.tax_amount
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'total_tax_amount': order.currency_id.round(tax_amount),
                'amount_total': amount_untaxed + amount_tax + order.charge_amount,
            })

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

    @api.onchange('po_doc_type_id')
    def onchange_po_doc_type_id(self):
        if self.po_doc_type_id:
            self.po_doc_type_code = self.po_doc_type_id.code

    @api.onchange('po_doc_type_code')
    def onchange_po_doc_type_code(self):
        if self.po_doc_type_code:
            po_doc_type_id = self.env['admin.po.document.type'].sudo().search([('code', '=', self.po_doc_type_code)],
                                                                              limit=1)
            if po_doc_type_id[:1]:
                self.po_doc_type_id = po_doc_type_id.id

    @api.model
    def create(self, vals):
        if vals.get('location_code') and vals.get('sap_client_id'):
            location = self.env['stock.location'].sudo().search([('code', '=', vals.get('location_code')),
                                                                 ('sap_client_id', '=', vals.get('sap_client_id'))],
                                                                limit=1)
            if location[:1]:
                vals.update({
                    'location_id': location.id,
                    'company_id': location.plant_id and location.plant_id.company_id.id or False,
                    'plant_id': location.plant_id and location.plant_id.id or False
                })
        if (not vals.get('location_code') or not vals.get('plant_id')) and vals.get('plant_code') and vals.get(
                'sap_client_id'):
            plant = self.env['location.plant'].sudo().search(
                [('code', '=', vals.get('plant_code')), ('sap_client_id', '=', vals.get('sap_client_id'))], limit=1)
            if plant[:1]:
                vals.update({
                    'company_id': plant.company_id.id,
                    'plant_id': plant.id
                })
        if not vals.get('company_id'):
            company = self.env['res.company'].sudo().search([('code', '=', vals.get('company_code'))], limit=1)
            vals['company_id'] = company[:1] and company.id or False
        if vals.get('universal_vendor_code'):
            partner = self.env['res.partner'].sudo().search(
                [('universal_vendor_code', '=', vals.get('universal_vendor_code'))], limit=1)
            vals['partner_id'] = partner[:1] and partner.id or False
        if vals.get('po_doc_type_code'):
            po_doc_type = self.env['admin.po.document.type'].sudo().search(
                [('code', '=', vals.get('po_doc_type_code'))], limit=1)
            vals['po_doc_type_id'] = po_doc_type[:1] and po_doc_type.id or False
        if vals.get('payment_term_code'):
            payment_term = self.env['account.payment.term'].sudo().search(
                [('code', '=', vals.get('payment_term_code'))], limit=1)
            vals['payment_term_id'] = payment_term[:1] and payment_term.id or False
        return super(PurchaseOrder, self).create(vals)

    def _compute_vendor_payment_count(self):
        for r in self:
            r.vendor_payment_count = self.env['admin.invoice.payment'].sudo().search_count([('purchase_id', '=', r.id)])

    def _compute_dr_count(self):
        for r in self:
            r.delivery_count = self.env['po.delivery.line'].sudo().search_count([('po_id', '=', r.id)])

    def _compute_vendor_si_count(self):
        for r in self:
            r.vendor_si_count = self.env['admin.sales.invoice'].sudo().search_count([('purchase_id', '=', r.id)])

    def action_open_admin_sale_invoice(self):
        self.ensure_one()
        return {
            'name': _('Sales Invoice'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'admin.sales.invoice',
            'domain': [('purchase_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_purchase_id': self.id,
                'default_admin_si_type': 'with_po',
                'default_vendor_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    def action_open_admin_po_payment(self):
        self.ensure_one()
        return {
            'name': _('Payment Released'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'admin.invoice.payment',
            'domain': [('purchase_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_vendor_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _rec_name = 'display_name'

    sap_goods_receipt = fields.Char(string="SAP Goods Receipt")
    sap_delivery_status = fields.Selection(selection=_SAP_DELIVERY_STATUS, string='SAP Delivery Status')
    delivery_product_line = fields.One2many('po.delivery.product.line', 'product_line_id',
                                            string='Delivery Product Line')
    si_product_line = fields.One2many('po.invoices.and.payments.product.line', 'product_line_id',
                                      string='SI Product Line')
    qty_delivered = fields.Float(string="Delivered Qty", store=True, compute="_compute_qty_received")
    pr_references = fields.Char(string="PR References")
    pr_notes = fields.Text(string="PR Notes")
    purchase_requisition_line_ids = fields.Many2many('purchase.requisition.material.details', 'po_pr_line_rel')
    purchase_requisition_line_id = fields.Many2one('purchase.requisition.material.details', string="PR Line")
    tax_amount = fields.Float(string="Tax Amount")
    product_uom_code = fields.Char(string="UoM Code", required=False)
    product_uom_category_code = fields.Char(string='Category Code')
    account_analytic_code = fields.Char(string="Analytic Account Code")
    material_code = fields.Char(string='Material Code / SKU')
    po_number = fields.Char(string='PO No.')
    po_line_code = fields.Char(string='PO Line Code')
    order_id = fields.Many2one('purchase.order', string='Order Reference', index=True, required=False,
                               ondelete='cascade')
    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    pr_line_item_code = fields.Char("PR Line Item Code")
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the product line item without removing it.")

    @api.onchange('order_id')
    def onchange_order_id(self):
        if self.order_id:
            self.po_reference = self.order_id.name

    @api.onchange('po_number')
    def onchange_po_number(self):
        if self.po_number:
            order_id = self.env['purchase.order'].sudo().search(
                [('name', '=', self.po_number), ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if order_id[:1]:
                self.order_id = order_id.id

    @api.onchange('material_code')
    def onchange_material_code(self):
        if self.material_code:
            product_id = self.env['product.product'].sudo().search([('default_code', '=', self.material_code)], limit=1)
            if product_id[:1]:
                self.product_id = product_id[0].id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.material_code = self.product_id.default_code
        return super(PurchaseOrderLine, self).onchange_product_id()

    @api.onchange('account_analytic_id')
    def onchange_account_analytic_id(self):
        if self.account_analytic_id:
            self.account_analytic_code = self.account_analytic_id.code

    # needed to idetify kung what specific comapany
    @api.onchange('account_analytic_code')
    def onchange_account_analytic_code(self):
        if self.account_analytic_code:
            account_analytic_id = self.env['account.analytic.account'].sudo().search(
                [('code', '=', self.account_analytic_code)], limit=1)
            self.account_analytic_id = account_analytic_id.id

    @api.onchange('product_uom_category_id')
    def onchange_product_uom_category_id(self):
        if self.product_uom_category_id:
            self.category_code = self.product_uom_category_id.code

    @api.onchange('product_uom_category_code')
    def onchange_product_uom_category_code(self):
        if self.product_uom_category_code:
            product_uom_category_id = self.env['uom.category'].sudo().search(
                [('code', '=', self.product_uom_category_code)], limit=1)
            if product_uom_category_id[:1]:
                self.product_uom_category_id = product_uom_category_id.id

    # @api.depends('product_qty', 'price_unit', 'tax_amount')
    # def _compute_amount(self):
    #     for line in self:
    #         total_amount = ((line.product_qty * line.price_unit) + line.tax_amount)
    #         line.price_tax = 0
    #         line.price_total = total_amount
    #         line.price_subtotal = total_amount

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': line.tax_amount,  # sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': line.product_qty * line.price_unit,
                'price_subtotal': taxes['total_excluded'] - line.tax_amount,
            })

    @api.onchange('pr_references')
    def onchange_pr_reference(self):
        if self.pr_references:
            # Comment split pr because 1 po line is equal to 1 related pr material line.
            # pr = re.split('; |, |\*|\n', self.pr_references)
            # if pr:
            pr_rec = self.env['purchase.requisition.material.details'].sudo().search([
                ('request_id_name', '=', self.pr_references),
                ('company_id', '=', self.company_id.id),
                ('material_code', '=', self.product_id.default_code),
                ('pr_line_item_code', '=', self.pr_line_item_code),
                ('sap_client_id', '=', self.sap_client_id)
            ], limit=1)
            self.purchase_requisition_line_ids = [(6, 0, pr_rec.ids)]
            # for line in pr_rec:
            #     processing_status = 'without_po'
            #     po_line_qty = 0
            #     po_lines = self.sudo().search([
            #         ('company_id', '=', pr_rec.company_id.id),
            #         ('product_id.default_code', '=', pr_rec.material_code),
            #         ('pr_references', 'ilike', pr_rec.request_id.name),
            #         ('pr_line_item_code', '=', pr_rec.pr_line_item_code),
            #         ('sap_client_id', '=', pr_rec.sap_client_id)
            #     ])
            #     for ln in po_lines:
            #         po_line_qty += ln.product_qty
            #     if po_line_qty > 0:
            #         if po_line_qty >= line.quantity:
            #             processing_status = 'fully_po'
            #         else:
            #             processing_status = 'partially_po'
            #     line.processing_status = processing_status

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_uom:
            self.product_uom_code = self.product_uom.code

    @api.onchange('product_uom_code')
    def onchange_product_uom_code(self):
        if self.product_uom_code:
            product_uom = self.env['uom.uom'].sudo().search([('code', '=', self.product_uom_code)], limit=1)
            if product_uom:
                self.product_uom = product_uom.id

    def get_product_id(self, material_code):
        if material_code:
            product = self.env['product.product'].sudo().search([('default_code', '=', material_code)], limit=1)
            return product
        return False

    def get_product_uom(self, uom_code):
        uom_id = False
        if uom_code:
            product_uom_ids = self.env['uom.uom'].sudo().search([('code', '=', uom_code)], limit=1)
            if product_uom_ids[:1]:
                uom_id = product_uom_ids[0].id
        return uom_id

    @api.model
    def create(self, vals):
        # product_id and product_uom_code is assigned as required field in _sql_constraints so need e trigger yung onchange of codes before saving/creation of entry to prevent validation error.
        if vals.get('material_code'):
            product_id = self.get_product_id(vals.get('material_code'))
            if product_id:
                vals['product_id'] = product_id.id
            if product_id and product_id.product_uom_code == vals.get('product_uom_code') and product_id.uom_id:
                vals['product_uom'] = product_id.uom_id.id
                vals['product_uom_category_id'] = product_id.uom_id.category_id.id
            elif product_id and product_id.po_uom_code == vals.get('product_uom_code') and product_id.uom_po_id:
                vals['product_uom'] = product_id.uom_po_id.id
                vals['product_uom_category_id'] = product_id.uom_id.category_id.id
            elif vals.get('product_uom_code'):
                product_uom = self.env['uom.uom'].sudo().search([('code', '=', vals.get('product_uom_code'))], limit=1)
                vals['product_uom'] = product_uom.id
                vals['product_uom_category_id'] = product_uom.category_id.id
        vals['price_unit'] = float(vals['price_unit'])
        vals['product_qty'] = float(vals['product_qty'])
        if vals.get('po_number') and vals.get('sap_client_id'):
            order_id = self.env['purchase.order'].sudo().search(
                [('name', '=', vals.get('po_number')), ('sap_client_id', '=', vals.get('sap_client_id'))], limit=1)
            if order_id[:1]:
                vals['order_id'] = order_id.id
                if vals.get('pr_references') and vals.get('pr_line_item_code'):
                    pr_rec_line = self.env['purchase.requisition.material.details'].sudo().search([
                        ('request_id_name', '=', vals.get('pr_references')),
                        ('company_id', '=', order_id.company_id.id),
                        ('material_code', '=', vals.get('material_code')),
                        ('pr_line_item_code', '=', vals.get('pr_line_item_code')),
                        ('sap_client_id', '=', vals.get('sap_client_id'))
                    ], limit=1)
                    vals['purchase_requisition_line_id'] = pr_rec_line[:1] and pr_rec_line.id
                    if pr_rec_line[:1] and pr_rec_line.cost_center_id:
                        vals['account_analytic_id'] = pr_rec_line.cost_center_id.id
                    elif vals.get('account_analytic_code'):
                        account_analytic_id = self.env['account.analytic.account'].sudo().search(
                            [('code', '=', self.account_analytic_code)], limit=1)
                        vals['account_analytic_id'] = account_analytic_id.id
        return super(PurchaseOrderLine, self).create(vals)

    def write(self, vals):
        super(PurchaseOrderLine, self).write(vals)
        if vals.get('pr_references') or vals.get('company_id') or 'product_qty' in vals:
            self.onchange_pr_reference()
        return True

    @api.depends('delivery_product_line', 'delivery_product_line.delivery_quantity')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        for line in self:
            line.qty_received = 0.0
            line.qty_delivered = 0.0
            total = 0
            for delivery in line.delivery_product_line:
                total += delivery.delivery_quantity
            if total > 0:
                line.qty_received = total
                line.qty_delivered = total

    @api.depends('name', 'product_qty', 'pr_references', 'price_unit', 'order_id.name')
    def _compute_display_name(self):
        diff = dict(show_product_qty=None, show_price=None)
        names = dict(self.with_context(**diff).name_get())
        for po_line in self:
            po_line.display_name = names.get(po_line.id)

    def name_get(self):
        result = []
        for po_line in self:
            name = po_line.name
            if po_line.order_id and po_line.order_id.name:
                name = po_line.order_id.name + ' (' + name + ')'
            if self.env.context.get('show_product_qty'):
                name += ' (' + str(po_line.product_qty) + ')'
            if self.env.context.get('show_price'):
                name += ' (' + "{:,.2f}".format(po_line.price_unit) + ')'
            result.append((po_line.id, name))
        return result


class PODeliveryLine(models.Model):
    _name = "po.delivery.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "PO Delivery Line"
    _sql_constraints = [
        ('unique_company_gr_line', 'unique(gr_year, gr_number, po_reference, sap_client_id)',
         'The combination of the ff. "gr_year, gr_number, po_reference, sap_client_id" fields must have unique value per Sap Severs!')]
    _rec_name = "dr_no"

    dr_no = fields.Char('DR No.')
    gr_number = fields.Char('GR No.')
    dr_date = fields.Date('DR Date')
    receiving_date = fields.Date('Receiving Date')
    delivered_by = fields.Char(string="Delivered By")
    received_by = fields.Char(string="Received By")
    company_id = fields.Many2one('res.company', string="Company")
    company_code = fields.Char(string="Company Code")
    po_id = fields.Many2one('purchase.order', string='PO #', ondelete='cascade')
    po_reference = fields.Char(string='PO Ref.')
    product_line = fields.One2many('po.delivery.product.line', 'po_delivery_id', string='Product Lines')
    received_original_doc = fields.Boolean(string="Received Original Docs")
    received_original_doc_date = fields.Date(string="Received Original Docs Date")
    countered = fields.Boolean(string="Countered")
    countered_date = fields.Date(string="Countered Date")
    countering_notes = fields.Text(string="Countering Notes")
    gr_year = fields.Char(string='GR Year')
    delivery_remarks = fields.Text(string='Delivery Remarks')
    partner_id = fields.Many2one('res.partner', string='Vendor', change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    universal_vendor_code = fields.Char(string="Universal Vendor Code")
    total_amount = fields.Float(string='Total Amount', store=True, compute='_total_amount')
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the dr/gr without removing it.")
    countered_si_id = fields.Many2one('admin.sales.invoice', string="Countered SI")

    @api.depends('product_line.amount', 'product_line')
    def _total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.product_line:
                total_amount += line.amount
            rec.total_amount = total_amount

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.universal_vendor_code = self.partner_id.universal_vendor_code

    @api.onchange('universal_vendor_code')
    def onchange_universal_vendor_code(self):
        if self.universal_vendor_code:
            partner_id = self.env['res.partner'].sudo().search(
                [('universal_vendor_code', '=', self.universal_vendor_code)], limit=1)
            if partner_id[:1]:
                self.partner_id = partner_id.id

    @api.onchange('po_id')
    def onchange_po_id(self):
        if self.po_id:
            self.po_reference = self.po_id.name
            self.partner_id = self.po_id.partner_id and self.po_id.partner_id.id or False
            self.company_id = self.po_id.company_id and self.po_id.company_id.id or False
            self.company_code = self.po_id.company_id and self.po_id.company_id.code or False

    @api.onchange('po_reference')
    def onchange_po_reference(self):
        if self.po_reference:
            po_id = self.env['purchase.order'].sudo().search(
                [('name', '=', self.po_reference), ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if po_id[:1]:
                self.po_id = po_id.id
                self.partner_id = po_id.partner_id and po_id.partner_id.id or False
                self.universal_vendor_code = po_id.partner_id and po_id.universal_vendor_code

    @api.onchange('received_original_doc')
    def onchange_received_original_doc(self):
        if self.received_original_doc:
            self.received_original_doc_date = date.today()
        else:
            self.received_original_doc_date = False

    @api.model
    def create(self, vals):
        dr_no = ''
        if 'dr_no' in vals:
            dr_no = vals['dr_no'].upper()
            dr_no = "".join(dr_no.split())
            vals['dr_no'] = dr_no
        if 'po_id' in vals and 'dr_no' in vals and 'dr_date' in vals:
            has_gr_number = False
            if 'gr_number' in vals and vals['gr_number'] and vals['gr_number'] != '':
                has_gr_number = True
            if not has_gr_number:
                existing_dr = self.sudo().search(
                    [('po_id', '=', vals['po_id']), ('dr_no', '=', vals['dr_no']), ('dr_date', '=', vals['dr_date'])],
                    limit=1)
                if existing_dr[:1]:
                    return existing_dr
        if vals.get('po_reference') and vals.get('sap_client_id'):
            po = self.env['purchase.order'].sudo().search(
                [('name', '=', vals.get('po_reference')), ('sap_client_id', '=', vals.get('sap_client_id'))], limit=1)
            vals.update({
                'po_id': po.id,
                'partner_id': po.partner_id and po.partner_id.id or False,
                'universal_vendor_code': po.partner_id and po.universal_vendor_code,
                'company_id': po.company_id.id,
                'company_code': po.company_id.code
            })
        return super(PODeliveryLine, self).create(vals)


class PODeliveryProductLine(models.Model):
    _name = "po.delivery.product.line"
    _description = "PO Delivery Product Line"
    _sql_constraints = [
        ('unique_company_gr_line', 'unique(gr_year, po_line_code, gr_number, po_ref, sap_client_id)',
         'The combination of the ff. "gr_year, po_line_code, gr_number, po_ref, sap_client_id" fields must have unique value per Sap Severs!')]

    name = fields.Char(string="Description")
    po_delivery_id = fields.Many2one('po.delivery.line', string='DRs/GRs', ondelete='cascade')
    po_delivery_ref = fields.Char(string='DR Ref.')
    po_id = fields.Many2one('purchase.order', string='PO No.')
    po_ref = fields.Char(string='PO Ref.')
    product_line_id = fields.Many2one('purchase.order.line', string='Product')
    product_id = fields.Many2one('product.product', string="Material/Service", store=True,
                                 related="product_line_id.product_id")
    product_code = fields.Char(string='Material Code/SKU')
    product_uom_code = fields.Char(string="UoM Code", required=False, )
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', store=True,
                                  related="product_line_id.product_uom")
    product_uom_category_id = fields.Many2one(store=True, related='product_line_id.product_id.uom_id.category_id')
    delivery_quantity = fields.Float(string='Delivery Quantity')
    sequence = fields.Integer(string='Sequence', default=10)
    po_line_code = fields.Char(string='PO Line Code')
    gr_number = fields.Char(string='GR No.')
    gr_year = fields.Char(string='GR Year')
    amount = fields.Float(string='Amount')
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the dr/gr product line item without removing it.")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_code = self.product_id.default_code

    @api.onchange('product_code')
    def onchange_product_code(self):
        if self.product_code:
            product_id = self.env['product.product'].sudo().search([('default_code', '=', self.product_code)], limit=1)
            if product_id:
                self.product_id = product_id.id

    @api.onchange('po_id')
    def onchange_po_id(self):
        if self.po_id:
            self.po_ref = self.po_id.name

    @api.onchange('po_ref')
    def onchange_po_ref(self):
        if self.po_ref:
            po_id = self.env['purchase.order'].sudo().search(
                [('name', '=', self.po_ref), ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if po_id:
                self.po_id = po_id.id

    @api.onchange('po_delivery_id')
    def onchange_po_delivery_id(self):
        if self.po_delivery_id:
            self.po_delivery_ref = self.po_delivery_id.dr_no

    @api.onchange('gr_number')
    def onchange_gr_number(self):
        if self.gr_number and self.gr_year:
            po_delivery_id = self.env['po.delivery.line'].sudo().search([('gr_number', '=', self.gr_number),
                                                                         ('gr_year', '=', self.gr_year),
                                                                         ('sap_client_id', '=', self.sap_client_id)],
                                                                        limit=1)
            if po_delivery_id:
                self.po_delivery_id = po_delivery_id.id

    @api.onchange('product_line_id')
    def _onchange_product_line_id(self):
        self.name = self.product_line_id.name
        self.delivery_quantity = self.product_line_id.product_qty
        if self.product_line_id:
            self.po_line_code = self.product_line_id.po_line_code

    @api.onchange('po_line_code')
    def onchange_po_line_code(self):
        if self.po_line_code:
            product_line_id = self.env['purchase.order.line'].sudo().search([('po_line_code', '=', self.po_line_code),
                                                                             ('po_number', '=', self.po_ref), (
                                                                                 'sap_client_id', '=',
                                                                                 self.sap_client_id)],
                                                                            limit=1)
            if product_line_id:
                self.product_line_id = product_line_id.id

    @api.onchange('delivery_quantity')
    def _onchange_delivery_quantity(self):
        if self.product_line_id and self.product_line_id.product_qty < self.delivery_quantity:
            raise Warning("Product delivery quantity should not be greater than PO quantity.")

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_uom:
            self.product_uom_code = self.product_uom.code

    @api.onchange('product_uom_code')
    def onchange_product_uom_code(self):
        if self.product_uom_code:
            product_uom = self.env['uom.uom'].sudo().search([('code', '=', self.product_uom_code)], limit=1)
            if product_uom:
                self.product_uom = product_uom.id

    @api.model
    def create(self, vals):
        if vals.get('gr_number') and vals.get('gr_year') and vals.get('sap_client_id') and vals.get('po_ref'):
            po_delivery = self.env['po.delivery.line'].sudo().search([('gr_number', '=', vals.get('gr_number')),
                                                                      ('gr_year', '=', vals.get('gr_year')),
                                                                      ('sap_client_id', '=', vals.get('sap_client_id')),
                                                                      ('po_reference', '=', vals.get('po_ref'))],
                                                                     limit=1)
            if po_delivery[:1]:
                vals.update({
                    'po_delivery_id': po_delivery.id,
                    'po_id': po_delivery.po_id and po_delivery.po_id.id or False
                })
        if vals.get('sap_client_id') and vals.get('po_ref') and vals.get('po_line_code'):
            product_line = self.env['purchase.order.line'].sudo().search(
                [('po_line_code', '=', vals.get('po_line_code')),
                 ('po_number', '=', vals.get('po_ref')),
                 ('sap_client_id', '=', vals.get('sap_client_id'))], limit=1)
            if product_line[:1]:
                vals.update({
                    'product_line_id': product_line.id,
                    'product_id': product_line.product_id and product_line.product_id.id or False,
                    'product_uom': product_line.product_uom and product_line.product_uom.id or False
                })
        return super(PODeliveryProductLine, self).create(vals)


class POInvoicesAndPayments(models.Model):
    _name = "po.invoices.and.payments"
    _description = "PO Invoices and Payments Line"
    _rec_name = "si_no"

    si_no = fields.Char('SI No.', required=True)
    si_date = fields.Date('SI Date', default=fields.Date.today())
    si_amount = fields.Float('SI Amount')
    edts_ref_no = fields.Char('EDTS Reference No.')
    amount_released = fields.Float('Amount Released')
    or_number = fields.Char('OR No.')
    po_id = fields.Many2one('purchase.order', string='PO #')
    product_line = fields.One2many('po.invoices.and.payments.product.line', 'po_inv_payment_id', string='Product Lines')


class POInvoicesAndPaymentsLine(models.Model):
    _name = "po.invoices.and.payments.product.line"
    _description = "PO Invoices and Payments Product Line"

    name = fields.Char(string="Description")
    po_inv_payment_id = fields.Many2one('po.invoices.and.payments', string='SI No.')
    po_id = fields.Many2one('purchase.order', string='PO No.')
    product_line_id = fields.Many2one('purchase.order.line', string='Product', required=True)
    si_amount = fields.Float(string='SI Amount')
    sequence = fields.Integer(string='Sequence', default=10)

    @api.onchange('product_line_id')
    def _onchange_type(self):
        self.name = self.product_line_id.name
        self.si_amount = self.product_line_id.price_unit

    @api.onchange('si_amount')
    def _onchange_si_amount(self):
        if self.product_line_id and self.product_line_id.price_unit < self.si_amount:
            raise Warning("SI amount should not be greater than PO product price.")


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    code = fields.Char(string="Code")
    company_code = fields.Char(string="Company Code")

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

    @api.model
    def create(self, values):
        res = super(AccountPaymentTerm, self).create(values)
        if res:
            res.onchange_company_code()
        return res
