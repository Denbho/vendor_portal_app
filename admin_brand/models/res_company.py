# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    brand_id = fields.Many2one('admin.brand', string='Brand')
