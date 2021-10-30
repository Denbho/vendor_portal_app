# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'
    allow_renewal_days = fields.Integer(string='Allow Renewal Days')


class EdtsResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    allow_renewal_days = fields.Integer(related='company_id.allow_renewal_days', string='Allow renewal days', readonly=False)

