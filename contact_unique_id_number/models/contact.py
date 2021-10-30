# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_assign_number = fields.Char(string="Customer Number", help="Unique Customer Number")
    universal_assign_number = fields.Char(string="UCN", help="Universal Customer Number")
    supplier_number = fields.Char('Supplier No.', track_visibility="always")
