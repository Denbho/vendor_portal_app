# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    code = fields.Char(string="Code")

    _sql_constraints = [
        ('company_code',
         'CHECK(code IS NOT NULL AND unique(code))',
         'The "Company Code" field  must have unique value per Sap Severs!')]




