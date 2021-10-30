# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AdminCancelAndHaltReason(models.Model):
    _name = 'admin.cancel.and.halt.reason'
    _description = 'Admin Cancel and Halt Reasons'

    name = fields.Char(string="Reason", required=True)
    description = fields.Text(string="Description")
