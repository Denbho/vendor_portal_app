# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class AdminBrand(models.Model):
    _name = "admin.brand"
    _description = "Admin Brand"

    name = fields.Char(string='Brand Name', required=True)
