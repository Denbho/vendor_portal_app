# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import http
import json
import logging

_logger = logging.getLogger("_name_")


class Company(models.Model):
    _inherit = 'res.company'

    _sql_constraints = [
        ('company_code', 'unique(code)',
         'The "Company Code" field  must have unique value per Sap Severs!')]

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class Contact(models.Model):
    _inherit = 'res.partner'

    sap_client_id = fields.Integer(string="Client ID", default=lambda self: self.env.company.sap_client_id, index=True)
    partner_assign_number = fields.Char(string="Customer Number", help="Unique Customer Number", index=True)
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")
    universal_assign_number = fields.Char(string="UCN", help="Universal Customer Number", store=True,
                                          compute="_get_ucn")

    @api.depends('sap_client_id', 'partner_assign_number')
    def _get_ucn(self):
        for i in self:
            if i.sap_client_id and i.partner_assign_number:
                i.universal_assign_number = f"{i.sap_client_id}_{i.partner_assign_number}"

    @api.constrains('partner_assign_number', 'sap_client_id', 'sales_account_number', 'supplier_number')
    def check_dups_partner_assign_number(self):
        if self.partner_assign_number and self.sap_client_id:
            dup = self.sudo().search([('id', '!=', self.id), ('partner_assign_number', '=', self.partner_assign_number),
                                      ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if dup[:1]:
                raise ValidationError(
                    _(f'The "Unique Customer Number": {self.partner_assign_number} - {self.sap_client_id} field  must have unique value per Sap Severs!'))
        if self.sales_account_number and self.sap_client_id:
            dup = self.sudo().search([('id', '!=', self.id), ('sales_account_number', '=', self.sales_account_number),
                                      ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if dup[:1]:
                raise ValidationError(_('The "Sale Account Number" field  must have unique value per Sap Severs!'))
        if self.supplier_number and self.sap_client_id:
            dup = self.sudo().search([('id', '!=', self.id), ('supplier_number', '=', self.supplier_number),
                                      ('sap_client_id', '=', self.sap_client_id)], limit=1)
            if dup[:1]:
                raise ValidationError(_('Supplier Number" field  must have unique value per Sap Severs!'))

    # _sql_constraints = [
    #     ('partner_assign_number',
    #      'CHECK(partner_assign_number IS NOT NULL) AND unique(partner_assign_number, sap_client_id)',
    #      'The "Unique Customer Number" field  must have unique value per Sap Severs!'),
    #     ('partner_assign_number',
    #      'CHECK(sales_account_number IS NOT NULL) AND unique(sales_account_number, sap_client_id)',
    #      'The "Sale Account Number" field  must have unique value per Sap Severs!'),
    #     ('supplier_number',
    #      'CHECK(supplier_number IS NOT NULL) AND unique(supplier_number, sap_client_id)',
    #      'The "Supplier Number" field  must have unique value per Sap Severs!')
    # ]


class PropertyFinancingTypeTerm(models.Model):
    _inherit = 'property.financing.type.term'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyFinancingType(models.Model):
    _inherit = "property.financing.type"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyDownpaymentTerm(models.Model):
    _inherit = "property.downpayment.term"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleRequiredDocument(models.Model):
    _inherit = 'property.sale.required.document'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleCancellationReason(models.Model):
    _inherit = 'property.sale.cancellation.reason'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyStatusAssignedPerson(models.Model):
    _inherit = 'property.status.assigned.person'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleDocumentStatusBrand(models.Model):
    _inherit = 'property.sale.document.status.project'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleStatus(models.Model):
    _inherit = 'property.sale.status'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleStatus(models.Model):
    _inherit = 'property.sale.sub.status'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleBankLoanApplication(models.Model):
    _inherit = 'property.sale.bank.loan.application'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyAdminSale(models.Model):
    _inherit = 'property.admin.sale'

    sap_client_id = fields.Integer(string="Client ID", index=True)
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    def action_view_payments(self):
        self.ensure_one()
        res = super(PropertyAdminSale, self).action_view_payments()
        res['domain'] = [('so_number', '=', self.so_number), ('sap_client_id', '=', self.sap_client_id)]
        return res

    @api.onchange('customer_number', 'sap_client_id')
    def onchange_customer_number(self):
        contact = self.env['res.partner']
        if self.customer_number:
            partner = contact.search(
                [('partner_assign_number', '=', self.customer_number), ('sap_client_id', '=', self.sap_client_id)],
                limit=1)
            self.partner_id = partner[:1] and partner.id or False
            self.universal_assign_number = partner[:1] and partner.universal_assign_number or False

    def _get_payment_lines(self):
        payment = self.env['property.ledger.payment.item']
        for r in self:
            principal = 0
            interest = 0
            penalty = 0
            payment_history = payment.sudo().search(
                [('so_number', '=', r.so_number), ('sap_client_id', '=', self.sap_client_id)])
            r.payment_history_ids = payment_history
            for i in payment_history:
                principal += i.principal_amount
                interest += i.interest_amount
                penalty += i.sundry_amount
            r.total_penalty_paid = penalty
            r.total_principal_amount_paid = principal
            r.total_interest_amount_paid = interest
            r.grand_total_paid = sum([penalty, interest, principal])
            r.outstanding_balance = r.tcp - principal

    def get_so_payments_from_sap(self):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        conn = http.client.HTTPSConnection(api_key.api_url)
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        prefix = api_key.api_prefix
        conn.request("GET", f"{prefix}GetPayments?MANDT={self.sap_client_id}&VBELN={self.so_number}&BUKRS={self.company_code}", [],
                     headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        if json_data:
            payment = self.env['property.ledger.payment.item']
            for i in json_data:
                try:
                    data = {
                        'sap_client_id': str(i.get('Mandt')),
                        'so_number': i.get('Vbeln'),
                        'line_counter': i.get('Linecnt'),
                        'posting_date': i.get('Budat'),
                        'billing_number': i.get('Belnr'),
                        'reference_number': i.get('Refnum'),
                        'payment_amount': i.get('Payamt'),
                        'principal_amount': i.get('Principal'),
                        'interest_amount': i.get('Interest'),
                        'recap_amount': i.get('Recap'),
                        'sundry_amount': i.get('Sundry'),
                        'unpaid_amount': i.get('Unpaid'),
                        'running_bal': i.get('Runbal'),
                        'billing_amount': i.get('Bill_Amt'),
                        'billing_date': i.get('Fkdat'),
                        'clearing_document_ref': i.get('Augbl'),
                        'clearing_date': i.get('Augdt'),
                        'transaction_description': i.get('Descr'),
                        'reference_count': i.get('Refcnt'),
                        'reference_document_number': i.get('Xblnr'),
                        'document_type': i.get('Blart'),
                        'billing_type': i.get('Fkart'),
                        'payment_document_number': i.get('Belnr'),
                        'payment_posting_date': i.get('Budat'),
                        'or_number': i.get('Ryoshusho'),
                        'allocated_to_requirement': i.get('Alloc'),
                        'line_tagging': i.get('Tag'),
                        'restructure_amount': i.get('Restruc'),
                        'fiscal_year': i.get('Gjahr') and str(i.get('Gjahr')) or None,
                        'billing_due_date': i.get('Zfbdt'),
                        'accounting_date': i.get('Bldat'),
                        'amount_in_local_currency': i.get('Dmbtr'),
                        'so_assign_number': i.get('Zuonr'),
                        'customer_notes': i.get('Bsad'),
                        'bank_notes': i.get('Bseg'),
                        'total_amount': i.get('Total'),
                        'display_name': i.get('Ryoshusho'),
                        'customer_number': i.get('Kunnr'),
                        'sap_datetime_sync': datetime.now()
                    }
                    payment_rec = payment.sudo().create(data)
                except:
                    pass
        else:
            _logger.info(f"\n\nNo Payment Records\n\n")


class PropertySaleSOAOverdueLine(models.Model):
    _inherit = 'property.sale.soa.overdue.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleStatementOfAccount(models.Model):
    _inherit = 'property.sale.statement.of.account'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyLedgerPaymentItem(models.Model):
    _inherit = 'property.ledger.payment.item'
    _sql_constraints = [
        ('check_dups_so_payment', 'unique(so_number, sap_client_id, line_counter)',
         "Duplicate of payments is not allowed in the so number, client_id and line_counter!")
    ]

    line_counter = fields.Integer(string="Line Item Counter", index=True)
    sap_client_id = fields.Integer(string="Client ID", index=True)
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")
    customer_number = fields.Char(string="Customer #", index=True)
    so_number = fields.Char(string="SO #", required=True, index=True)
    property_sale_id = fields.Many2one('property.admin.sale', string="Property Sale", compute="_get_so_details")
    so_assign_number = fields.Char(string="Assignment #", help="SO Number sa SAP financial side", index=True)
    be_code = fields.Char(string="BE Code", help="Business Entity Code", compute="_get_so_details")
    partner_id = fields.Many2one('res.partner', string="Customer", compute="_get_partner")
    company_code = fields.Char(string="Company Code", index=True)
    company_id = fields.Many2one('res.company', 'Company', index=True,
                                 store=True, compute="_get_company_details", check_company=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")

    def _get_so_details(self):
        for r in self:
            if r.so_number and r.sap_client_id:
                property_sale = r.env['property.admin.sale'].sudo().search([('so_number', '=', r.so_number),
                                                                            ('sap_client_id', '=', r.sap_client_id)],
                                                                           limit=1)
                r.property_sale_id = property_sale[:1] and property_sale.id or False
                r.be_code = property_sale[:1] and property_sale.be_code or False

    def _get_partner(self):
        for r in self:
            contact = r.env['res.partner'].sudo().search([('partner_assign_number', '=', r.customer_number),
                                                          ('sap_client_id', '=', r.sap_client_id)], limit=1)
            r.partner_id = contact[:1] and contact.id or False

    @api.depends('company_code')
    def _get_company_details(self):
        company = self.env['res.company']
        for r in self:
            if r.company_code:
                rec = company.sudo().search([('code', '=', r.company_code)], limit=1)
                r.company_id = rec[:1] and rec.id or False

    # @api.constrains('so_number', 'sap_client_id', 'line_counter')
    # def check_dups_so_payment(self):
    #     if self.sap_client_id and self.sap_client_id and self.line_counter:
    #         dup = self.sudo().search(
    #             [('id', '!=', self.id), ('so_number', '=', self.so_number), ('sap_client_id', '=', self.sap_client_id),
    #              ('line_counter', '=', self.line_counter)], limit=1)
    #         if dup[:1]:
    #             raise ValidationError(
    #                 _('Duplicate of payments is not allowed in the so number, client_id and line_counter!'))
    #

class PropertyPriceRange(models.Model):
    _inherit = 'property.price.range'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyModelType(models.Model):
    _inherit = 'property.model.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyModelUnitType(models.Model):
    _inherit = 'property.model.unit.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class HousingModel(models.Model):
    _inherit = 'housing.model'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySubdivision(models.Model):
    _inherit = "property.subdivision"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySubdivisionPhase(models.Model):
    _inherit = "property.subdivision.phase"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyDetail(models.Model):
    _inherit = "property.detail"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    @api.onchange('material_number', 'subdivision_phase_id')
    def onchange_get_project_house_model(self):
        sap_client_id = self.subdivision_phase_id and self.subdivision_phase_id.sap_client_id or self.subdivision_phase_id.company_id.sap_client_id
        if self.material_number:
            house = self.env['housing.model'].search([('material_number', '=', self.material_number)], limit=1)
            if sap_client_id:
                house = self.env['housing.model'].search(
                    [('material_number', '=', self.material_number), ('sap_client_id', '=', sap_client_id)], limit=1)
            if house[:1]:
                self.house_model_id = house.id
                if house.model_type_id:
                    self.model_type_id = house.model_type_id.id
                if house.property_type:
                    self.property_type = house.property_type
