# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning

_STATES = [
    ('unreleased', 'Unreleased'),
    ('partially_released', 'Partially Released'),
    ('released', 'Released')
]

_SOURCING = [
    ('bidding', 'Bidding'),
    ('rfq', 'RFQ'),
    ('rfp', 'RFP'),
]

_RELEASE_INDICATOR = [
    ('unreleased', 'Unreleased'),
    ('released', 'Released')
]

_PR_TO_RFQ_ACTION_TYPE = [
    ('create', 'Create new RFQ'),
    ('append', 'Append to Existing RFQ')
]


class AdminPurchaseRequisition(models.Model):
    _name = "admin.purchase.requisition"
    _description = "Admin Purchase Requisition"
    _order = 'id desc'

    def _compute_material_count(self):
        for record in self:
            record.material_count = len([line.id for line in record.pr_line])

    name = fields.Char(string='PR No.', required=True, copy=False, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', 'Company', index=True,
                                 default=lambda self: self.env.company)
    company_code = fields.Char(string='Company Code')
    pr_doc_type_id = fields.Many2one('pr.document.type', 'PR Document Type', domain="[('company_id','=',company_id)]")
    pr_doc_type_code = fields.Char(string='PR Document Type Code')
    warehouse_id = fields.Many2one('location.plant', 'Plant', domain="[('company_id','=',company_id)]")
    plant_code = fields.Char(string='Plant Code')
    pr_line = fields.One2many('purchase.requisition.material.details', 'request_id', string='Material Details Lines',
                              copy=True, auto_join=True)
    state = fields.Selection(selection=_STATES,
                             string='PR Status',
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='unreleased',
                             compute='_compute_release_indicator',
                             store=True)
    material_count = fields.Integer(compute='_compute_material_count', string='Material Count')
    requisitioner_id = fields.Many2one('purchase.requisitioner', string='Requisitioner')
    requisitioner_code = fields.Char(string='Requisitioner Code')
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the pr without removing it.")

    @api.depends('pr_line', 'pr_line.release_indicator')
    def _compute_release_indicator(self):
        for rec in self:
            status = 'unreleased'
            unreleased_ids = self.env['purchase.requisition.material.details'].search(
                [('request_id', '=', rec.id), ('release_indicator', '=', 'unreleased')])
            released_ids = self.env['purchase.requisition.material.details'].search(
                [('request_id', '=', rec.id), ('release_indicator', '=', 'released')])
            if unreleased_ids and released_ids:
                status = 'partially_released'
            elif released_ids and not unreleased_ids:
                status = 'released'
            rec.state = status

    @api.onchange('requisitioner_id')
    def onchange_requisitioner_id(self):
        if self.requisitioner_id:
            self.requisitioner_code = self.requisitioner_id.code

    @api.onchange('requisitioner_code')
    def onchange_requisitioner_code(self):
        if self.requisitioner_code:
            requisitioner_id = self.env['purchase.requisitioner'].sudo().search(
                [('code', '=', self.requisitioner_code)], limit=1)
            if requisitioner_id[:1]:
                self.requisitioner_id = requisitioner_id[0].id

    def action_view_materials(self):
        self.ensure_one()
        return {
            'name': _('PR Material Details'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.requisition.material.details',
            'domain': [('id', 'in', [line.id for line in self.pr_line])],
            'target': 'current',
        }

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

    @api.onchange('warehouse_id')
    def onchange_plant(self):
        if self.warehouse_id:
            self.plant_code = self.warehouse_id.code

    @api.onchange('plant_code')
    def onchange_plant_code(self):
        if self.plant_code:
            plant_id = self.env['location.plant'].sudo().search([('code', '=', self.plant_code)], limit=1)
            if plant_id[:1]:
                self.warehouse_id = plant_id[0].id

    @api.onchange('pr_doc_type_id')
    def onchange_pr_doc_type_id(self):
        if self.pr_doc_type_id:
            self.pr_doc_type_code = self.pr_doc_type_id.code

    @api.onchange('pr_doc_type_code')
    def onchange_pr_doc_type_code(self):
        if self.pr_doc_type_code:
            pr_doc_type_id = self.env['pr.document.type'].sudo().search([('code', '=', self.pr_doc_type_code)], limit=1)
            if pr_doc_type_id[:1]:
                self.pr_doc_type_id = pr_doc_type_id[0].id

    @api.model
    def create(self, vals):
        if vals.get('plant_code') and vals.get('sap_client_id'):
            plant = self.env['location.plant'].sudo().search([('code', '=', vals.get('plant_code')), ('sap_client_id', '=', vals.get('sap_client_id'))], limit=1)
            if plant[:1]:
                vals.update({
                    'warehouse_id': plant.id,
                    'company_id': plant.company_id.id
                })
                if vals.get('pr_doc_type_code'):
                    pr_doc_type = self.env['pr.document.type'].sudo().search([('code', '=', vals.get('pr_doc_type_code')), ('company_id', '=', plant.company_id.id)], limit=1)
                    vals['pr_doc_type_id'] = pr_doc_type.id
                if vals.get('requisitioner_code'):
                    requisitioner = self.env['purchase.requisitioner'].sudo().search(
                        [('code', '=', vals.get('requisitioner_code'))], limit=1)
                    vals['requisitioner_id'] = requisitioner[:1] and requisitioner.id or False
        return super(AdminPurchaseRequisition, self).create(vals)

    def write(self, vals):
        if 'requisitioner_code' in vals:
            if vals.get('requisitioner_code'):
                requisitioner = self.env['purchase.requisitioner'].sudo().search(
                    [('code', '=', vals.get('requisitioner_code'))], limit=1)
                vals['requisitioner_id'] = requisitioner[:1] and requisitioner.id or False
            else:
                vals['requisitioner_id'] = False
        if 'pr_doc_type_code' in vals:
            if vals.get('pr_doc_type_code'):
                pr_doc_type = self.env['pr.document.type'].sudo().search(
                    [('code', '=', vals.get('pr_doc_type_code')), ('company_id', '=', plant.company_id.id)], limit=1)
                vals['pr_doc_type_id'] = pr_doc_type.id
            else:
                vals['pr_doc_type_id'] = False
        return super(AdminPurchaseRequisition, self).write(vals)

    def button_rfq(self):
        self.ensure_one()
        rfq_count = 0
        rfq_product_lines = []
        for line in self.pr_line:
            if line.sourcing == "rfq":
                rfq_count += 1
                if not line.rfq_line_id:
                    rfq_product_lines.append(line.id)
        if rfq_count >= 1:
            if rfq_product_lines:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('PR to RFQ'),
                    'res_model': 'admin.pr.to.rfq',
                    'target': 'new',
                    'view_mode': 'form',
                }
            else:
                raise Warning("Material details with RFQ sourcing are already made/exist in RFQ.")
        else:
            raise Warning("There is no RFQ sourcing found in material details.")

    def action_view_material_details_pivot(self):
        self.ensure_one()
        return {
            'name': _('Material Details'),
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'res_model': 'purchase.requisition.material.details',
            'domain': [('request_id', '=', self.id)],
            'target': 'current',
        }


class PurchaseRequisitionMaterialDetails(models.Model):
    _name = 'purchase.requisition.material.details'
    _description = 'Purchase Requisition Material Details'
    _order = 'id'
    _rec_name = 'product_id'

    request_id = fields.Many2one('admin.purchase.requisition', string='PR No.', ondelete='cascade')
    request_id_name = fields.Char(string="PR Ref.")
    company_id = fields.Many2one('res.company', string='Company')
    company_code = fields.Char(string='Company Code')
    product_id = fields.Many2one('product.product', string='Material')
    categ_id_code = fields.Char(string="Material Group Code", required=False, )
    product_categ_id = fields.Many2one('product.category', string='Material Group')
    material_description = fields.Text(string='Material Description')
    material_code = fields.Char(string='Material Code / SKU')
    latest_price = fields.Text(string='Latest Price')
    acct_assignment_categ = fields.Many2one('acct.assignment.category', string='Acct. Assignment Category')
    acct_assignment_categ_code = fields.Char(string='Acct. Assignment Category Code')
    product_uom_code = fields.Char(string="UoM Code", required=False)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    quantity = fields.Float(string="Material Quantity", default=1)
    release_indicator = fields.Selection(selection=_RELEASE_INDICATOR, string='Release Indicator', default='unreleased')
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center')
    cost_center_code = fields.Char(string="Cost Center Code", required=False, )
    warehouse_id = fields.Many2one('location.plant', 'Plant', domain="[('company_id','=',company_id)]")
    plant_code = fields.Char(string='Plant Code')
    location = fields.Many2one('stock.location', string='Storage Location',
                               domain="[('company_id','=',company_id), ('plant_id', '=', warehouse_id)]")
    location_code = fields.Char(string='Storage Location Code')
    target_delivery_date = fields.Date(string="Target Delivery Date")
    requisitioner_id = fields.Many2one('purchase.requisitioner', string='Requisitioner')
    requisitioner_code = fields.Char(string='Requisitioner Code')
    pr_releaser_id = fields.Many2one('res.partner', string='PR Releaser')
    asset_code = fields.Char(string='Asset Code')
    unloading_point = fields.Char(string='Unloading Point')
    purchasing_group_id = fields.Many2one('purchasing.group', string='Purchasing Group')
    purchasing_group_code = fields.Char(string='Purchasing Group Code')
    network = fields.Char(string='Network')
    internal_order = fields.Char(string='Internal Order')
    sourcing = fields.Selection(selection=_SOURCING, string='Sourcing')
    rfq_id = fields.Many2one('admin.request.for.quotation', string='RFQ No.')
    rfq_line_id = fields.Many2one('admin.request.for.quotation.line', string='RFQ Line')
    state = fields.Selection(selection=[('pending', 'Pending'), ('done', 'Done')], string='Status', default='pending')
    bom_price = fields.Float("BOM Price")
    market_price = fields.Float("Market Price")
    target_price = fields.Float("Target Price")
    pr_line_item_code = fields.Char("Item Code")
    po_code_reference = fields.Char("PO Reference")
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the PR line item without removing it.")

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

    @api.onchange('warehouse_id')
    def onchange_plant(self):
        if self.warehouse_id:
            self.plant_code = self.warehouse_id.code

    @api.onchange('plant_code')
    def onchange_plant_code(self):
        if self.plant_code:
            plant_id = self.env['location.plant'].sudo().search([('code', '=', self.plant_code)], limit=1)
            if plant_id[:1]:
                self.warehouse_id = plant_id[0].id

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

    @api.onchange('request_id')
    def onchange_request_id(self):
        if self.request_id:
            self.request_id_name = self.request_id.name

    @api.onchange('request_id_name')
    def onchange_request_id_name(self):
        if self.request_id_name:
            request_id = self.env['admin.purchase.requisition'].sudo().search(
                [('name', '=', self.request_id_name), ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if request_id[:1]:
                self.request_id = request_id.id

    @api.onchange('product_categ_id')
    def onchange_product_categ_id(self):
        if self.product_categ_id:
            self.categ_id_code = self.product_categ_id.code

    @api.onchange('categ_id_code')
    def onchange_categ_id_code(self):
        if self.categ_id_code:
            categ_id_code = self.env['product.category'].sudo().search([('code', '=', self.categ_id_code)], limit=1)
            if categ_id_code:
                self.product_categ_id = categ_id_code.id

    @api.onchange('cost_center_id')
    def onchange_cost_center_id(self):
        if self.cost_center_id:
            self.cost_center_code = self.cost_center_id.code

    @api.onchange('cost_center_code')
    def onchange_cost_center_code(self):
        if self.cost_center_code:
            cost_center_id = self.env['account.analytic.account'].sudo().search([('code', '=', self.cost_center_code)],
                                                                                limit=1)
            self.cost_center_id = cost_center_id.id

    @api.onchange('location')
    def onchange_location(self):
        if self.location:
            self.location_code = self.location.code

    @api.onchange('location_code')
    def onchange_location_code(self):
        if self.location_code:
            location_id = self.env['stock.location'].sudo().search([('code', '=', self.location_code)], limit=1)
            if location_id[:1]:
                self.location = location_id[0].id

    @api.onchange('acct_assignment_categ')
    def onchange_acct_assignment_categ(self):
        if self.acct_assignment_categ:
            self.acct_assignment_categ_code = self.acct_assignment_categ.code

    @api.onchange('acct_assignment_categ_code')
    def onchange_acct_assignment_categ_code(self):
        if self.acct_assignment_categ_code:
            acct_assignment_categ_id = self.env['acct.assignment.category'].sudo().search(
                [('code', '=', self.acct_assignment_categ_code)], limit=1)
            if acct_assignment_categ_id[:1]:
                self.acct_assignment_categ = acct_assignment_categ_id[0].id

    @api.onchange('requisitioner_id')
    def onchange_requisitioner_id(self):
        if self.requisitioner_id:
            self.requisitioner_code = self.requisitioner_id.code

    @api.onchange('requisitioner_code')
    def onchange_requisitioner_code(self):
        if self.requisitioner_code:
            requisitioner_id = self.env['purchase.requisitioner'].sudo().search(
                [('code', '=', self.requisitioner_code)], limit=1)
            if requisitioner_id[:1]:
                self.requisitioner_id = requisitioner_id[0].id

    @api.onchange('purchasing_group_id')
    def onchange_purchasing_group_id(self):
        if self.purchasing_group_id:
            self.purchasing_group_code = self.purchasing_group_id.code

    @api.onchange('purchasing_group_code')
    def onchange_purchasing_group_code(self):
        if self.purchasing_group_code:
            purchasing_group_id = self.env['purchasing.group'].sudo().search(
                [('code', '=', self.purchasing_group_code)], limit=1)
            if purchasing_group_id[:1]:
                self.purchasing_group_id = purchasing_group_id[0].id

    @api.model
    def create(self, vals):
        if vals.get('request_id_name') and vals.get('sap_client_id'):
            request_id = self.env['admin.purchase.requisition'].sudo().search(
                [('name', '=', vals.get('request_id_name')), ('sap_client_id', '=', vals.get('sap_client_id'))],
                limit=1)
            if request_id[:1]:
                vals.update({
                    'request_id': request_id.id,
                    'company_id': request_id.company_id.id,
                    'warehouse_id': request_id.warehouse_id and request_id.warehouse_id.id or False,
                    'requisitioner_id': request_id.requisitioner_id and request_id.requisitioner_id.id or False
                })
            else:
                plant_id = self.env['location.plant'].sudo().search(
                    [('code', '=', vals.get('plant_code')), ('sap_client_id', '=', vals.get('sap_client_id'))], limit=1)
                if plant_id[:1]:
                    vals.update({
                        'warehouse_id': plant_id.id,
                        'company_id': plant_id.company_id.id,
                    })
                if vals.get('requisitioner_code'):
                    requisitioner_id = self.env['purchase.requisitioner'].sudo().search(
                        [('code', '=', vals.get('requisitioner_code'))], limit=1)
                    vals['requisitioner_id'] = requisitioner_id[:1] and requisitioner_id.id or False
            if vals.get('location_code'):
                location_query = [('code', '=', vals.get('location_code'))]
                if request_id[:1]:
                    location_query.append(('plant_id', '=', request_id.warehouse_id.id))
                else:
                    location_query.append(('plant_id', '=', plant_id.id))
                location_id = self.env['stock.location'].sudo().search(location_query, limit=1)
                vals['location'] = location_id[:1] and location_id.id or False
            if vals.get('material_code'):
                product_id = self.env['product.product'].sudo().search([('default_code', '=', vals.get('material_code'))],
                                                                       limit=1)
                if product_id[:1]:
                    vals.update({
                        'product_id': product_id.id,
                        'product_categ_id': product_id.categ_id.id
                    })
                if product_id[:1] and product_id.product_uom_code == vals.get('product_uom_code') and product_id.uom_id:
                    vals['product_uom'] = product_id.uom_id.id
                elif product_id[:1] and product_id.po_uom_code == vals.get('product_uom_code') and product_id.uom_po_id:
                    vals['product_uom'] = product_id.uom_po_id.id
                elif vals.get('product_uom_code'):
                    product_uom = self.env['uom.uom'].sudo().search([('code', '=', vals.get('product_uom_code'))], limit=1)
                    vals['product_uom'] = product_uom.id
            if vals.get('acct_assignment_categ_code'):
                acct_assignment_categ = self.env['acct.assignment.category'].sudo().search(
                    [('code', '=', vals.get('acct_assignment_categ_code'))], limit=1)
                vals['acct_assignment_categ'] = acct_assignment_categ[:1] and acct_assignment_categ.id or False
            if vals.get('requisitioner_code'):
                requisitioner = self.env['purchase.requisitioner'].sudo().search(
                    [('code', '=', vals.get('requisitioner_code'))], limit=1)
                vals['requisitioner_id'] = requisitioner[:1] and requisitioner.id or False
            if vals.get('cost_center_code'):
                cost_center = self.env['account.analytic.account'].sudo().search(
                    [('code', '=', vals.get('cost_center_code'))],
                    limit=1)
                vals['cost_center_id'] = cost_center[:1] and cost_center.id or False
            if vals.get('purchasing_group_code'):
                purchasing_group = self.env['purchasing.group'].sudo().search(
                    [('code', '=', vals.get('purchasing_group_code'))], limit=1)
                vals['purchasing_group_id'] = purchasing_group[:1] and purchasing_group.id or False
        return super(PurchaseRequisitionMaterialDetails, self).create(vals)

    @api.onchange('material_code')
    def onchange_material_code(self):
        if self.material_code:
            product_id = self.env['product.product'].sudo().search([('default_code', '=', self.material_code)], limit=1)
            if product_id[:1]:
                self.product_id = product_id[0].id

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            self.material_description = self.product_id.description_purchase
            self.material_code = self.product_id.default_code
            self.product_categ_id = self.product_id.categ_id and self.product_id.categ_id.id or False
            self.product_uom = self.product_id.uom_po_id and self.product_id.uom_po_id.id or False
            line_values = ""
            line_cnt = 0
            br = "<br/>"
            for line in self.product_id.seller_ids:
                if line_cnt < 3:
                    line_values = line_values + "<b>Vendor: </b>" + line.name.name
                    if line.product_name:
                        line_values = line_values + br + "<b>Vendor Product Name: </b>" + line.product_name
                    if line.product_code:
                        line_values = line_values + br + "<b>Vendor Product Code: </b>" + line.product_code
                    if line.delay >= 1:
                        line_values = line_values + br + "<b>Delivery Lead Time: </b>" + str(line.delay) + " day(s)"
                    line_values = line_values + br + "<b>Quantity: </b>" + str(
                        line.min_qty) + " " + line.product_uom.name
                    line_values = line_values + br + "<b>Price: </b>" + str(line.price)
                    if line.date_start:
                        line_values = line_values + br + "<b>Validity: </b>" + str(line.date_start) + " to " + str(
                            line.date_end)
                    line_values = line_values + br + br
                line_cnt += 1
            self.latest_price = line_values


class AcctAssignmentCategory(models.Model):
    _name = 'acct.assignment.category'
    _description = 'Acct. Assignment Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)


class PurchaseRequisitioner(models.Model):
    _name = 'purchase.requisitioner'
    _description = 'Requisitioner'
    _order = 'name'

    name = fields.Char(string='Department Group', required=True)
    code = fields.Char(string='Code', required=True)


class PurchasingGroup(models.Model):
    _name = 'purchasing.group'
    _description = 'Purchasing Group'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)


class AdminPRtoRFQ(models.TransientModel):
    _name = "admin.pr.to.rfq"
    _description = "Admin PR to RFQ"

    def _get_pr_materials_line(self):
        context = self.env.context
        pr_data = self.env['admin.purchase.requisition'].browse(context['active_id'])
        res = []
        for line in pr_data.pr_line:
            if line.sourcing == "rfq" and not line.rfq_line_id:
                res.append((0, 0, {
                    'pr_material_line_id': line.id,
                    'product_id': line.product_id and line.product_id.id or False,
                    'quantity': line.quantity,
                    'location': line.location and line.location.id or False,
                    'bom_price': line.bom_price,
                    'market_price': line.market_price,
                    'target_price': line.target_price,
                }))
        return res

    type = fields.Selection(selection=_PR_TO_RFQ_ACTION_TYPE, string='Type of Action', default='create', required=True)
    rfq_id = fields.Many2one('admin.request.for.quotation', string='RFQ Ref.')
    pr_materials_line = fields.One2many('admin.pr.to.rfq.line', 'pr_to_rfq_id', string='Materials Line',
                                        default=_get_pr_materials_line)
    vendor_ids = fields.Many2many('res.partner', 'pr_to_rfq_rel', string="Vendors")

    def view_rfq_form(self, rfq_id):
        template_id = self.env['ir.model.data'].get_object_reference('admin_request_for_quotation',
                                                                     'admin_request_for_quotation_view_form')[1]
        ctx = dict(self.env.context or {})
        ctx.update({
            'form_view_initial_mode': 'edit',
            'force_detailed_view': 'true'
        })
        return {
            'name': 'Vendor RFQ',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': template_id,
            'res_id': rfq_id,
            'res_model': 'admin.request.for.quotation',
            'context': ctx,
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def button_create_rfq(self):
        rfq_product_lines = []
        context = self.env.context
        pr_data = self.env['admin.purchase.requisition'].browse(context['active_id'])
        new_vendor_ids = [[6, False, [l for l in self.vendor_ids.ids]]]
        for line in self.pr_materials_line:
            if line.pr_material_line_id.sourcing == "rfq" and not line.pr_material_line_id.rfq_line_id:
                rfq_product_lines.append(
                    {
                        'product_id': line.product_id.id,
                        'default_product_code': line.pr_material_line_id.material_code,
                        'product_description': line.pr_material_line_id.material_description or line.product_id.name,
                        'prod_qty': line.quantity,
                        'product_uom': line.pr_material_line_id.product_uom.id,
                        'stock_location_id': line.location and line.location.id or False,
                        'pr_line_id': line.pr_material_line_id.id,
                        'bom_price': line.bom_price,
                        'market_price': line.market_price,
                        'target_price': line.target_price,
                        'vendor_ids': new_vendor_ids,
                    })
        new_rfq_id = self.env['admin.request.for.quotation'].create({
            'vendor_ids': new_vendor_ids,
            'company_code': pr_data.company_code,
            'company_id': pr_data.company_id and pr_data.company_id.id or False,
            'vendor_ids': new_vendor_ids,
        })
        for ln in rfq_product_lines:
            ln['rfq_id'] = new_rfq_id.id
            pr_line_entry = self.env['purchase.requisition.material.details'].browse(ln['pr_line_id'])
            ln.pop('pr_line_id', None)
            # Create RFQ materials line
            new_rfq_line_id = self.env['admin.request.for.quotation.line'].create(ln)
            # Create company related material RFQ
            self.env['admin.request.for.quotation.company.qty'].create({
                'pr_id': pr_data.id,
                'rfq_line_id': new_rfq_line_id.id,
                'company_id': pr_data.company_id.id,
                'product_id': ln['product_id'],
                'qty': ln['prod_qty'],
                'product_uom': ln['product_uom']
            })
            pr_line_entry.write({'rfq_line_id': new_rfq_line_id.id, 'rfq_id': new_rfq_id.id})
        return self.view_rfq_form(new_rfq_id.id)

    def button_append_to_existing_rfq(self):
        rfq_product_lines = []
        context = self.env.context
        pr_data = self.env['admin.purchase.requisition'].browse(context['active_id'])
        rfq_line_obj = self.env['admin.request.for.quotation.line']
        new_vendor_ids = [[6, False, [l for l in self.rfq_id.vendor_ids.ids]]]
        for line in self.pr_materials_line:
            if line.pr_material_line_id.sourcing == "rfq" and not line.pr_material_line_id.rfq_line_id:
                location_id = line.location and line.location.id or False
                rfq_line_existing = rfq_line_obj.search([('product_id', '=', line.product_id.id),
                                                         ('stock_location_id', '=', location_id),
                                                         ('rfq_id', '=', self.rfq_id.id)], limit=1)
                line_id = False
                if rfq_line_existing:
                    rfq_line_existing[0].write({'prod_qty': rfq_line_existing.prod_qty + line.quantity})
                    line_id = rfq_line_existing.id
                else:
                    # Ceate new RFQ product/material line.
                    new_rfq_line_id = rfq_line_obj.create({
                        'product_id': line.product_id.id,
                        'default_product_code': line.pr_material_line_id.material_code,
                        'product_description': line.pr_material_line_id.material_description or line.product_id.name,
                        'prod_qty': line.quantity,
                        'product_uom': line.pr_material_line_id.product_uom.id,
                        'stock_location_id': location_id,
                        'rfq_id': self.rfq_id.id,
                        'bom_price': line.bom_price,
                        'market_price': line.market_price,
                        'target_price': line.target_price,
                        'vendor_ids': new_vendor_ids,
                    })
                    line_id = new_rfq_line_id.id
                # Create company related material RFQ
                self.env['admin.request.for.quotation.company.qty'].create({
                    'pr_id': pr_data.id,
                    'rfq_line_id': line_id,
                    'company_id': pr_data.company_id.id,
                    'product_id': line.product_id.id,
                    'qty': line.quantity,
                    'product_uom': line.pr_material_line_id.product_uom.id
                })
                line.pr_material_line_id.write({'rfq_line_id': line_id, 'rfq_id': self.rfq_id.id})
        return self.view_rfq_form(self.rfq_id.id)


class AdminPRtoRFQLine(models.TransientModel):
    _name = "admin.pr.to.rfq.line"
    _description = "Admin PR to RFQ Line"

    pr_to_rfq_id = fields.Many2one('admin.pr.to.rfq', string='PR to RFQ ID')
    pr_material_line_id = fields.Many2one('purchase.requisition.material.details', 'Material Line ID')
    product_id = fields.Many2one('product.product', 'Material')
    quantity = fields.Float('Quantity')
    location = fields.Many2one('stock.location', string='Storage Location')
    vendor_partner_ids = fields.Many2many('res.partner', 'admin_vendor_pr_to_rfq_line_rel', string="Vendors")
    bom_price = fields.Float("BOM Price")
    market_price = fields.Float("Market Price")
    target_price = fields.Float("Target Price")
