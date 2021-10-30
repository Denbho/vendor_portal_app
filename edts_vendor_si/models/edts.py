# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EdtsInfoInherit(models.Model):
    _inherit = 'edts.info'

    admin_sales_invoice_id = fields.Many2one('admin.sales.invoice', string='Vendor SI', ondelete='cascade', readonly=True)