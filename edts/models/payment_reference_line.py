# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning, ValidationError
from datetime import datetime
import http
import json


UNABLE_TO_DELETE = 'Cannot delete payment that has already been released'
NO_API_CONFIG_WARNING = 'Please check SETTINGS and provide appropriate API CONFIG.'


class PaymentReferenceLine(models.Model):
    _name = 'edts.payment.reference.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EDTS Payment Reference Line'
    _rec_name = 'payment_doc'
    _order = 'id desc'

    account_move_id = fields.Many2one('account.move', string='Account Move', auto_join=True, ondelete='cascade', readonly=True)
    company_code = fields.Char(string='Company Code', related='account_move_id.company_code')
    currency_id = fields.Many2one('res.currency', string='Currency')
    ap_doc = fields.Char(string='AP Document', required=True)
    payment_doc = fields.Char(string='Payment Document', required=True)
    mode = fields.Selection([
        ('wire', 'Wire Transfer'),
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('check_writer', 'Check Writer'),
        ('debit_memo', 'Debit Memo'),
    ], string='Payment Mode', default=False, required=True)
    check_no = fields.Char(string='Check No.')
    check_date = fields.Date(string='Check Date')
    payment_amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    is_or_required = fields.Boolean(string='OR Required')
    is_payment_ready_for_releasing = fields.Boolean(string='For Releasing', default=True)

    payment_received_by = fields.Char(string='Payment Received By')
    payment_received_date = fields.Date(string='Payment Received Date')

    processed_by = fields.Char(string='Processed By', readonly=True)
    processed_date = fields.Date(string='Processed Date', readonly=True)

    released = fields.Boolean(string='Released', default=False, readonly=True)
    released_date = fields.Datetime(string='Released Date/Time', readonly=True)
    released_by = fields.Char(string='Released By', readonly=True)

    encashed = fields.Boolean(string='Encashed', default=False, readonly=True)
    encashed_date = fields.Datetime(string='Encashed Date/Time', readonly=True)
    encashed_by = fields.Char(string='Encashed By', readonly=True)

    or_number = fields.Char(string='OR No.')
    or_date = fields.Date(string='OR Date')

    released_api_remarks = fields.Char(string='Release Remarks')
    encashed_api_remarks = fields.Char(string='Encash Remarks')

    fiscal_year = fields.Char(string='Fiscal Year', default=datetime.now().year, readonly=True)

    def unlink(self):
        for r in self:
            if r.released:
                raise Warning(UNABLE_TO_DELETE)

        linked_records = self.sudo().search([('account_move_id', '=', self.account_move_id.id)]) if self.account_move_id else \
                         False

        if linked_records and linked_records == self:
            self.account_move_id.set_processing_finance_status()

        record = super(PaymentReferenceLine, self).unlink()
        return record

    @api.constrains('ap_doc')
    def _check_duplicate(self):
        for record in self:
            payments = self.env['edts.payment.reference.line'].search([('id', '!=', self.id), ('company_code', '=', record.company_code), ('fiscal_year', '=', record.fiscal_year), ('ap_doc', '=', record.ap_doc)])

            if payments:
                raise ValidationError('Company Code, Fiscal Year and AP Document must be unique')

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

    def edts_payment_released_via_api(self, **kwargs):
        self.released = True
        self.payment_received_by = kwargs.get('payment_received_by')
        self.payment_received_date = kwargs.get('payment_received_date')

        # Set Proper EDTS Status Based from Payments
        if self.account_move_id.status not in ['partial_payment_released'] and self.account_move_id.total_payment_amount < self.account_move_id.amount:
            self.account_move_id.set_partial_payment_released_status()
        elif self.account_move_id.status not in ['fully_paid'] and self.account_move_id.total_payment_amount >= self.account_move_id.amount:
            self.account_move_id.set_fully_paid_status()

        self.released_by = kwargs.get('released_by')
        self.released_date = kwargs.get('released_date')

        # Send Email that payment was successfully released
        if self.account_move_id.vendor_id:
            self.send_payment_released_email()

        return True

    def edts_payment_encashed_via_api(self, **kwargs):
        if self.released and self.mode in ['check', 'check_writer']:
            self.encashed = True
            self.encashed_date = kwargs.get('encashed_date')
            self.encashed_by = kwargs.get('encashed_by')

    def send_payment_released_email(self):
        template_id = self.env.ref('edts.email_template_edts_payment_released').id
        view_id = self.env.ref('edts.payment_reference_form').id

        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url += '/web#id=%d&view_type=form&view_id=%s&model=%s' % (self.id, view_id, self._name)

        context = {
            'url': url
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)

    def release_payment(self):
        view_id = self.env.ref('edts.payment_reference_received_by_form').id

        return {
            'name': 'Release',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'edts.payment.reference.line.wizard',
            'target': 'new',
            'context': {
                'default_payment_reference_line_id': self.id,
                'default_mode': self.mode,
            }
        }

    def release_payment_via_api(self):
        headers, conn, prefix = self.get_api_config()

        payload = {
            "Params": {
                "EdtsNo": self.account_move_id.name,
                "APDoc": self.ap_doc,
                "PayDoc": self.payment_doc,
                "Subtype": self.account_move_id.edts_subtype
            }
        }

        conn.request("POST", f"{prefix}PostReleaseDocument", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)
        self.released_api_remarks = json_data.get('message')

    def encash_payment(self):
        self.encashed = True
        self.encashed_date = datetime.now()
        self.encashed_by = self.env.user.name

    def encash_payment_via_api(self):
        headers, conn, prefix = self.get_api_config()

        payload = {
            "Params": {
                "EdtsNo": self.account_move_id.name,
                "APDoc": self.ap_doc,
                "PayDoc": self.payment_doc,
                "Subtype": self.account_move_id.edts_subtype
            }
        }

        conn.request("POST", f"{prefix}PostEncashDocument", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)
        self.encashed_api_remarks = json_data.get('message')

