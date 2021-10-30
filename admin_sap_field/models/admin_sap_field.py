# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AdminPurchaseRequisition(models.Model):
    _inherit = 'admin.purchase.requisition'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('admin_pr_unique_key', 'unique(name, sap_client_id)', "PR No. must be unique per client ID!"),
    ]

class PurchaseRequisitionMaterialDetails(models.Model):
    _inherit = 'purchase.requisition.material.details'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('admin_pr_line_unique_key', 'unique(request_id_name, sap_client_id, pr_line_item_code)',
        "PR Line must be unique per PR No., clien ID and line item code!"),
    ]

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('admin_po_unique_key', 'unique(name, sap_client_id)', "PO No. must be unique per client ID!"),
    ]

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('admin_po_line_unique_key', 'unique(po_number, sap_client_id, po_line_code)',
        "PO line must be unique per PO No., client ID and PO line code!"),
    ]

class PODeliveryLine(models.Model):
    _inherit = 'po.delivery.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('admin_drgr_unique_key', 'unique(gr_number, sap_client_id, po_id, gr_year)',
        "DR/GR must be unique per GR No., PO No., client ID and gr year!"),
    ]

class PODeliveryProductLine(models.Model):
    _inherit = 'po.delivery.product.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('admin_drgr_line_unique_key', 'unique(gr_number, sap_client_id, po_id, gr_year, po_line_code)',
        "DR/GR line must be unique per GR No., PO No., PO line code, client ID and gr year!"),
    ]

class AdminSalesInvoice(models.Model):
    _inherit = 'admin.sales.invoice'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AdminInvoicePayment(models.Model):
    _inherit = 'admin.invoice.payment'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ContractsAndAgreements(models.Model):
    _inherit = 'contracts.and.agreements'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ContractsAndAgreementsInclusion(models.Model):
    _inherit = 'contracts.and.agreements.inclusion'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class Company(models.Model):
    _inherit = 'res.company'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AcctAssignmentCategory(models.Model):
    _inherit = 'acct.assignment.category'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PurchaseRequisitioner(models.Model):
    _inherit = 'purchase.requisitioner'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PurchasingGroup(models.Model):
    _inherit = 'purchasing.group'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class LocationPlant(models.Model):
    _inherit = 'location.plant'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class StockLocation(models.Model):
    _inherit = 'stock.location'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PRDocumentType(models.Model):
    _inherit = 'pr.document.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PODocumentType(models.Model):
    _inherit = 'admin.po.document.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class MaterialGroups(models.Model):
    _inherit = 'product.category'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class UnitsofMeasure(models.Model):
    _inherit = 'uom.uom'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class UnitsofMeasureCategories(models.Model):
    _inherit = 'uom.category'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    company_code = fields.Char(string="Company Code")
    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.model
    def create(self, values):
        res = super(AccountAnalyticAccount, self).create(values)
        res.onchange_company_code()
        return res
