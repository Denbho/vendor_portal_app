# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from datetime import datetime
import json


class AccountJournalInherit(models.Model):
    _inherit = 'account.journal'

    """Did not inherit edts.info to avoid unnecessary columns in account.journal table"""
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

    @api.model
    def _create_sequence(self, vals, refund=False):
        """Overriden method to pass edts_subtype value to set default desired EDTS prefix"""
        edts_subtype = vals['edts_subtype'] if 'edts_subtype' in vals else False
        prefix = self._get_sequence_prefix(vals['code'], edts_subtype, refund)
        seq_name = refund and vals['code'] + _(': Refund') or vals['code']
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = refund and vals.get('refund_sequence_number_next', 1) or vals.get(
            'sequence_number_next', 1)
        return seq

    @api.model
    def _get_sequence_prefix(self, code, edts_subtype=False, refund=False):
        """Overriden method to set desired EDTS prefix"""
        if edts_subtype:
            return '%(short_code)s-%(range_year)s-%(company_code)s-'

        prefix = code.upper()
        if refund:
            prefix = 'R' + prefix
        return prefix + '/%(range_year)s/'


class AccountMoveInherit(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'edts.info']

    @api.model
    def _get_default_journal(self):
        journal = super(AccountMoveInherit, self)._get_default_journal()

        if self._context.get('default_edts_subtype'):
            journal = self.env['account.journal'].sudo().search([
                                                ('edts_subtype', '=', self._context.get('default_edts_subtype')),
                                                ('company_id', '=', self.env.company.id)],
                                                limit=1)

        return journal

    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]",
                                 default=_get_default_journal)

    """Removed ambiguity by specifying a new relation name for many2many field."""
    child_recurring_ids = fields.Many2many(comodel_name='account.move', relation='account_move_account_move_rel',
                                           column1='account_move_id', column2='recurring_id',
                                           string='Sub Recurring Record/s', readonly=True)

    po_delivery_ids = fields.Many2many('po.delivery.line', 'account_move_delivery_rel', string="Delivery Document")

    @api.model
    def create(self, vals):
        """In EDTS Application the field 'name' is being generated upon creation this is for the user
        to have a reference of the record"""
        record = super(AccountMoveInherit, self).create(vals)

        if record.edts_subtype:
            record.requestor = record.create_uid.id
            record.name = '(* %s)' %record.id
            record.get_edts_data_based_from_codes()

        return record

    def write(self, vals):
        """In EDTS Application the field 'name' is being generated even if the 'state' is in draft.
        Allow edit of journal as long as edts status is not proccessing accounting onwards"""
        if self.name != '/' and 'journal_id' in vals and self.journal_id.id != vals['journal_id']:
            if self.edts_subtype:
                if self.status in ['draft', 'waiting_for_head', 'waiting_for_accounting', 'processing_accounting', 'rejected']:
                    return super(models.Model, self).write(vals)
                else:
                    raise UserError(_('You cannot edit the journal of an account move if it has been posted once.'))

        record = super(AccountMoveInherit, self).write(vals)

        return record

    def unlink(self):
        for record in self:
            if record.name != '/' and not self._context.get('force_delete'):
                if record.edts_subtype:
                    return super(models.Model, self).unlink()
                    # if record.status in ['draft', 'ongoing', 'waiting_for_head', 'waiting_for_accounting', 'processing_accounting', 'rejected']:
                    #     self.env.context = dict(self.env.context)
                    #     self.env.context.update({'force_delete': True})
                    # else:
                    #     raise UserError(_("You cannot delete an entry which has been posted once."))

        record = super(AccountMoveInherit, self).unlink()

        return record

    def _get_move_display_name(self, show_ref=False):
        """Overriden method to set desired EDTS record name.
        Remove draft_name before the self.name if record is created in EDTS application"""
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft' and self.edts_subtype is False:
            draft_name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
            }[self.type]
            if not self.name or self.name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.name
        return (draft_name or self.name) + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')

    @api.onchange('journal_id')
    def onchange_edts_get_journal_id(self):
        for record in self:
            if record.journal_id:
                record.currency_id = record.journal_id.currency_id or record.journal_id.company_id.currency_id

    def set_draft_status(self):
        self.status = 'draft'
        self.clear_countered_data()
        return True

    def set_waiting_for_head_status(self):
        self.generate_move_name()
        self.status = 'waiting_for_head'
        self.clear_wizard_data()
        if self.document_date is False:
            self.document_date = datetime.now().date()
        self.send_edts_status_update_email()
        return True

    def set_waiting_for_accounting_status(self):
        self.status = 'waiting_for_accounting'
        if self.edts_subtype in ['return']:
            self.generate_move_name()
            self.clear_wizard_data()
            if self.document_date is False:
                self.document_date = datetime.now().date()
        self.send_edts_status_update_email()
        return True

    def set_processing_accounting_status(self):
        self.status = 'processing_accounting'
        self.send_edts_status_update_email()
        return True

    def set_processing_finance_status(self):
        self.status = 'processing_finance'
        self.posting_date = datetime.now().date()
        self.send_edts_status_update_email()
        return True

    def set_partial_payment_released_status(self):
        self.status = 'partial_payment_released'
        self.send_edts_status_update_email()
        return True

    def set_fully_paid_status(self):
        self.status = 'fully_paid'
        self.send_edts_status_update_email()
        return True

    def set_done_status(self):
        self.status = 'done'
        self.posting_date = datetime.now().date()
        self.fund_returned_date = datetime.now()
        self.fund_returned_by = self._uid
        self.send_edts_status_update_email()
        return True


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    posting_key = fields.Char(string='Posting Key')
    description = fields.Char(string='Description')
    text = fields.Char(string='Text')
    cash_flow_code = fields.Char(string='Cash Flow Code')

    @api.onchange('cash_flow_code')
    def onchange_edts_cash_flow_code(self):
        for record in self:
            if record.cash_flow_code:
                record.cash_flow_code_lookup()

    def cash_flow_code_lookup(self):
        headers, conn, prefix = self.move_id.get_api_config()

        conn.request("GET", f"{prefix}CashFlowLookUp?SapClientId={'%s'}&Code={'%s'}"
                     % (self.move_id.sap_client_id, self.cash_flow_code), [],
                     headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)

        if 'Errors' in json_data or ('status' in json_data and json_data.get('status') in ['Error']):
            raise Warning(json_data.get('Errors') or json_data.get('message'))


class AccountAccountInherit(models.Model):
    _inherit = 'account.account'

    company_code = fields.Char(string='Company Code')

    @api.model
    def create(self, vals):
        record = super(AccountAccountInherit, self).create(vals)
        record.onchange_edts_company_code()
        return record

    @api.onchange('company_code')
    def onchange_edts_company_code(self):
        for record in self:
            if record.company_code:
                company = self.env['res.company'].sudo().search([('code', '=', record.company_code)], limit=1)
                if company[:1]:
                    record.company_id = company.id

    @api.onchange('company_id')
    def onchange_edts_company_id(self):
        for record in self:
            if record.company_id:
                company = self.env['res.company'].sudo().search([('id', '=', record.company_id.id)], limit=1)
                if company[:1]:
                    record.company_code = company.code




