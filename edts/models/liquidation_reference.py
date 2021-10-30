# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class LiquidationReference(models.Model):
    _name = 'edts.liquidation.reference'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EDTS Liquidation Reference'
    _order = 'id desc'

    name = fields.Char(string='Liquidation Reference', readonly=True)
    account_move_id = fields.Many2one('account.move', string='EDTS NO.', auto_join=True, ondelete='cascade', readonly=True)
    status = fields.Selection([('draft', 'Draft'),
                              ('waiting_for_head', 'Waiting for Head Approval'),
                              ('waiting_for_accounting', 'Waiting for Accounting Validation'),
                              ('validated', 'Validated'),
                              ('cancelled', 'Cancelled')], string="Status",
                             default='draft', readonly=True, track_visibility="always")
    liquidation_status = fields.Selection([
        ('unliquidated', 'Unliquidated'),
        ('partially_liquidated', 'Partially Liquidated'),
        ('fully_liquidated', 'Fully Liquidated'),
    ], string='Liquidation Status', default='unliquidated', tracking=True)
    submission_status = fields.Selection([
        ('pending_for_submission', 'Pending For Submission'),
        ('partially_submitted', 'Partially Submitted'),
        ('fully_submitted', 'Fully Submitted'),
    ], string='Submission Status', default='pending_for_submission', tracking=True)
    # Used in search view for groupings
    edts_subtype = fields.Selection([
        ('invoice_wo_po', 'Invoice w/o PO'),
        ('invoice_w_po', 'Invoice w/ PO'),
        ('advance_payment', 'Advance Payment'),
        ('rawland_acquisition', 'Rawland Acquisition'),
        ('reimbursement', 'Reimbursement'),
        ('cash_advance', 'Cash Advance'),
        ('stl', 'STL'),
        ('techserv_liaison', 'Techserv/Liaison'),
        ('setup', 'Setup'),
        ('return', 'Return'),
        ('agency_contracts_accruals', 'Agency Contracts Accruals'),
        ('agency_contracts_monthly', 'Agency Contracts Monthly'),
        ('recurring_transactions_accruals', 'Recurring Transactions Accruals'),
        ('recurring_transactions_monthly', 'Recurring Transactions Monthly'),
    ], string='EDTS Subtype', default=False)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    company_code = fields.Char(string='Company Code', related='company_id.code')
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    requestor = fields.Many2one('res.users', string='Name of Requestor', readonly=True)
    request_date = fields.Date(string='Request Date', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary(string='Amount', currency_field='currency_id', readonly=True)
    description = fields.Text(string='Description')

    overage_shortage = fields.Monetary(string='Overage/Shortage', compute='_compute_overage_shortage', currency_field='currency_id', readonly=True)
    or_number_overage = fields.Char(string='OR number for Overage')
    voucher_reference_shortage = fields.Char(string='Voucher Reference for Shortage')

    submitted_by = fields.Many2one('res.users', string='Submitted By', readonly=True)
    submitted_date = fields.Datetime(string='Submitted Date', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    validated_by = fields.Many2one('res.users', string='Validated By', readonly=True)
    validated_date = fields.Datetime(string='Validated Date', readonly=True)
    received_by = fields.Many2one('res.users', string='Received By', readonly=True)
    received_date = fields.Datetime(string='Received Date', readonly=True)
    audited_by = fields.Many2one('res.users', string='Audited By', readonly=True)
    audited_date = fields.Datetime(string='Audited Date', readonly=True)

    open_house_total_amount = fields.Monetary(string='Total Open House', currency_field='currency_id', compute='_compute_open_house_total_amount')
    meeting_total_amount = fields.Monetary(string='Total Meetings', currency_field='currency_id', compute='_compute_meeting_total_amount')
    supplies_total_amount = fields.Monetary(string='Total Supplies', currency_field='currency_id', compute='_compute_supplies_total_amount')
    techserv_total_amount = fields.Monetary(string='Total Techserv', currency_field='currency_id', compute='_compute_techserv_total_amount')
    others_total_amount = fields.Monetary(string='Total Others', currency_field='currency_id', compute='_compute_others_total_amount')
    total_liquidated_amount = fields.Monetary(string='Total Liquidated Amount', currency_field='currency_id', compute='_compute_total_liquidated_amount')

    liquidation_reference_line_ids = fields.One2many('edts.liquidation.reference.line', 'liquidation_reference_id', string='Liquidation Lines')
    total_liquidation_lines = fields.Integer(compute='_compute_total_liquidation_lines')

    dept_head_signature = fields.Binary(string="Department Head's Signature")
    accounting_signature = fields.Binary(string="Accounting Department's Signature")

    @api.model
    def create(self, vals):
        record = super(LiquidationReference, self).create(vals)
        record.name = '(* %s)' %record.id
        return record

    def _compute_total_liquidation_lines(self):
        for record in self:
            record.total_liquidation_lines = self.env['edts.liquidation.reference.line'].sudo().search_count([('liquidation_reference_id', '=', record.id)])

    def _compute_total_liquidated_amount(self):
        for record in self:
            record.total_liquidated_amount = 0
            for line in record.liquidation_reference_line_ids:
                record.total_liquidated_amount += line.gross_amount

    def _compute_overage_shortage(self):
        for record in self:
            record.overage_shortage = 0
            if record.amount and record.total_liquidated_amount:
                record.overage_shortage = record.amount - record.total_liquidated_amount

    def submit_request(self):
        self.status = 'waiting_for_head'
        self.name = self.generate_liquidation_reference()
        self.submitted_by = self._uid
        self.submitted_date = datetime.now()

    def approve_request(self):
        view_id = self.env.ref('edts.signature_wizard_form').id
        return {
            'name': 'Approve Liquidation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.signature.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_liquidation_reference_id': self.id,
                'default_action': 'approve'
            }
        }

    def validate_request(self):
        view_id = self.env.ref('edts.signature_wizard_form').id
        return {
            'name': 'Validate Liquidation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.signature.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_liquidation_reference_id': self.id,
                'default_action': 'validate'
            }
        }

    def recall_request(self):
        self.status = 'draft'
        self.set_unliquidated_status()
        self.set_pending_for_submission_status()

    def cancel_request(self):
        self.status = 'cancelled'
        self.set_unliquidated_status()
        self.set_pending_for_submission_status()

    def update_liquidation_status(self):
        view_id = self.env.ref('edts.update_liquidation_status_form').id

        return {
            'name': 'Update Liquidation Status',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'edts.liquidation.reference.wizard',
            'target': 'new',
            'context': {
                'default_liquidation_reference_id': self.id
            }
        }

    def update_submission_status(self):
        view_id = self.env.ref('edts.update_submission_status_form').id

        return {
            'name': 'Update Liquidation Status',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'edts.liquidation.reference.wizard',
            'target': 'new',
            'context': {
                'default_liquidation_reference_id': self.id
            }
        }

    def generate_liquidation_reference(self):
        name = self.name
        if '*' in self.name:
            name = '%s-%s-%s-%s' % (datetime.now().year, str(datetime.now().month).zfill(2), self.company_code, str(self.id).zfill(6))
        return name

    def set_unliquidated_status(self):
        self.liquidation_status = 'unliquidated'

    def set_pending_for_submission_status(self):
        self.submission_status = 'pending_for_submission'


class LiquidationReferenceLine(models.Model):
    _name = 'edts.liquidation.reference.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EDTS Liquidation Reference Line'
    _rec_name = 'invoice_doc_number'
    _order = 'id desc'

    liquidation_reference_id = fields.Many2one('edts.liquidation.reference', string='Liquidation Reference', auto_join=True, ondelete='cascade', readonly=True)
    liquidation_reference_status = fields.Selection(string='Liquidation Reference Status', related='liquidation_reference_id.status')
    invoice_doc_number = fields.Char(string='Invoice Document #')
    or_number = fields.Char(string='OR No.')
    or_date = fields.Date(string='OR Date')
    tin = fields.Char(string='TIN')
    payee = fields.Char(string='Payee')
    currency_id = fields.Many2one('res.currency', string='Currency')
    vat_sales = fields.Monetary(string='Vatable Amount', currency_field='currency_id')
    input_tax = fields.Monetary(string='Input Tax', currency_field='currency_id')
    gross_amount = fields.Monetary(string='Gross Amount', currency_field='currency_id')
    liquidation_type_id = fields.Many2one('edts.liquidation.reference.line.type', string='Type')
    description = fields.Text(string='Description')

    @api.onchange('vat_sales', 'input_tax')
    def onchange_edts_compute_gross_amount(self):
        for record in self:
            if record.vat_sales or record.input_tax:
                record.gross_amount = record.vat_sales + record.input_tax

    def view_liquidation_line(self):
        view_id = self.env.ref('edts.liquidation_reference_line_form').id

        return {
            'name': 'Liquidation Lines',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'edts.liquidation.reference.line',
            'res_id': self.id,
            'target': 'current',
        }


class LiquidationReferenceLineType(models.Model):
    _name = 'edts.liquidation.reference.line.type'
    _description = 'EDTS Liquidation Reference Line Type'
    _order = 'sequence, id'

    name = fields.Char(string='Name')
    sequence = fields.Integer(default=10)
