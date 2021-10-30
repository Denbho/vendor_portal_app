# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, timedelta, datetime


class Website(models.Model):
    _inherit = 'website'

    captcha_sitekey = fields.Char()
    captcha_secretkey = fields.Char()
    
    def date_by_adding_business_days(self,from_date, add_days):
        if from_date:
            business_days_to_add = add_days + 1
            current_date = from_date
           # date_1 = datetime.datetime.strptime(current_date, "%y-%m-%d")
            while business_days_to_add > 0:
                current_date += timedelta(days=1)
                weekday = current_date.weekday()
                if weekday >= 5: # sunday = 6
                    continue
                business_days_to_add -= 1
            return current_date.strftime("%B %d, %Y")

    def get_date(self, m_date):
        message_date = (m_date).strftime("%Y-%m-%d")
        date_object = datetime.strptime(message_date, '%Y-%m-%d').date()
        today = date.today()
        yesterday = date.today() - timedelta(days = 1)
        if(date_object == today):
            data = 'Today'
        elif(date_object == yesterday):
            data = 'Yesterday'
        else:
            data = message_date
        return data


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    captcha_sitekey = fields.Char(
        string="Recaptcha Site Key",
        related='website_id.captcha_sitekey',
        readonly=False,
    )
    captcha_secretkey = fields.Char(
        string="Recaptcha Secret Key",
        related='website_id.captcha_secretkey',
        readonly=False,
    )
