# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class modified_contacts(models.Model):
#     _name = 'modified_contacts.modified_contacts'
#     _description = 'modified_contacts.modified_contacts'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
