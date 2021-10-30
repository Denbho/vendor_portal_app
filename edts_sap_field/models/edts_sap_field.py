# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PODeliverylineInherit(models.Model):
    _inherit = 'po.delivery.line'

    invoice_doc_no = fields.Char(string='Invoice Document #', readonly=True)
    invoice_doc_status = fields.Char(string='Invoice Document Status', readonly=True)


class EdtsInfoInherit(models.Model):
    _inherit = 'edts.info'

    edts_invoice_doc_line_ids = fields.One2many('edts.invoice.doc.line', 'account_move_id', string='Invoice Doc Line')
    processed_by = fields.Char(string='Processed By')
    processed_date = fields.Date(string='Processed Date')


class EdtsInvoiceDocLine(models.Model):
    _name = 'edts.invoice.doc.line'
    _description = 'EDTS Invoice Document Line'
    _rec_name = 'invoice_doc_no'

    account_move_id = fields.Many2one('account.move', string='Account Move')
    invoice_doc_no = fields.Char(string='Invoice Document #')
    invoice_doc_status = fields.Char(string='Invoice Document Status')
