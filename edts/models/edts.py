# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning, ValidationError
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import http
import json

INTERNAL_LOOKUP_WARNING = 'EDTS Company Code not equal to Queried Company Code \n \n' \
                          'EDTS Company Code: %s \n' \
                          'Internal Order Company Code: %s \n'
ASSET_LOOKUP_WARNING = 'EDTS Company Code not equal to Queried Company Code \n \n' \
                       'EDTS Company Code: %s \n' \
                       'Asset Company Code: %s \n'
NO_DR_GR_WARNING = 'Please add atleast one (1) DR/GR record. Also, make sure that the DR/GR added is already countered.'
DR_GR_NOT_COUNTERED_WARNING = 'Please make sure that all DR/GR related to this EDTS has been tagged as Countered.'
NO_API_CONFIG_WARNING = 'Please check SETTINGS and provide appropriate API CONFIG.'
MONTHLY_PAYMENT_TERM_WARNING = 'If payment term is MONTHLY, MONTH DIFFERENCE for baseline dates must be AT LEAST A MONTH.\n' \
                              'Please CHANGE the BASELINE DATES or PAYMENT TERMS to compute AMOUNT correctly.'
QUARTERLY_PAYMENT_TERM_WARNING = 'If payment term is QUARTERLY, baseline dates must be divisible by 3.\n' \
                              'Please CHANGE the BASELINE DATES or PAYMENT TERMS to compute AMOUNT correctly.'
SEMI_ANNUAL_PAYMENT_TERM_WARNING = 'If payment term is SEMI-ANNUAL, baseline dates must be divisible by 6.\n' \
                              'Please CHANGE the BASELINE DATES or PAYMENT TERMS to compute AMOUNT correctly.'
ANNUAL_PAYMENT_TERM_WARNING = 'If payment term is ANNUALLY, YEAR DIFFERENCE for baseline dates must be AT LEAST A YEAR.\n' \
                              'Please CHANGE the BASELINE DATES or PAYMENT TERMS to compute AMOUNT correctly.'
VALID_FROM_DATE_WARNING = 'Please enter present to future dates.'
VALID_TO_DATE_WARNING = 'Please enter future dates that will cover at least a month based from your Valid From date.'
RUN_DAY_WARNING = 'Cannot enter RUN DAY equal to VALID FROM day'


class EdtsInfo(models.Model):
    _name = 'edts.info'
    _description = 'Electronic Document Tracking System Information'

    status = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_head', 'Waiting for Head Approval'),
        ('waiting_for_accounting', 'Waiting for Accounting Validation'),
        ('ongoing', 'Ongoing'),
        ('processing_accounting', 'Processing Accounting'),
        ('processing_finance', 'Processing Finance'),
        ('partial_payment_released', 'Partial Payment Released'),
        ('fully_paid', 'Fully Paid'),
        ('done', 'Done'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ], string="EDTS Status", default='draft', tracking=True)
    edts_status_label = fields.Char(string='EDTS Status Label', compute='_compute_edts_status_label')
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
    edts_subtype_label = fields.Char(string='EDTS Subtype Label', compute='_compute_edts_subtype_label')
    currency_id = fields.Many2one('res.currency', string='EDTS Currency')
    is_edts_field_readonly = fields.Boolean(string='Is EDTS Field Readonly', compute='_compute_is_edts_field_readonly')

    countered = fields.Boolean(string='Countered', tracking=True)
    countered_date = fields.Datetime(string='Countered Date/Time', readonly=True, tracking=True)
    countered_by = fields.Many2one('res.users', string='Countered By', readonly=True, tracking=True)
    countering_notes = fields.Text(string="Countering Notes", tracking=True)

    wizard_reason = fields.Char(string='Internal Note', tracking=True)
    returned_or_recalled = fields.Boolean(string='Was Returned or Recalled', default=False)

    request_date = fields.Date(string='Request Date', default=datetime.now().date(), readonly=True)
    reason = fields.Text(string='Purpose/Reason')
    company_code = fields.Char(string='Company Code')
    """Did not use company_id field in account.move to avoid conflict with odoo's original journal entry process"""
    edts_company_id = fields.Many2one('res.company', string='EDTS Company', default=lambda s: s.env.company)
    sap_client_id = fields.Integer(string="Client ID", related='edts_company_id.sap_client_id')
    balance = fields.Monetary(string='Balance', currency_field='currency_id')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    acquisition_cost = fields.Monetary(string='Acquisition Cost', digits=(12, 2), currency_field='currency_id')
    billed_amount = fields.Monetary(string='Billed Amount', currency_field='currency_id')
    approved_amount = fields.Monetary(string='Approved Amount', currency_field='currency_id')

    """Did not use purchase_id field in account.move to avoid conflict with odoo's original journal entry process"""
    edts_purchase_id = fields.Many2one('purchase.order', string='EDTS Purchase Order')
    internal_order = fields.Char(string='Internal Order')
    asset = fields.Char(string='Asset')
    property_admin_sale_id = fields.Many2one('property.admin.sale', string='Sales Order')
    wbs_element = fields.Char(string='WBS Element')
    cmc_type_id = fields.Many2one('edts.cmc.type', string='CMC Type')
    account_number = fields.Char(string='Account Number')
    employee_code = fields.Char(string='Employee Code')
    employee_id = fields.Many2one('res.partner', string='Employee')
    vendor_code_113 = fields.Char(string='Vendor Code 113')
    vendor_code_303 = fields.Char(string='Vendor Code 303')
    universal_vendor_code = fields.Char(string='Universal Vendor Code')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    rawland_owner_id = fields.Many2one('res.partner', string='Rawland Owner')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term')
    cash_journal_no = fields.Char(string='Cash Journal #')
    baseline_date = fields.Date(string='Baseline Date')
    invoice_type = fields.Selection([
        ('down_payment', 'Down payment'),
        ('retention_release', 'Retention Release'),
        ('progress_billing', 'Progress Billing')
    ], string='Down Retention Type', default=False)
    down_payment_percent = fields.Float(string='Down payment %')
    retention_release_percent = fields.Float(string='Retention Release %')
    baseline_start_date = fields.Date(string='Baseline Start Date')
    baseline_end_date = fields.Date(string='Baseline End Date')
    rawland_payment_terms = fields.Selection([
        ('due', 'Due Immediately'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annualy', 'Annualy'),
    ], string='Rawland Payment Terms', default='due')
    payee = fields.Char(string='Payee')
    accountable_person = fields.Char(string='Accountable Person')
    techserv_remarks = fields.Text(string='Remarks')
    department = fields.Char(string='Department')
    cost_center = fields.Char(string='Cost Center')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    run_day = fields.Integer(string='Run Day')

    posting_date = fields.Date(string='Posting Date', readonly=True)
    document_date = fields.Date(string='Document Date', readonly=True)
    doc_header = fields.Char(string='Document Header')
    assignment = fields.Char(string='Assignment')

    project_description = fields.Char(string='Project Description')
    profit_center_id = fields.Many2one('account.analytic.account', string='Profit Center')
    profit_center_code = fields.Char(string='Profit Center Code')

    fund_returned_date = fields.Datetime(string='Fund Returned Date/Time', readonly=True)
    fund_returned_by = fields.Many2one('res.users', string='Fund Returned By', readonly=True)

    payment_reference_ids = fields.One2many('edts.payment.reference.line', 'account_move_id', string='Payment References')
    total_payment_count = fields.Integer(compute='_compute_total_payment_count')
    need_released_count = fields.Integer(compute='_compute_need_release_count')
    need_encashed_count = fields.Integer(compute='_compute_need_encash_count')
    total_payment_amount = fields.Monetary(string='Total Payment Reference Amount', compute='_compute_total_payment_amount', currency_field='currency_id')
    total_payment_amount_display = fields.Char(string='Total Payment Reference Amount Display', compute='_compute_total_payment_amount_display')

    liquidation_reference_ids = fields.One2many('edts.liquidation.reference', 'account_move_id', string='Liquidation References')
    total_liquidation_count = fields.Integer(compute='_compute_total_liquidation_count')
    liquidation_status = fields.Selection([
        ('unliquidated', 'Unliquidated'),
        ('partially_liquidated', 'Partially Liquidated'),
        ('fully_liquidated', 'Fully Liquidated'),
    ], string='Liquidation Status', compute='_compute_liquidation_status', store=True, readonly=True)
    submission_status = fields.Selection([
        ('pending_for_submission', 'Pending For Submission'),
        ('partially_submitted', 'Partially Submitted'),
        ('fully_submitted', 'Fully Submitted'),
    ], string='Submission Status', compute='_compute_submission_status', store=True, readonly=True)

    is_recurring_invoice = fields.Boolean(string='Is Recurring Invoice', default=False)
    parent_recurring_id = fields.Many2one('account.move', string='Main Recurring Record', ondelete='cascade', readonly=True)
    child_recurring_ids = fields.Many2many(comodel_name='account.move', relation='edts_info_account_move_rel',
                                           column1='edts_id', column2='recurring_id',
                                           string='Recurring Invoice/s', readonly=True)
    old_renewal_id = fields.Many2one('account.move', string='Old Record', ondelete='cascade', readonly=True)
    new_renewal_id = fields.Many2one('account.move', string='Renewed record', ondelete='cascade', readonly=True)
    extension_reference_ids = fields.One2many('edts.extension.reference.line', 'account_move_id', string='Extension References')

    is_in_valid_renewal_date = fields.Boolean(string='Is In Valid Renewal Date', compute='_compute_is_in_valid_renewal_date')
    last_run_date = fields.Date(string='Last Run Date')

    sap_api_status = fields.Selection([
        ('posted_to_sap', 'Posted To SAP'),
        ('invoice_doc_received', 'Invoice Document # Received'),
        ('payment_doc_received', 'Payment Document # Received'),
        ('failed', 'Failed')
    ], string='SAP Status', default=False)
    edts_sap_remarks = fields.Text(string='POST EDTS to SAP')
    get_invoice_doc_remarks = fields.Text(string='GET Invoice Doc.')
    get_payment_doc_remarks = fields.Text(string='GET Payment Doc.')

    po_delivery_ids = fields.Many2many('po.delivery.line', 'edts_delivery_rel', string="Delivery Document")
    dept_head_signature = fields.Binary(string="Department Head's Signature")
    accounting_signature = fields.Binary(string="Accounting Department's Signature")

    approver = fields.Many2one('res.users', string='Approver', tracking=True)
    processor = fields.Many2one('res.users', string='Processor', tracking=True)
    requestor = fields.Many2one('res.users', string='Requestor', tracking=True)

    hide_transfer_btn = fields.Boolean(string='Hide Transfer', compute='_compute_hide_transfer_btn')
    hide_recall_btn = fields.Boolean(string='Hide Recall', compute='_compute_hide_recall_btn')
    hide_return_reject_btn = fields.Boolean(string='Hide Return Reject', compute='_compute_hide_return_reject_btn')

    is_requestor = fields.Boolean(string='Is Requestor', compute='_compute_is_requestor')
    is_processor = fields.Boolean(string='Is Processor', compute='_compute_is_processor')
    is_approver = fields.Boolean(string='Is Approver', compute='_compute_is_approver')

    @api.onchange('company_code')
    def onchange_edts_company_code(self):
        for record in self:
            if record.company_code:
                company = self.env['res.company'].sudo().search([('code', '=', record.company_code), ('id', 'in', self._context.get('allowed_company_ids'))], limit=1)
                if company[:1]:
                    record.edts_company_id = company.id

    @api.onchange('edts_company_id')
    def onchange_edts_company(self):
        for record in self:
            if record.edts_company_id:
                company = self.env['res.company'].sudo().search([('id', '=', record.edts_company_id.id)], limit=1)
                if company[:1]:
                    record.company_code = company.code

    @api.onchange('employee_code')
    def onchange_edts_employee_code(self):
        for record in self:
            if record.employee_code:
                employee = self.env['res.partner'].sudo().search([('partner_assign_number', '=', record.employee_code), ('vendor_account_group_code', '=', '6000')], limit=1)
                if employee[:1]:
                    record.employee_id = employee.id

    @api.onchange('employee_id')
    def onchange_edts_employee(self):
        for record in self:
            if record.employee_id:
                employee = self.env['res.partner'].sudo().search([('id', '=', record.employee_id.id)], limit=1)
                if employee[:1]:
                    record.employee_code = employee.partner_assign_number

    @api.onchange('universal_vendor_code')
    def onchange_edts_universal_vendor_code(self):
        for record in self:
            if record.universal_vendor_code:
                if record.edts_subtype in ['rawland_acquisition']:
                    vendor = self.env['res.partner'].sudo().search([('universal_vendor_code', '=', record.universal_vendor_code), ('vendor_account_group_code', '=', '7000')], limit=1)
                    if vendor[:1]:
                        record.rawland_owner_id = vendor.id
                else:
                    vendor = self.env['res.partner'].sudo().search([('universal_vendor_code', '=', record.universal_vendor_code)], limit=1)
                    if vendor[:1]:
                        record.vendor_id = vendor.id

                if vendor[:1] and (record.vendor_id or record.rawland_owner_id):
                    record.vendor_code_113 = vendor.vendor_code_113
                    record.vendor_code_303 = vendor.vendor_code_303

    @api.onchange('vendor_code_113')
    def onchange_edts_vendor_code_113(self):
        for record in self:
            if record.vendor_code_113:
                if record.edts_subtype in ['rawland_acquisition']:
                    vendor = self.env['res.partner'].sudo().search([('sap_client_id', '=', 113), ('vendor_code_113', '=', record.vendor_code_113), ('vendor_account_group_code', '=', '7000')], limit=1)
                    if vendor[:1]:
                        record.rawland_owner_id = vendor.id
                else:
                    vendor = self.env['res.partner'].sudo().search([('sap_client_id', '=', 113), ('vendor_code_113', '=', record.vendor_code_113)], limit=1)
                    if vendor[:1]:
                        record.vendor_id = vendor.id

                if vendor[:1] and (record.vendor_id or record.rawland_owner_id):
                    record.universal_vendor_code = vendor.universal_vendor_code

    @api.onchange('vendor_code_303')
    def onchange_edts_vendor_code_303(self):
        for record in self:
            if record.vendor_code_303:
                if record.edts_subtype in ['rawland_acquisition']:
                    vendor = self.env['res.partner'].sudo().search([('sap_client_id', '=', 303), ('vendor_code_303', '=', record.vendor_code_303), ('vendor_account_group_code', '=', '7000')], limit=1)
                    if vendor[:1]:
                        record.rawland_owner_id = vendor.id
                else:
                    vendor = self.env['res.partner'].sudo().search([('sap_client_id', '=', 303), ('vendor_code_303', '=', record.vendor_code_303)], limit=1)
                    if vendor[:1]:
                        record.vendor_id = vendor.id

                if vendor[:1] and (record.vendor_id or record.rawland_owner_id):
                    record.universal_vendor_code = vendor.universal_vendor_code

    @api.onchange('vendor_id')
    def onchange_edts_vendor(self):
        for record in self:
            if record.vendor_id:
                vendor = self.env['res.partner'].sudo().search([('id', '=', record.vendor_id.id)], limit=1)
                if vendor[:1]:
                    record.universal_vendor_code = vendor.universal_vendor_code
                    record.vendor_code_113 = vendor.vendor_code_113
                    record.vendor_code_303 = vendor.vendor_code_303

    @api.onchange('rawland_owner_id')
    def onchange_edts_rawland_owner(self):
        for record in self:
            if record.rawland_owner_id:
                rawland_owner = self.env['res.partner'].sudo().search([('id', '=', record.rawland_owner_id.id)], limit=1)
                if rawland_owner[:1]:
                    record.universal_vendor_code = rawland_owner.universal_vendor_code
                    record.vendor_code_113 = rawland_owner.vendor_code_113
                    record.vendor_code_303 = rawland_owner.vendor_code_303

    @api.onchange('edts_purchase_id')
    def onchange_edts_purchase_order(self):
        for record in self:
            if record.edts_purchase_id and record.edts_purchase_id.partner_id:
                default_payment_term = self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')])
                record.balance = record.edts_purchase_id.amount_total
                record.payment_term_id = default_payment_term.id if default_payment_term[:1] and record.edts_purchase_id and not record.edts_purchase_id.payment_term_id else record.edts_purchase_id.payment_term_id.id
                record.vendor_id = record.edts_purchase_id.partner_id.id
                record.universal_vendor_code = record.edts_purchase_id.partner_id.universal_vendor_code
                record.vendor_code_113 = record.edts_purchase_id.partner_id.vendor_code_113
                record.vendor_code_303 = record.edts_purchase_id.partner_id.vendor_code_303

    @api.onchange('profit_center_code')
    def onchange_edts_profit_center_code(self):
        for record in self:
            if record.profit_center_code:
                profit_center = self.env['account.analytic.account'].sudo().search([('code', '=', record.profit_center_code), ('company_id', '=', record.edts_company_id.id)], limit=1)
                if profit_center[:1]:
                    record.profit_center_id = profit_center.id

    @api.onchange('profit_center_id')
    def onchange_edts_profit_center(self):
        for record in self:
            if record.profit_center_id:
                profit_center = self.env['account.analytic.account'].sudo().search([('id', '=', record.profit_center_id.id)], limit=1)
                if profit_center[:1]:
                    record.profit_center_code = profit_center.code

    @api.onchange('asset')
    def onchange_edts_asset(self):
        for record in self:
            if record.asset:
                record.asset_lookup()

    @api.onchange('internal_order')
    def onchange_edts_internal_order(self):
        for record in self:
            if record.internal_order:
                record.internal_order_lookup()

    @api.onchange('property_admin_sale_id')
    def onchange_edts_property_admin_sale(self):
        for record in self:
            if record.property_admin_sale_id:
                record.property_admin_sale_lookup()

    @api.onchange('edts_purchase_id', 'invoice_type', 'down_payment_percent')
    def onchange_edts_amount_via_type(self):
        for record in self:
            if record.edts_subtype in ['invoice_w_po']:
                if record.edts_purchase_id and record.invoice_type and record.down_payment_percent:
                    record.amount = record.edts_purchase_id.amount_total * record.down_payment_percent

    @api.onchange('po_delivery_ids')
    def onchange_edts_amount_via_po_delivery_ids(self):
        for record in self:
            total_dr_gr_amount = 0
            for delivery_id in record.po_delivery_ids:
                total_dr_gr_amount += delivery_id.total_amount

            record.amount = total_dr_gr_amount

    @api.onchange('rawland_payment_terms', 'baseline_start_date', 'baseline_end_date', 'acquisition_cost')
    def onchange_edts_amount_via_acquisition_cost(self):
        for record in self:
            if record.edts_subtype in ['rawland_acquisition']:
                month_diff = record.get_month_difference(record.baseline_end_date, record.baseline_start_date)
                year_diff = record.get_year_difference(record.baseline_end_date, record.baseline_start_date)

                if record.rawland_payment_terms in ['due']:
                    record.amount = record.acquisition_cost

                elif record.rawland_payment_terms in ['monthly']:
                    if month_diff != 0:
                        record.amount = record.acquisition_cost / month_diff
                    else:
                        raise Warning(MONTHLY_PAYMENT_TERM_WARNING)

                elif record.rawland_payment_terms in ['quarterly']:
                    if month_diff and month_diff % 3 == 0:
                        record.amount = record.acquisition_cost / (month_diff/3)
                    else:
                        raise Warning(QUARTERLY_PAYMENT_TERM_WARNING)

                elif record.rawland_payment_terms in ['semi_annual']:
                    if month_diff and month_diff % 6 == 0:
                        record.amount = record.acquisition_cost / (month_diff/6)
                    else:
                        raise Warning(SEMI_ANNUAL_PAYMENT_TERM_WARNING)

                elif record.rawland_payment_terms in ['annualy']:
                    if year_diff != 0:
                        record.amount = record.acquisition_cost / year_diff
                    else:
                        raise Warning(ANNUAL_PAYMENT_TERM_WARNING)

    @api.onchange('valid_from')
    def onchange_edts_valid_from_validation(self):
        for record in self:
            present_date = datetime.now().date()
            if record.valid_from and record.valid_from < present_date:
                raise Warning(VALID_FROM_DATE_WARNING)
            else:
                record.valid_to = record.get_target_date(record.valid_from)

    @api.onchange('valid_to')
    def onchange_edts_valid_to_validation(self):
        for record in self:
            if record.valid_from:
                minimum_date = record.get_target_date(record.valid_from)
                if record.valid_to and record.valid_to < minimum_date:
                    raise Warning(VALID_TO_DATE_WARNING)

    def _compute_is_requestor(self):
        for record in self:
            record.is_requestor = False

            if record.requestor == self.env.user:
                record.is_requestor = True

    def _compute_is_approver(self):
        for record in self:
            record.is_approver = False

            if record.approver == self.env.user:
                record.is_approver = True

    def _compute_is_processor(self):
        for record in self:
            record.is_processor = False

            if record.processor == self.env.user:
                record.is_processor = True

    def _compute_hide_transfer_btn(self):
        for record in self:
            hide_btn = False

            if record.is_requestor is False and record.is_approver is False and record.is_processor is False:
                hide_btn = True

            if record.is_requestor and record.is_requestor != record.is_processor and record.status not in ['draft'] or \
                    record.is_approver and record.status not in ['waiting_for_head'] or \
                    record.is_processor and record.is_requestor != record.is_processor and record.status not in ['waiting_for_accounting'] or \
                    record.is_requestor and record.is_processor and record.status in ['waiting_for_head']:
                hide_btn = True

            record.hide_transfer_btn = hide_btn

    def _compute_hide_recall_btn(self):
        for record in self:
            hide_btn = False

            if record.is_requestor is False and record.is_approver is False and record.is_processor is False:
                hide_btn = True

            if record.is_requestor and record.is_requestor != record.is_processor and record.status not in ['waiting_for_head'] or \
                    record.is_approver and record.status not in ['waiting_for_accounting'] or \
                    record.is_processor and record.is_requestor != record.is_processor or \
                    record.is_requestor and record.is_processor and record.status in ['waiting_for_accounting']:
                hide_btn = True

            record.hide_recall_btn = hide_btn

    def _compute_hide_return_reject_btn(self):
        for record in self:
            hide_btn = False

            if record.is_requestor is False and record.is_approver is False and record.is_processor is False:
                hide_btn = True

            if record.status in ['waiting_for_head'] and record.is_approver is False:
                hide_btn = True
            elif record.status in ['waiting_for_accounting'] and record.is_processor is False:
                hide_btn = True

            record.hide_return_reject_btn = hide_btn

    def _compute_is_edts_field_readonly(self):
        for record in self:
            readonly = False
            base_condition = record.sap_api_status in ['posted_to_sap'] or record.status not in ['waiting_for_accounting', 'processing_accounting']
            same_requestor_processor = record.sap_api_status in ['posted_to_sap'] or record.status not in ['draft', 'waiting_for_accounting', 'processing_accounting']

            if record.is_requestor is False and record.is_approver is False and record.is_processor is False:
                readonly = True

            if record.is_requestor and record.is_requestor != record.is_processor and record.status not in ['draft'] or \
                    record.is_approver and record.status not in ['waiting_for_head'] or \
                    record.is_processor and record.is_requestor != record.is_processor and base_condition or \
                    record.is_requestor and record.is_processor and same_requestor_processor:

                readonly = True

            record.is_edts_field_readonly = readonly

    def _compute_total_payment_count(self):
        for record in self:
            record.total_payment_count = self.env['edts.payment.reference.line'].sudo().search_count([('account_move_id', '=', record.id)])

    def _compute_need_release_count(self):
        for record in self:
            record.need_released_count = self.env['edts.payment.reference.line'].sudo().search_count([('account_move_id', '=', record.id), ('released', '=', False), ('is_payment_ready_for_releasing', '=', True)])

    def _compute_need_encash_count(self):
        for record in self:
            record.need_encashed_count = self.env['edts.payment.reference.line'].sudo().search_count([('account_move_id', '=', record.id), ('released', '=', True), ('encashed', '=', False), ('mode', 'in', ['check', 'check_writer'])])

    def _compute_total_payment_amount(self):
        for record in self:
            total_amount = 0
            for r in record.payment_reference_ids:
                if r.released:
                    total_amount += r.payment_amount
            record.total_payment_amount = total_amount

    def _compute_total_payment_amount_display(self):
        for record in self:
            total_amount = 0
            for r in record.payment_reference_ids:
                if r.released:
                    total_amount += r.payment_amount
            record.total_payment_amount_display = '{:,.2f}'.format(total_amount) + ' ' + record.currency_id.symbol

    def _compute_total_liquidation_count(self):
        for record in self:
            record.total_liquidation_count = self.env['edts.liquidation.reference'].sudo().search_count([('account_move_id', '=', record.id)])

    @api.depends('liquidation_reference_ids.liquidation_status')
    def _compute_liquidation_status(self):
        for record in self:
            record.liquidation_status = 'unliquidated'
            if record.liquidation_reference_ids and record.liquidation_reference_ids[0]:
                record.liquidation_status = record.liquidation_reference_ids[0].liquidation_status

    @api.depends('liquidation_reference_ids.submission_status')
    def _compute_submission_status(self):
        for record in self:
            record.submission_status = 'pending_for_submission'
            if record.liquidation_reference_ids and record.liquidation_reference_ids[0]:
                record.submission_status = record.liquidation_reference_ids[0].submission_status

    def _compute_edts_subtype_label(self):
        for record in self:
            record.edts_subtype_label = False
            if record.edts_subtype:
                record.edts_subtype_label = dict(record._fields['edts_subtype'].selection).get(record.edts_subtype)

    def _compute_edts_status_label(self):
        for record in self:
            record.edts_status_label = False
            if record.status:
                record.edts_status_label = dict(record._fields['status'].selection).get(record.status)

    def _compute_is_in_valid_renewal_date(self):
        for record in self:
            present_date = datetime.now().date()
            allow_renewal_days = record.edts_company_id.allow_renewal_days
            allow_renewal_date = record.valid_to and record.valid_to - relativedelta(days=allow_renewal_days)
            if allow_renewal_date and present_date >= allow_renewal_date and record.status not in ['completed']:
                record.is_in_valid_renewal_date = True
            else:
                record.is_in_valid_renewal_date = False

    def create_default_lines_for_next_record(self, move_id):
        """ Setting default account.move.line values from base record to renewed/created recurring record
        self: Base Record
        move_id: Next Record Id
        """
        new_line_ids = []

        for line in self.line_ids:
            vals = {
                'move_id': move_id,
                'posting_key': line.posting_key,
                'account_id': line.account_id.id,
                'description': line.description,
                'text': line.text,
                'debit': line.debit,
                'credit': line.credit,
                'cash_flow_code': line.cash_flow_code,
            }
            new_line_ids.append(vals)

        record_ids = self.env['account.move.line'].create(new_line_ids)

        return record_ids

    def check_countering(self):
        for record in self:
            if not record.po_delivery_ids and record.edts_subtype in ['invoice_w_po']:
                raise ValidationError(NO_DR_GR_WARNING)

            for dr in record.po_delivery_ids:
                if not dr.countered:
                    raise ValidationError(DR_GR_NOT_COUNTERED_WARNING)

    def clear_wizard_data(self):
        for record in self:
            if record.wizard_reason:
                record.wizard_reason = False

    def clear_countered_data(self):
        for record in self:
            if record.countered:
                record.countered = False
                record.countered_date = False
                record.countered_by = False

    def generate_move_name(self):
        for record in self:
            if '*' in record.name:
                sequence = record._get_sequence()
                if not sequence:
                    raise Warning('Please define a sequence on your journal.')

                record.name = sequence.with_context(ir_sequence_date=record.date).next_by_id()

    def get_edts_data_based_from_codes(self):
        """Used mainly for import since xlsx format only have codes"""
        # Getting Company by Company Code
        if not self.edts_company_id and self.company_code:
            self.onchange_edts_company_code()

        # Getting Vendor or Rawland Owner by Vendor Codes
        if ((self.edts_subtype in ['rawland_acquisition'] and not self.rawland_owner_id) or not self.vendor_id) \
            and (self.universal_vendor_code or self.vendor_code_113 or self.vendor_code_303):

            self.onchange_edts_universal_vendor_code()
            self.onchange_edts_vendor_code_113()
            self.onchange_edts_vendor_code_303()

        # Getting Employee by Employee Code
        if not self.employee_id and self.employee_code:
            self.onchange_edts_employee_code()

        # Getting Vendor and Vendor Codes by Purchase Order
        if not self.vendor_id and self.edts_purchase_id and self.edts_purchase_id.partner_id \
            and not self.universal_vendor_code \
            and not self.vendor_code_113 \
            and not self.vendor_code_303:

            self.onchange_edts_purchase_order()

        # Getting Profit Center and Internal Order by Asset
        if not self.profit_center_id and not self.internal_order and self.asset:
            self.onchange_edts_asset()

        # Getting Profit Center by Internal Order
        if not self.profit_center_id and self.internal_order:
            self.onchange_edts_internal_order()

        # Getting WBS Element and Project Description by Property Admin Sale
        if not self.wbs_element and not self.project_description and self.property_admin_sale_id:
            self.onchange_edts_property_admin_sale()

        if not self.profit_center_id and self.profit_center_code:
            self.onchange_edts_profit_center_code()

    def get_target_date(self, initial_date, number_of_months=1):
        target_date = False

        if initial_date:
            target_date = initial_date + relativedelta(months=number_of_months)
            max_days_in_initial_date = monthrange(initial_date.year, initial_date.month)[1]
            max_days_in_target_date = monthrange(target_date.year, target_date.month)[1]

            if max_days_in_target_date > max_days_in_initial_date and initial_date.day == max_days_in_initial_date:
                target_date = target_date + timedelta(days=max_days_in_target_date - max_days_in_initial_date)

        return target_date

    def get_year_difference(self, end_date, start_date):
        year_diff = 0
        if end_date and start_date:
            year_diff = (end_date.year - start_date.year)
        return year_diff

    def get_month_difference(self, end_date, start_date):
        month_diff = 0
        if end_date and start_date:
            month_diff = ((end_date.year - start_date.year) * 12) + (end_date.month - start_date.month)
        return month_diff

    def send_edts_status_update_email(self):
        requestor_template_id = self.env.ref('edts.email_template_edts_status_update_requestor').id
        dept_head_template_id = self.env.ref('edts.email_template_edts_status_update_dept_head').id
        acctg_template_id = self.env.ref('edts.email_template_edts_status_update_acctg').id

        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        context = {
            'url': url,
        }

        requestor_template = self.env['mail.template'].browse(requestor_template_id).with_context(context)
        dept_head_template = self.env['mail.template'].browse(dept_head_template_id).with_context(context)
        acctg_template = self.env['mail.template'].browse(acctg_template_id).with_context(context)

        requestor_template.send_mail(self.id, force_send=True)

        if self.status in ['waiting_for_accounting'] and self.edts_subtype not in ['return']:
            dept_head_template.send_mail(self.id, force_send=True)
        elif self.status not in ['draft', 'waiting_for_head', 'waiting_for_accounting']:
            if self.edts_subtype not in ['return']:
                dept_head_template.send_mail(self.id, force_send=True)
            acctg_template.send_mail(self.id, force_send=True)

    def send_edts_for_approval_dept_head_email(self):
        template_id = self.env.ref('edts.email_template_edts_for_approval_dept_head').id
        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        context = {
            'url': url
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)

    def send_edts_for_validation_acctg_email(self):
        template_id = self.env.ref('edts.email_template_edts_for_validation_acctg').id
        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        context = {
            'url': url
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)

    def send_edts_recall_email(self):
        requestor_template_id = self.env.ref('edts.email_template_edts_recalled_requestor').id
        dept_head_template_id = self.env.ref('edts.email_template_edts_recalled_dept_head').id
        acctg_template_id = self.env.ref('edts.email_template_edts_recalled_acctg').id

        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        if self.status in ['draft']:
            sender = self.requestor.name
        elif self.status in ['waiting_for_head']:
            sender = self.approver.name

        context = {
            'url': url,
            'sender': sender
        }

        requestor_template = self.env['mail.template'].browse(requestor_template_id).with_context(context)
        dept_head_template = self.env['mail.template'].browse(dept_head_template_id).with_context(context)
        acctg_template = self.env['mail.template'].browse(acctg_template_id).with_context(context)

        if self.status in ['draft']:
            dept_head_template.send_mail(self.id, force_send=True)
        elif self.status in ['waiting_for_head']:
            requestor_template.send_mail(self.id, force_send=True)
            acctg_template.send_mail(self.id, force_send=True)

    def send_edts_return_email(self):
        requestor_template_id = self.env.ref('edts.email_template_edts_returned_requestor').id
        dept_head_template_id = self.env.ref('edts.email_template_edts_returned_dept_head').id
        acctg_template_id = self.env.ref('edts.email_template_edts_returned_acctg').id

        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        if self.status in ['waiting_for_head']:
            sender = self.approver.name
        elif self.status in ['waiting_for_accounting']:
            sender = self.processor.name

        context = {
            'url': url,
            'sender': sender
        }

        requestor_template = self.env['mail.template'].browse(requestor_template_id).with_context(context)
        dept_head_template = self.env['mail.template'].browse(dept_head_template_id).with_context(context)
        acctg_template = self.env['mail.template'].browse(acctg_template_id).with_context(context)

        if self.status in ['waiting_for_head']:
            requestor_template.send_mail(self.id, force_send=True)
            acctg_template.send_mail(self.id, force_send=True)
        elif self.status in ['waiting_for_accounting']:
            requestor_template.send_mail(self.id, force_send=True)
            dept_head_template.send_mail(self.id, force_send=True)

    def send_edts_reject_email(self):
        requestor_template_id = self.env.ref('edts.email_template_edts_rejected_requestor').id
        dept_head_template_id = self.env.ref('edts.email_template_edts_rejected_dept_head').id
        acctg_template_id = self.env.ref('edts.email_template_edts_rejected_acctg').id

        view_id = self.env.ref('edts.view_move_form_inherit').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        if self.status in ['waiting_for_head']:
            sender = self.approver.name
        elif self.status in ['waiting_for_accounting']:
            sender = self.processor.name

        context = {
            'url': url,
            'sender': sender
        }

        requestor_template = self.env['mail.template'].browse(requestor_template_id).with_context(context)
        dept_head_template = self.env['mail.template'].browse(dept_head_template_id).with_context(context)
        acctg_template = self.env['mail.template'].browse(acctg_template_id).with_context(context)

        if self.status in ['waiting_for_head']:
            requestor_template.send_mail(self.id, force_send=True)
            acctg_template.send_mail(self.id, force_send=True)
        elif self.status in ['waiting_for_accounting']:
            requestor_template.send_mail(self.id, force_send=True)
            dept_head_template.send_mail(self.id, force_send=True)

    def send_renewal_notification_email(self):
        template_id = self.env.ref('edts.email_template_renewal_notification').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def send_extended_notification_email(self):
        template_id = self.env.ref('edts.email_template_is_extended_notification').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def send_renewed_notification_email(self):
        template_id = self.env.ref('edts.email_template_is_renewed_notification').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def send_completed_notification_email(self):
        template_id = self.env.ref('edts.email_template_completed_notification').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def transfer_edts(self):
        view_id = self.env.ref('edts.transfer_wizard_form').id
        return {
            'name': 'Transfer EDTS',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.transfer.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'default_edts_status': self.status,
                'default_requestor_from': self.requestor.id,
                'default_approver_from': self.approver.id,
                'default_processor_from': self.processor.id,
            }
        }

    def submit_edts(self):
        if self.returned_or_recalled:
            if self.edts_subtype in ['return']:
                self.set_waiting_for_accounting_status()
                self.send_edts_for_validation_acctg_email()
            else:
                self.set_waiting_for_head_status()
                self.send_edts_for_approval_dept_head_email()
        else:
            view_id = self.env.ref('edts.submit_wizard_form').id
            return {
                'name': 'Submit EDTS',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'edts.submit.wizard',
                'view_id': view_id,
                'target': 'new',
                'context': {
                    'default_account_move_id': self.id,
                    'default_edts_subtype': self.edts_subtype,
                    'default_requestor': self.requestor.id
                }
            }

    def recall_edts(self):
        self.set_recall_status()
        self.send_edts_recall_email()
        return True

    def approve_edts(self):
        view_id = self.env.ref('edts.signature_wizard_form').id
        return {
            'name': 'Approve EDTS',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.signature.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'default_action': 'approve'
            }
        }

    def validate_edts(self):
        view_id = self.env.ref('edts.signature_wizard_form').id
        return {
            'name': 'Validate EDTS',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.signature.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'default_action': 'validate'
            }
        }

    def reject_edts(self):
        view_id = self.env.ref('edts.rejected_wizard_form').id
        return {
            'name': 'Reject',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.reason.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_account_move_id': self.id
            }
        }

    def return_edts(self):
        view_id = self.env.ref('edts.returned_wizard_form').id
        return {
            'name': 'Return',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.reason.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_account_move_id': self.id
            }
        }

    def done_edts(self):
        self.set_done_status()
        return True

    def countered_edts(self):
        self.check_countering()
        view_id = self.env.ref('edts.countered_wizard_form').id
        return {
            'name': 'Countered EDTS',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'edts.countered.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_account_move_id': self.id
            }
        }

    def process_finance(self):
        self.set_processing_finance_status()
        return True

    def renew_recurring_edts(self):
        view_id = self.env.ref('edts.edts_form_view').id
        month_difference = ((self.valid_to.year - self.valid_from.year) * 12) + (self.valid_to.month - self.valid_from.month)
        new_valid_from = self.valid_to + relativedelta(days=1)
        new_valid_to = self.get_target_date(new_valid_from, month_difference) - relativedelta(days=1)

        vals = {
            'old_renewal_id': self.id,
            'edts_subtype': self.edts_subtype,
            'company_id': self.company_id.id,
            'company_code': self.company_code,
            'journal_id': self.journal_id.id,
            'amount': self.amount,
            'approved_amount': self.approved_amount,
            'billed_amount': self.billed_amount,
            'internal_order': self.internal_order,
            'account_number': self.account_number,
            'employee_code': self.employee_code,
            'employee_id': self.employee_id.id,
            'universal_vendor_code': self.universal_vendor_code,
            'vendor_code_113': self.vendor_code_113,
            'vendor_code_303': self.vendor_code_303,
            'vendor_id': self.vendor_id.id,
            'department': self.department,
            'cost_center': self.cost_center,
            'valid_from': new_valid_from,
            'valid_to': new_valid_to,
            'run_day': self.run_day,
        }

        renewed_record = self.create(vals)
        self.create_default_lines_for_next_record(renewed_record.id)
        self.new_renewal_id = renewed_record.id
        self.send_renewed_notification_email()
        self.set_completed_status()

        return {
            'name': 'Renew',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_id': renewed_record.id,
            'res_model': 'account.move',
            'target': 'current',
        }

    def extend_recurring_edts(self):
        view_id = self.env.ref('edts.accruals_or_monthly_extension_form').id

        return {
            'name': 'Extension',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'edts.reason.wizard',
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'default_valid_from': self.valid_from,
                'default_valid_to': self.valid_to,
            }
        }

    def get_all_payments(self):
        payment_tree = self.env.ref('edts.payment_reference_tree')
        payment_form = self.env.ref('edts.payment_reference_form')

        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'domain': [('account_move_id', '=', self.id)],
            'res_model': 'edts.payment.reference.line',
            'view_mode': 'tree,form',
            'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
            'context': {
                'default_account_move_id': self.id,
                'create': False if self.status in ['fully_paid'] else True,
                'edit': False if self.status in ['fully_paid'] else True,
            }
        }

    def get_need_released_payments(self):
        payment_tree = self.env.ref('edts.payment_reference_tree')
        payment_form = self.env.ref('edts.payment_reference_to_release_form')

        return {
            'name': 'To Release',
            'type': 'ir.actions.act_window',
            'domain': [('account_move_id', '=', self.id), ('released', '=', False), ('is_payment_ready_for_releasing', '=', True)],
            'res_model': 'edts.payment.reference.line',
            'view_mode': 'tree,form',
            'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
            'context': {
                'create': False,
            }
        }

    def get_need_encashed_payments(self):
        payment_tree = self.env.ref('edts.payment_reference_tree')
        payment_form = self.env.ref('edts.payment_reference_to_encash_form')

        return {
            'name': 'To Encash',
            'type': 'ir.actions.act_window',
            'domain': [('account_move_id', '=', self.id), ('released', '=', True), ('encashed', '=', False), ('mode', 'in', ['check', 'check_writer'])],
            'res_model': 'edts.payment.reference.line',
            'view_mode': 'tree,form',
            'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
            'context': {
                'create': False,
                'edit': False
            }
        }

    def get_all_liquidations(self):
        liquidation_tree = self.env.ref('edts.liquidation_reference_from_edts_tree')
        liquidation_form = self.env.ref('edts.liquidation_reference_form')
        liquidation_search = self.env.ref('edts.edts_liquidation_reference_search_view')

        return {
            'name': 'Liquidations',
            'type': 'ir.actions.act_window',
            'domain': [('account_move_id', '=', self.id)],
            'res_model': 'edts.liquidation.reference',
            'view_mode': 'tree,form',
            'search_view_id': [liquidation_search.id, 'search'],
            'views': [(liquidation_tree.id, 'tree'), (liquidation_form.id, 'form')],
            'context': {
                'default_account_move_id': self.id,
                'default_edts_subtype': self.edts_subtype,
                'default_company_id': self.edts_company_id.id,
                'default_journal_id': self.journal_id.id,
                'default_request_date': self.request_date,
                'default_currency_id': self.currency_id.id,
                'default_amount': self.amount,
                'default_requestor': self.requestor.id,
                'create': True if len(self.liquidation_reference_ids) == 0 else False
            }
        }

    def set_recall_status(self):
        if self.status in ['waiting_for_head']:
            self.set_draft_status()
        elif self.status in ['waiting_for_accounting']:
            self.set_waiting_for_head_status()
        self.returned_or_recalled = True
        return True

    def set_draft_status(self):
        self.status = 'draft'
        return True

    def set_ongoing_status(self):
        self.status = 'ongoing'
        return True

    def set_waiting_for_head_status(self):
        self.status = 'waiting_for_head'
        return True

    def set_waiting_for_accounting_status(self):
        self.status = 'waiting_for_accounting'
        return True

    def set_processing_accounting_status(self):
        self.status = 'processing_accounting'
        return True

    def set_processing_finance_status(self):
        self.status = 'processing_finance'
        return True

    def set_partial_payment_released_status(self):
        self.status = 'partial_payment_released'
        return True

    def set_fully_paid_status(self):
        self.status = 'fully_paid'
        return True

    def set_done_status(self):
        self.status = 'done'
        return True

    def set_completed_status(self):
        self.status = 'completed'
        return True

    def set_reject_status(self):
        self.status = 'rejected'
        return True

    def get_api_config(self):
        # Get API config in settings
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')

        if api_key and api_key.api_app_key and api_key.api_app_id and api_key.api_url and api_key.api_prefix:
            headers = {'X-AppKey': api_key.api_app_key,
                       'X-AppId': api_key.api_app_id,
                       'Content-Type': api_key.api_content_type}
            conn = http.client.HTTPSConnection(api_key.api_url)
            prefix = api_key.api_prefix
        else:
            raise Warning(NO_API_CONFIG_WARNING)

        return headers, conn, prefix

    def get_invoice_wo_po_payload(self):
        user = self.env['res.users'].sudo().search([('id', '=', self._uid)], limit=1)
        if user[:1]:
            processed_by = user.name

        if self.sap_client_id == 113:
            vendor_code = self.vendor_code_113
        elif self.sap_client_id == 303:
            vendor_code = self.vendor_code_303
        else:
            vendor_code = False

        payload = {
            "Params": {
                "Client": self.sap_client_id or '',
                "EdtsNo": self.name,
                "DocumentDate": str(self.document_date),
                "PostingDate": str(datetime.now().date()),
                "Reference": self.ref or '',
                "CompanyCode": self.company_code,
                "DocumentHeader": self.doc_header or '',
                "VendorCode": vendor_code or '',
                "UniversalVendorCode": self.universal_vendor_code or '',
                "Amount": self.amount,
                "ProcessBy": processed_by,
                "Text": self.reason or '',
                "ID": self.id,
            }
        }
        return 'InvoiceWithoutPO', payload

    def get_invoice_w_po_payload(self):
        user = self.env['res.users'].sudo().search([('id', '=', self._uid)], limit=1)
        if user[:1]:
            processed_by = user.name

        if self.sap_client_id == 113:
            vendor_code = self.vendor_code_113
        elif self.sap_client_id == 303:
            vendor_code = self.vendor_code_303
        else:
            vendor_code = False

        dr_grs = []
        for dr in self.po_delivery_ids:
            dr_grs.append(dr.gr_number or dr.dr_no)

        payload = {
            "Params": {
                "Client": self.sap_client_id or '',
                "EdtsNo": self.name,
                "Type": self.invoice_type or '',
                "DocumentDate": str(self.document_date),
                "PostingDate": str(datetime.now().date()),
                "RequestDate": str(datetime.now().date()),
                "Reference": self.ref or '',
                "CompanyCode": self.company_code,
                "PurchaseOrder": self.edts_purchase_id.name or '',
                "DocumentHeader": self.doc_header or '',
                "VendorCode": vendor_code or '',
                "UniversalVendorCode": self.universal_vendor_code or '',
                "Amount": self.amount,
                "ProcessBy": processed_by,
                "Text": self.reason or '',
                "ID": self.id,
                "GRList": dr_grs,
            }
        }
        return 'InvoiceWithPO', payload

    def get_advance_payment_payload(self):
        user = self.env['res.users'].sudo().search([('id', '=', self._uid)], limit=1)
        if user[:1]:
            processed_by = user.name

        if self.sap_client_id == 113:
            vendor_code = self.vendor_code_113
        elif self.sap_client_id == 303:
            vendor_code = self.vendor_code_303
        else:
            vendor_code = False

        payload = {
            "Params": {
                "ID": self.id,
                "Client": self.sap_client_id or '',
                "CompanyCode": self.company_code,
                "VendorCode": vendor_code or '',
                "UniversalVendorCode": self.universal_vendor_code or '',
                "EdtsNo": self.name,
                "PostingDate": str(datetime.now().date()),
                "DocumentDate": str(self.document_date),
                "DocumentHeader": self.doc_header or '',
                "ProfitCenter": self.profit_center_id or '',
                "Text": self.reason or '',
                "Assignment": self.assignment or '',
                "AcctPer": self.accountable_person or '',
                "Amount": self.amount,
                "ProcessBy": processed_by,
            }
        }
        return 'PostProcAdvancePay', payload

    def get_rawland_payload(self):
        user = self.env['res.users'].sudo().search([('id', '=', self._uid)], limit=1)
        if user[:1]:
            processed_by = user.name

        if self.sap_client_id == 113:
            vendor_code = self.vendor_code_113
        elif self.sap_client_id == 303:
            vendor_code = self.vendor_code_303
        else:
            vendor_code = False

        payload = {
            "Params": {
                "ID": self.id,
                "Client": self.sap_client_id or '',
                "CompanyCode": self.company_code,
                "VendorCode": vendor_code or '',
                "UniversalVendorCode": self.universal_vendor_code or '',
                "EdtsNo": self.name,
                "PostingDate": str(datetime.now().date()),
                "DocumentDate": str(self.document_date),
                "DocumentHeader": self.doc_header or '',
                "Asset": self.asset or '',
                "ProfitCenter": self.profit_center_id.code or '',
                "RawlandOwnerCode": vendor_code or '',
                "RawlandOwner": self.rawland_owner_id.name or '',
                "Text": self.reason or '',
                "BaselineStartDate": str(self.baseline_start_date) or '',
                "BaselineEndDate": str(self.baseline_end_date) or '',
                "PaymentTerms": self.rawland_payment_terms or '',
                "Amount": self.amount,
                "ProcessBy": processed_by,
            }
        }
        return 'PostRawLandPost', payload

    def get_reimbursement_payload(self):
        user = self.env['res.users'].sudo().search([('id', '=', self._uid)], limit=1)
        if user[:1]:
            processed_by = user.name

        payload = {
            "Params": {
                "ID": self.id,
                "Client": self.sap_client_id or '',
                "CompanyCode": self.company_code,
                "VendorCode": self.employee_code or '',
                "EdtsNo": self.name,
                "PostingDate": str(datetime.now().date()),
                "DocumentDate": str(self.document_date),
                "DocumentHeader": self.doc_header or '',
                "Asset": self.asset or '',
                "InternalOrder": self.internal_order or '',
                "ProfitCenter": self.profit_center_id.code or '',
                "Text": self.reason or '',
                "Assignment": self.assignment or '',
                "Amount": self.amount,
                "ProcessBy": processed_by,
            }
        }
        print(payload)
        return 'PostProcReimbursement', payload

    def get_cash_advance_payload(self):
        user = self.env['res.users'].sudo().search([('id', '=', self._uid)], limit=1)
        if user[:1]:
            processed_by = user.name

        payload = {
            "Params": {
                "ID": self.id,
                "Client": self.sap_client_id or '',
                "CompanyCode": self.company_code,
                "VendorCode": self.employee_code or '',
                "EdtsNo": self.name,
                "PostingDate": str(datetime.now().date()),
                "DocumentDate": str(self.document_date),
                "DocumentHeader": self.doc_header or '',
                "ProfitCenter": self.profit_center_id.code or '',
                "Text": self.reason or '',
                "Assignment": self.assignment or '',
                "Amount": self.amount,
                "ProcessBy": processed_by,
            }
        }
        print(payload)
        return 'PostProcCashAdvancePay', payload

    def get_tech_serv_payload(self):
        if self.sap_client_id == 113:
            vendor_code = self.vendor_code_113
        elif self.sap_client_id == 303:
            vendor_code = self.vendor_code_303
        else:
            vendor_code = False

        payload = {
            "Params": {
                "ID": self.id,
                "EdtsNo": self.name,
                "CompanyCode": self.company_code,
                "SalesOrder": self.property_admin_sale_id.so_number or '',
                "VendorCode": vendor_code or '',
                "CustomerCode": self.employee_code or '',
                "CMCType": str(self.cmc_type_id.cmc_type).zfill(2) or '',
                "Payee": self.payee or '',
                "ActPerson": self.accountable_person or '',
                "Amount": self.amount,
            }
        }
        return 'PostTechServe', payload

    def get_setup_payload(self):
        payload = {
            "Params": {
                "Client": self.sap_client_id or '',
                "EdtsNo": self.name,
                "CompanyCode": self.company_code,
                "CashJournal": self.cash_journal_no or '',
                "CustodianCode": self.employee_code or '',
                "Amount": self.amount,
                "ProfitCenter": self.profit_center_id.code or '',
                "PostingDate": str(datetime.now().date()),
                "Reference": self.ref or '',
                "DocumentHeader": self.doc_header or '',
                "DocumentDate": str(self.document_date),
                "Text": self.reason or '',
                "Assignment": self.assignment or '',
            }
        }
        return 'PostSetup', payload

    def internal_order_lookup(self):
        headers, conn, prefix = self.get_api_config()

        conn.request("GET", f"{prefix}InternalOrderLookUp?InternerOrder={'%s'}"
                     % self.internal_order, [],
                     headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        if 'status' in json_data and json_data.get('status') in ['Success']:
            if json_data.get('data').get('CompanyCode'):
                if json_data.get('data').get('CompanyCode') != self.company_code:
                    raise Warning(INTERNAL_LOOKUP_WARNING % (self.company_code, json_data.get('data').get('CompanyCode')))

            profit_center = self.env['account.analytic.account'].search([('code', '=', json_data.get('data').get('ProfitCenterCode'))], limit=1)
            if profit_center[:1]:
                self.profit_center_id = profit_center.id
        elif 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            raise Warning(json_data.get('Errors') or json_data.get('message'))

    def asset_lookup(self):
        headers, conn, prefix = self.get_api_config()

        conn.request("GET", f"{prefix}AssetLookUp?SapClientId={'%s'}&Asset={'%s'}"
                     % (self.sap_client_id, self.asset), [],
                     headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        if 'status' in json_data and json_data.get('status') in ['Success']:
            if json_data.get('data').get('CompanyCode'):
                if json_data.get('data').get('CompanyCode') != self.company_code:
                    raise Warning(ASSET_LOOKUP_WARNING % (self.company_code, json_data.get('data').get('CompanyCode')))

            profit_center = self.env['account.analytic.account'].search([('code', '=', json_data.get('data').get('CostCenter'))], limit=1)
            if profit_center[:1]:
                self.profit_center_id = profit_center.id

            if json_data.get('data').get('InternalOrder'):
                self.internal_order = json_data.get('data').get('InternalOrder')
        elif 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            raise Warning(json_data.get('Errors') or json_data.get('message'))

    def property_admin_sale_lookup(self):
        headers, conn, prefix = self.get_api_config()

        conn.request("GET", f"{prefix}SOValidation?SapClientId={'%s'}&SalesOrder={'%s'}"
                     % (self.sap_client_id, self.property_admin_sale_id.so_number), [],
                     headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        if 'status' in json_data and json_data.get('status') in ['Success']:
            if json_data.get('data').get('Description'):
                self.project_description = json_data.get('data').get('Description')

            if json_data.get('data').get('WBS'):
                self.wbs_element = json_data.get('data').get('WBS')

        elif 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            raise Warning(json_data.get('Errors') or json_data.get('message'))

    def post_edts_data(self):
        headers, conn, prefix = self.get_api_config()

        # Get Payload per EDTS Subtype
        if self.edts_subtype in ['invoice_wo_po']:
            base, payload = self.get_invoice_wo_po_payload()

        elif self.edts_subtype in ['invoice_w_po']:
            base, payload = self.get_invoice_w_po_payload()

        elif self.edts_subtype in ['advance_payment']:
            base, payload = self.get_advance_payment_payload()

        elif self.edts_subtype in ['rawland_acquisition']:
            base, payload = self.get_rawland_payload()

        elif self.edts_subtype in ['reimbursement']:
            base, payload = self.get_reimbursement_payload()

        elif self.edts_subtype in ['cash_advance']:
            base, payload = self.get_cash_advance_payload()

        elif self.edts_subtype in ['techserv_liaison']:
            base, payload = self.get_tech_serv_payload()

        elif self.edts_subtype in ['setup']:
            base, payload = self.get_setup_payload()

        # POST process
        conn.request("POST", f"{prefix}%s" % base, json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        # Success or Error Handling
        if 'status' in json_data and json_data.get('status') in ['Success']:
            self.posting_date = datetime.now().date()
            self.sap_api_status = 'posted_to_sap'
            self.edts_sap_remarks = json_data.get('message')
        elif 'status' in json_data and json_data.get('status') in ['Error'] and json_data.get('message') in 'EDTS is already existing.':
            self.sap_api_status = 'posted_to_sap'
            self.edts_sap_remarks = json_data.get('Errors') or json_data.get('message')
        elif 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            self.sap_api_status = 'failed'
            self.edts_sap_remarks = json_data.get('Errors') or json_data.get('message')

    def get_invoice_doc(self):
        headers, conn, prefix = self.get_api_config()

        if self.edts_subtype in ['invoice_w_po']:
            base = 'PostProcessInvoiceWithPO'
            payload = {
                "Params": {
                    "EdtsNo": self.name
                }
            }
        else:
            base = 'PostProcessInvoice'
            payload = {
                "Params": {
                    "EdtsNo": self.name,
                    "Subtype": self.edts_subtype
                }
            }

        conn.request("POST", f"{prefix}%s" % base, json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        if 'status' in json_data and json_data.get('status') in ['Success']:
            self.sap_api_status = 'invoice_doc_received'
            self.get_invoice_doc_remarks = json_data.get('message')
            self.set_processing_finance_status()
        elif 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            self.get_invoice_doc_remarks = json_data.get('Errors') or json_data.get('message')

    def get_payment(self):
        headers, conn, prefix = self.get_api_config()

        if self.edts_subtype in ['invoice_w_po']:
            base = 'PostProcessInvoiceWithPOPayment'
            dr_grs = []
            for dr in self.po_delivery_ids:
                dr_grs.append(
                    {
                        'GR': dr.gr_number or dr.dr_no,
                        'InvoiceDoc': dr.invoice_doc_no
                    }
                )

            payload = {
                "Params": {
                    "EdtsNo": self.name,
                    "GRList": dr_grs
                }
            }
        else:
            base = 'PostProcessInvoicePayment'
            invoice_lines = []
            for line in self.edts_invoice_doc_line_ids:
                invoice_lines.append(line.invoice_doc_no)

            payload = {
                "Params": {
                    "EdtsNo": self.name,
                    "InvoiceList": invoice_lines,
                    "Subtype": self.edts_subtype
                }
            }

        conn.request("POST", f"{prefix}%s" % base, json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        if 'status' in json_data and json_data.get('status') in ['Success']:
            self.sap_api_status = 'payment_doc_received'
            self.get_payment_doc_remarks = json_data.get('message')
        elif 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            self.get_payment_doc_remarks = json_data.get('Errors') or json_data.get('message')
