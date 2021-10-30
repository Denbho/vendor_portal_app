# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    so_number = fields.Char('Property SO Number')
    property_sale_id = fields.Many2one('property.admin.sale',
                                       string="Property")
                                       
    @api.model
    def create(self, vals):
        if not vals.get('res_model_id') and vals.get('property_sale_id'):
            vals['res_model_id'] = self.env['ir.model'].sudo().search([('model', '=', 'property.admin.sale')], limit=1).id
            vals['res_id'] = vals.get('property_sale_id')
        return super(CalendarEvent, self).create(vals)
