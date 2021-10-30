from odoo import fields, models, api
import re

_PROCESSING_STATUS = [
    ('without_po', 'Without PO'),
    ('partially_po', 'Partially PO'),
    ('fully_po', 'Fully PO'),
    ('over_po', 'Over PO')
]

class AdminPurchaseRequisition(models.Model):
    _inherit = "admin.purchase.requisition"

    processing_status = fields.Selection(selection=_PROCESSING_STATUS,
                             string='Processing Status',
                             copy=False,
                             default='without_po',
                             compute="_get_processing_status",
                             store=True)

    @api.depends('pr_line', 'pr_line.processing_status')
    def _get_processing_status(self):
        pr_line_obj = self.env['purchase.requisition.material.details']
        for rec in self:
            processing_status = 'without_po'
            partially_po_lines = pr_line_obj.sudo().search([
                                                        ('request_id', '=', rec.id),
                                                        ('processing_status','=','partially_po')], limit=1)
            fully_po_lines = pr_line_obj.sudo().search([
                                                        ('request_id', '=', rec.id),
                                                        ('processing_status','=','fully_po')], limit=1)
            without_po_lines = pr_line_obj.sudo().search([
                                                        ('request_id', '=', rec.id),
                                                        ('processing_status','=','without_po')], limit=1)
            if without_po_lines:
                if partially_po_lines or fully_po_lines:
                    processing_status = 'partially_po'
            else:
                if partially_po_lines:
                    processing_status = 'partially_po'
                elif fully_po_lines and not partially_po_lines:
                    processing_status = 'fully_po'
            rec.processing_status = processing_status

    def update_po_processing_status_per_line(self):
        for pr in self:
            for r in pr.pr_line:
                r.sudo().update_po_processing_status()


class PurchaseRequisitionMaterialDetails(models.Model):
    _inherit = 'purchase.requisition.material.details'

    processing_status = fields.Selection(selection=_PROCESSING_STATUS,
                             string='Processing Status', copy=False,
                             default='without_po')
    purchase_order_line_ids = fields.Many2many("purchase.order.line", 'pr_line_po_line_rel',
                                               compute="_get_po_line_related")

    def update_po_processing_status(self):
        if self.request_id:
            po_lines = self.env['purchase.order.line'].sudo().search([
                    ('sap_client_id', '=', self.sap_client_id),
                    ('pr_references', '=', self.request_id.name),
                    ('pr_line_item_code', '=', self.pr_line_item_code),
                    ('material_code', '=', self.material_code),
                    ('order_id.state', 'in', ['purchase', 'done'])
                  ])
            po_qty = po_lines[:1] and sum(line.product_qty for line in po_lines) or 0
            processing_status = 'without_po'
            if po_qty > self.quantity:
                processing_status = 'over_po'
            elif po_qty == self.quantity:
                processing_status = 'fully_po'
            elif self.quantity > po_qty >= 1:
                processing_status = 'partially_po'
            self.sudo().write({'processing_status': processing_status})

    def _get_po_line_related(self):
        po_line_obj = self.env['purchase.order.line']
        for r in self:
            r.purchase_order_line_ids = []
            if r.request_id and r.company_id and r.material_code:
                po_lines = po_line_obj.sudo().search([
                    ('company_id', '=', r.company_id.id),
                    ('product_id.default_code', '=', r.material_code),
                    ('pr_references', '=', r.request_id.name),
                    ('pr_line_item_code', '=', r.pr_line_item_code),
                    ('sap_client_id', '=', r.sap_client_id)
                ])
                po_line_ids = list()
                if po_lines[:1]:
                    for rec in po_lines:
                        pr_ref = re.split('; |, |\*|\n', rec.pr_references)
                        if r.request_id.name in pr_ref:
                            po_line_ids.append(rec.id)
                r.purchase_order_line_ids = po_line_ids

