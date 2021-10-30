# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning, ValidationError


class ResPartnerExtend(models.Model):
    _name = 'res.partner.extend'
    _inherit = ['mail.thread', 'mail.activity.mixin', "document.default.approval"]
    _description = 'Extending vendor to other client'

    name = fields.Char(string="Request Number", copy=False, readonly=True, index=True,
                       default=lambda self: _('New'), track_visibility="always")
    partner_id = fields.Many2one('res.partner', string="Vendor", domain="[('universal_vendor_code', 'not in', [False]), ('is_blocked','=',False)]", required=True, track_visibility="always")
    vendor_code_113 = fields.Char(string='Vendor Code 113', related="partner_id.vendor_code_113", store=True)
    vendor_code_303 = fields.Char(string='Vendor Code 303', related="partner_id.vendor_code_303", store=True)
    universal_vendor_code = fields.Char(string='Universal Vendor Code', related="partner_id.universal_vendor_code", index=True, store=True)
    extend_to_client = fields.Selection([('113', '113'), ('303', '303')], string="Extend to Clienf Server", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    company_code = fields.Char(string="Company Code", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string="Company", domain="[('sap_client_id', '=', extend_to_client)]", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    purchase_org_id = fields.Many2one('admin.purchase.organization', string="Purchase Organization", required=True, readonly=True, states={'draft': [('readonly', False)]})
    vendor_account_group_id = fields.Many2one('vendor.account.group', string="Account Group", required=True, readonly=True, states={'draft': [('readonly', False)]})
    note = fields.Text(string="Notes", states={'approved': [('readonly', True)]})
    state = fields.Selection(selection_add=[('rejected', 'Rejected')])

    def btn_reject(self):
        self.state = 'rejected'

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code
            
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('vendor.client.extend')
        return super(ResPartnerExtend, self).create(vals)

    @api.onchange('company_code', 'extend_to_client')
    def onchange_company_code(self):
        if self.company_code and self.extend_to_client:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code), ('sap_client_id', '=', self.extend_to_client)], limit=1)
            if company[:1]:
                self.company_id = company.id
            else:
                raise ValidationError(_(f"No Company Code {self.company_code} related to {self.extend_to_client} Found."))

    @api.constrains('company_code', 'extend_to_client', 'partner_id', 'state')
    def validate_data(self):
        if self.company_code and self.extend_to_client:
            if self.env['res.company'].sudo().search_count([('code', '=', self.company_code), ('sap_client_id', '=', self.extend_to_client)]) == 0:
                raise ValidationError(
                    _(f"No Company Code {self.company_code} related to {self.extend_to_client} Found."))
        data = self.sudo().search([
                                                ('company_code', '=', self.company_code),
                                                ('extend_to_client', '=', self.extend_to_client),
                                                ('partner_id', '=', self.partner_id.id),
                                                ('state', 'not in', ['rejected', 'canceled']),
                                                ('id', '!=', self.id)
                                            ], limit=1)
        if data[:1]:
            raise ValidationError(_(f"The same request are still in process. see {self.name}"))


