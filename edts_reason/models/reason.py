# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EdtsReturnReason(models.Model):
    _name = 'return.reason'
    _description = 'Return Reason'
    _order = 'sequence, id'

    name = fields.Char(string='Name')
    sequence = fields.Integer(default=10)

class EdtsRejectReason(models.Model):
    _name = 'reject.reason'
    _description = 'Reject Reason'
    _order = 'sequence, id'

    name = fields.Char(string='Name')
    sequence = fields.Integer(default=10)

class EdtsExtensionReason(models.Model):
    _name = 'extension.reason'
    _description = 'Extension Reason'
    _order = 'sequence, id'

    name = fields.Char(string='Name')
    sequence = fields.Integer(default=10)