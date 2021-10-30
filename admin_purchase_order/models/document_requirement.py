# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _

class DocumentRequirements(models.Model):
    _name = "document.requirement"
    _description = "Documents"
    _order = "name asc"

    name = fields.Char(string="Name", required=True)
