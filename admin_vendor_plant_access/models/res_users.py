# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    plant_ids = fields.Many2many('location.plant', 'res_plant_users_rel', string='Plants')
