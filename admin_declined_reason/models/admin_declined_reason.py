# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AdminDeclinedReason(models.Model):
    _name = 'admin.declined.reason'
    _description = 'Declined Reasons'

    name = fields.Char(string="Reason", required=True)
