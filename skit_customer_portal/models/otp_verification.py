# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class OTPVerification(models.Model):
    _name = 'customer.portal.otp.verification'

    otp = fields.Char(string="OTP Number")
    email = fields.Char(string="Email")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def clear_otp_datas(self):
        otp_verification = self.env['customer.portal.otp.verification']
        customer_portal_otp = otp_verification.sudo().search([])
        current_date = datetime.utcnow()
        for otp in customer_portal_otp:
            user_time_zone = pytz.UTC
            if self.env.user.partner_id.tz:
                user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
            cdate = (otp.create_date).strftime("%Y-%m-%d %H:%M:%S")
            utc = datetime.strptime(cdate, DEFAULT_SERVER_DATETIME_FORMAT)
            utc = utc.replace(tzinfo=pytz.UTC)
            user_time = utc.astimezone(user_time_zone).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)
            cutc = (current_date).strftime("%Y-%m-%d %H:%M:%S")
            current_utc = datetime.strptime(cutc, DEFAULT_SERVER_DATETIME_FORMAT)
            current_utc = current_utc.replace(tzinfo=pytz.UTC)
            currect_user_time = current_utc.astimezone(user_time_zone).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)
            currect_utc_date = datetime.strptime(currect_user_time, '%Y-%m-%d %H:%M:%S')
            otp_create_date = datetime.strptime(user_time, '%Y-%m-%d %H:%M:%S')
            diff = currect_utc_date - otp_create_date
            seconds = diff.total_seconds()
            if(seconds >3600):
                otp.unlink()
        return True


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        """ signup a user, to either:
            - create a new user (no token), or
            - create a user for a partner (with token, but no user for partner), or
            - change the password of a user (with token, and existing user).
            :param values: a dictionary with field values that are written on user
            :param token: signup token (optional)
            :return: (dbname, login, password) for the signed up user
        """
        if token:
            # signup with a token: find the corresponding partner id
            partner = self.env['res.partner']._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
            # invalidate signup token
            # partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})

            partner_user = partner.user_ids and partner.user_ids[0] or False

            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)

            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                if not partner_user.login_date:
                    partner_user._notify_inviter()
                return (self.env.cr.dbname, partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                partner_user = self._signup_create_user(values)
                partner_user._notify_inviter()
        else:
            # no token, sign up an external user
            values['email'] = values.get('email') or values.get('login')
            self._signup_create_user(values)

        return (self.env.cr.dbname, values.get('login'), values.get('password'))

