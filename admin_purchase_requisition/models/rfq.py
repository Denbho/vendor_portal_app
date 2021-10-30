# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _

class AdminRequestForQuotationCompanyQty(models.Model):
    _inherit = 'admin.request.for.quotation.company.qty'

    pr_id = fields.Many2one('admin.purchase.requisition', 'PR No.')

    @api.onchange('pr_id')
    def onchange_pr_id(self):
        if self.pr_id:
            self.company_id = self.pr_id.company_id and self.pr_id.company_id.id or False
        else:
            self.company_id = False
