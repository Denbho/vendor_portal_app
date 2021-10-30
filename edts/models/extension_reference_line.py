# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ExtensionReferenceLine(models.Model):
    _name = 'edts.extension.reference.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EDTS Extension Reference Line'
    _order = 'id desc'

    account_move_id = fields.Many2one('account.move', string='EDTS Invoice', auto_join=True, ondelete='cascade', readonly=True)
    transaction_extended_date = fields.Datetime(string='Transaction was Extended', readonly=True)
    transaction_extended_by = fields.Many2one('res.users', string='Transaction Extended By', readonly=True)
    extension_reason_id = fields.Many2one('extension.reason', string='Extension Reason')
    extension_remarks = fields.Text(string='Extension Remarks')
    extension_child_recurring_ids = fields.Many2many(comodel_name='account.move', relation='edts_extension_reference_line_account_move_rel',
                                                     column1='edts_id', column2='recurring_id',
                                                     string='Extension Sub Recurring Record/s', readonly=True)

