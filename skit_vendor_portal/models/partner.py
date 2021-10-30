# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from ast import literal_eval
from odoo import fields, models, api, _
from odoo.http import request
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    agree = fields.Boolean(string="Agree")
    company_code = fields.Char(string="Company Code", track_visibility="always")
    sales_account_number = fields.Char(string="Sale Account Number", track_visibility="always")
    
    @api.constrains('email')
    def _check_duplicate_email(self):
        for rec in self:
            emails = self.env['res.partner'].sudo().search([('email', '=', rec.email), ('id', '!=', rec.id)], limit=1)
            if emails[:1]:
                raise ValidationError("Email address is already registered. Please make sure to only use 1 email address per Vendor registration.If you have any queries, you may contact your designated Purchasing Officer.")

    def send_portal_vendor_mail(self, user):
        """send reset password mail"""
        # determine subject and body in the portal user's language
        template = self.env.ref('skit_vendor_portal.mail_template_vendor_portal_welcome_mail')
        partner = user.partner_id
        portal_url = partner.with_context(signup_force_type_in_url='reset')._get_signup_url_for_action()[partner.id]
        partner.sudo().signup_prepare(signup_type='reset')
        if template:
            template.send_mail(user.id, force_send=True)
        else:
            _logger.warning("No email template found for sending email to the portal user")
        return True
    
    def notify_vendor_creation(self, user):
        """send reset password mail"""
        # determine subject and body in the portal user's language
        template = self.env.ref('skit_vendor_portal.mail_template_notify_user')
        notify_user = self.env['res.users'].search(
                [('groups_id', 'in', self.env.ref('skit_vendor_portal.group_vendor_portal_notify_user').ids)])
       
        for us in notify_user: 
            email_values = {
                        'email_to': us.partner_id.email_formatted,
                    }    
            if template:
                template.with_context({'group_user':us}).send_mail(user.id, force_send=True, email_values=email_values)
            else:
                _logger.warning("No email template found for sending email to the User")
        return True
    
    def is_vportal_customer(self):
        property_sale = self.env['property.admin.sale'].search_count([('partner_id', '=', self.id)])
        if self.partner_assign_number or property_sale > 0:
            return True
        return False
    
    def is_vportal_vendor(self):
        rfi = self.env['admin.request.for.information.line'].search_count([('partner_id', '=', self.id)])
        rfq = self.env['admin.vendor.rfq'].search_count([('partner_id', '=', self.id)])
        rfp = self.env['admin.request.for.proposal.line'].search_count([('partner_id', '=', self.id)])
        bidding = self.env['purchase.bid.vendor'].search_count([('partner_id', '=', self.id)])
        po = self.env['purchase.order'].search_count([('partner_id', '=', self.id)])
        vendor_si = self.env['admin.sales.invoice'].search_count([('vendor_partner_id', '=', self.id)]) 
        dr = self.env['po.delivery.line'].search_count([('partner_id', '=', self.id)])
        payment_release = self.env['admin.invoice.payment'].search_count([('vendor_partner_id', '=', self.id)]) 
        if self.universal_vendor_code or self.sales_account_number or self.supplier_number or self.registration_date or self.date_accredited or (
                    rfi > 0 or rfq > 0 or rfp > 0 or bidding > 0 or po > 0 or vendor_si > 0 or dr > 0 or payment_release >0):
            return True
        return False


class ProductServiceOffered(models.Model):
    _inherit = 'product.service.offered'

    @api.model
    def create(self, vals):
        if vals.get('attachment_ids'):
            attachment_ids = literal_eval(vals.get('attachment_ids'))
            vals.update({'attachment_ids': [[6, 0, attachment_ids]]})
        res = super(ProductServiceOffered, self).create(vals)
        if res.attachment_ids:
            res.attachment_ids.write({'res_id': res.id})
        return res


class PurchaseBidVendor(models.Model):
    _inherit = 'purchase.bid.vendor'

    bid_ref_no = fields.Char(related='bid_id.name', string='Bid Ref.No')
    
    
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    @api.constrains('login', 'website_id')
    def _check_login(self):
        """ Do not allow two users with the same login without website """
        self.flush(['login', 'website_id'])
        self.env.cr.execute(
            """SELECT login
                 FROM res_users
                WHERE login IN (SELECT login FROM res_users WHERE id IN %s AND website_id IS NULL)
                  AND website_id IS NULL
             GROUP BY login
               HAVING COUNT(*) > 1
            """,
            (tuple(self.ids),)
        )
        if self.env.cr.rowcount:
            raise ValidationError(_('Email address is already registered. Please make sure to only use 1 email address per Vendor registration. \n\n'
                                     'If you have any queries, you may contact your designated Purchasing Officer.'
                                    ))

      
class PortalMixin(models.AbstractModel):
    _inherit = "portal.mixin"
    
    def _notify_get_groups(self, msg_vals=None):
        access_token = self._portal_ensure_token()
        #groups = super(PortalMixin, self)._notify_get_groups(msg_vals=msg_vals)
        groups = [
            (
                'user',
                lambda pdata: pdata['type'] == 'user',
                {}
            ), (
                'portal',
                lambda pdata: pdata['type'] == 'portal',
                {'has_button_access': False}
            ), (
                'customer',
                lambda pdata: True,
                {'has_button_access': False}
            )
        ]
        msg_vals = msg_vals or {}
        allow_signup = self.env['res.users']._get_signup_invitation_scope() == 'b2c'
        if access_token and 'partner_id' in self._fields and self['partner_id'] and allow_signup:
            customer = self['partner_id']
            msg_vals['access_token'] = self.access_token
            msg_vals.update(customer.signup_get_auth_param()[customer.id])
            access_link = self._notify_get_action_link('view', **msg_vals)

            new_group = [
                ('portal_customer', lambda pdata: pdata['id'] == customer.id, {
                    'has_button_access': False,
                    'button_access': {
                        'url': access_link,
                    },
                })
            ]
        else:
            new_group = []
        return new_group + groups
