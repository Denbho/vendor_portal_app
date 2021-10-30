# -*- coding: utf-8 -*-

import logging
import math
import random

from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class LoginHome(Home):

    @http.route('/web/login', type='http', auth="public", sitemap=False)
    def web_login(self, redirect=None, **kw):
        values = request.params.copy()
        login = request.params.get('login')
        res_users = request.env['res.users']
        portal_user = request.params.get('portal')
        current_user = res_users.sudo().search([('login', '=', login)])
        partner = request.env['res.partner'].sudo().search([('id','=',current_user.partner_id.id)])
        if (current_user.has_group('base.group_portal')):
            if portal_user=="customer":
                if not partner.is_vportal_customer():
                    values['login'] = request.params.get('login')
                    values['error'] = current_user.name+" is not a customer."
                    response = request.render('skit_customer_portal.login', values)
                    request.params['login_success'] = False
                    return response
            elif portal_user=="vendor":
                if not partner.is_vportal_vendor():
                    values['login'] = request.params.get('login')
                    values['error'] = current_user.name+" is not a vendor."
                    response = request.render('skit_customer_portal.login', values)
                    request.params['login_success'] = False
                    return response
            if(login and (not request.params.get('otp'))):
                request.session['portaluser'] = portal_user
                otp_verification = request.env['customer.portal.otp.verification']
                self.otp_verification(login, current_user)
                values['login'] = request.params.get('login')
                values['password'] = request.params.get('password')
                values['show_otp'] = "otp"
                values['message'] = "OTP has been sent to your email address"
                values['error'] = "OTP will expire in 1 hour"
                response = request.render('skit_customer_portal.otp_login', values)
                request.params['login_success'] = False
                return response
            elif request.params.get('otp'):
                try:
                    otp_verification = request.env['customer.portal.otp.verification']
                    customer_portal_otp = otp_verification.sudo().search([
                        ('email', '=', request.params.get('login')),
                        ('otp', '=', request.params.get('otp'))])
                    if not customer_portal_otp:
                        request.params['login_success'] = False
                        values['login'] = request.params.get('login')
                        values['show_otp'] = "otp"
                        values['error'] = "Wrong OTP Number."
                        raise ValidationError(_("Wrong OTP Number."))
                    else:
                        partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})
                        return super(LoginHome, self).web_login(redirect="/my/dashboard", **kw)
                        # if partner.supplier_rank==1:
                        #     return super(LoginHome, self).web_login(redirect="/my/dashboard", **kw)
                        # else:
                        #     #return super(LoginHome, self).web_login(redirect="/my/property_sales", **kw)
                        #     return super(LoginHome, self).web_login(redirect="/my/dashboard", **kw)
                except Exception as e:
                    response = request.render('skit_customer_portal.otp_login', values)
                    response.headers['X-Frame-Options'] = 'DENY'
                    return response
        else:
            ensure_db()
            response = super(LoginHome, self).web_login(redirect=None, **kw)
            return response

    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signup(values, token)
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        ## Commented below code to stop signin before OTP verification
        #uid = request.session.authenticate(db, login, password)
        #if not uid:
         #   raise SignupError(_('Authentication Failed.'))

#     @http.route('/web/login_otp', type='http', auth="public", website=True, sitemap=False)
#     def web_login_otp(self, redirect=None, **kw):
#
#         if request.params.get('otp'):
#             values = request.params.copy()
#             try:
#                 otp_verification = request.env['customer.portal.otp.verification']
#                 customer_portal_otp = otp_verification.sudo().search([
#                     ('email', '=', request.params.get('login')),
#                     ('otp', '=', request.params.get('otp'))])
#                 if not customer_portal_otp:
#                     request.params['login_success'] = False
#                     values['login'] = request.params.get('login')
#                     values['show_otp'] = "otp"
#                     values['error'] = "Wrong OTP Number."
#                     raise ValidationError(_("Wrong OTP Number."))
#                 else:
#                     uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
#                     return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
#             except Exception as e:
#                 response = request.render('skit_customer_portal.otp_login', values)
#                 response.headers['X-Frame-Options'] = 'DENY'
#                 return response

class CustomerPortalAuthSignupHome(Home):

    @http.route(['/resend/otp'], type='json', auth="public", methods=['POST'],
                website=True, csrf=False)
    def resend_otp(self, **post):
        """ Re-send OTP """
        login = post.get('login')
        user_sudo = request.env['res.users'].sudo().search([('login', '=', login)])
        if user_sudo:
            self.otp_verification(login, user_sudo)
        return True

    def otp_verification(self, login, user_sudo):
        otp_verification = request.env['customer.portal.otp.verification']
        digits = "0123456789"
        otp_no = ""
        for i in range(6):
            otp_no += digits[math.floor(random.random() * 10)]
        customer_portal_otp = otp_verification.sudo().create(
                    {'email': login,
                     'otp': otp_no})
        template = request.env.ref('skit_customer_portal.customer_portal_otp_verification', raise_if_not_found=False)
        mail_template = request.env['mail.template'].sudo().browse(template.id)
        mail_template.write({
                    'email_to': user_sudo.email
                })
        mail_id = mail_template.send_mail(customer_portal_otp.id, force_send=True)
        mail_mail_obj = request.env['mail.mail'].sudo().search(
                        [('id', '=', mail_id)]
                        )
        mail_mail_obj.send()

    def _login_redirect(self, uid, redirect=None):
        """Inherited to redirect the portal page after user logged in"""
        if not redirect and not request.env['res.users'].sudo().browse(uid).has_group('base.group_user'):
            return '/my/property_sales'
        return super(LoginHome, self)._login_redirect(uid, redirect=redirect)
