# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
import pytz

from odoo import http, _, fields
from odoo.http import request
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.addons.website_calendar.controllers.main import WebsiteCalendar


class WebsiteCalendar(WebsiteCalendar):

    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/info'],
                type='http',
                auth="public",
                website=True)
    def calendar_appointment_form(self,
                                  appointment_type,
                                  employee_id,
                                  date_time,
                                  **kwargs):
        """ Inherited to list the property sales of the logged in partner"""
        response = super(WebsiteCalendar, self).calendar_appointment_form(appointment_type,
                                                                          employee_id,
                                                                          date_time,
                                                                          **kwargs)
        partner = request.env.user.partner_id
        property_admin_sale = request.env['property.admin.sale']
        property_sales = property_admin_sale.sudo().search([('partner_id',
                                                             '=',
                                                             partner.id)])
        response.qcontext.update({
                'property_sales': property_sales
            })
        return response

    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/submit'],
                type='http',
                auth="public",
                website=True,
                method=["POST"])
    def calendar_appointment_submit(self,
                                    appointment_type,
                                    datetime_str,
                                    employee_id,
                                    name,
                                    phone,
                                    email,
                                    country_id=False,
                                    **kwargs):
        """ Inherited to add property sale in the calendar event"""
        timezone = request.session['timezone']
        tz_session = pytz.timezone(timezone)
        date_start = tz_session.localize(fields.Datetime.from_string(datetime_str)).astimezone(pytz.utc)
        date_end = date_start + relativedelta(hours=appointment_type.appointment_duration)

        # check availability of the employee again (in case someone else booked while the client was entering the form)
        Employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if Employee.user_id and Employee.user_id.partner_id:
            if not Employee.user_id.partner_id.calendar_verify_availability(date_start, date_end):
                return request.redirect('/website/calendar/%s/appointment?failed=employee' % appointment_type.id)

        country_id = int(country_id) if country_id else None
        country_name = country_id and request.env['res.country'].browse(country_id).name or ''
        Partner = request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)
        if Partner:
            if not Partner.calendar_verify_availability(date_start, date_end):
                return request.redirect('/website/calendar/%s/appointment?failed=partner' % appointment_type.id)
            if not Partner.mobile or len(Partner.mobile) <= 5 and len(phone) > 5:
                Partner.write({'mobile': phone})
            if not Partner.country_id:
                Partner.country_id = country_id
        else:
            Partner = Partner.create({
                'name': name,
                'country_id': country_id,
                'mobile': phone,
                'email': email,
            })

        description = (_('Country: %s') + '\n' +
                       _('Mobile: %s') + '\n' +
                       _('Email: %s') + '\n') % (country_name, phone, email)
        for question in appointment_type.question_ids:
            key = 'question_' + str(question.id)
            if question.question_type == 'checkbox':
                answers = question.answer_ids.filtered(lambda x: (key + '_answer_' + str(x.id)) in kwargs)
                description += question.name + ': ' + ', '.join(answers.mapped('name')) + '\n'
            elif kwargs.get(key):
                if question.question_type == 'text':
                    description += '\n* ' + question.name + ' *\n' + kwargs.get(key, False) + '\n\n'
                else:
                    description += question.name + ': ' + kwargs.get(key) + '\n'

        categ_id = request.env.ref('website_calendar.calendar_event_type_data_online_appointment')
        alarm_ids = appointment_type.reminder_ids and [(6, 0, appointment_type.reminder_ids.ids)] or []
        partner_ids = list(set([Employee.user_id.partner_id.id] + [Partner.id]))
        property_sale_id = kwargs.get('property_sale_id')
        property_sale_id = int(property_sale_id) if property_sale_id else None
        event = request.env['calendar.event'].sudo().create({
            'state': 'open',
            'name': _('%s with %s') % (appointment_type.name, name),
            'start': date_start.strftime(dtf),
            # FIXME master
            # we override here start_date(time) value because they are not properly
            # recomputed due to ugly overrides in event.calendar (reccurrencies suck!)
            #     (fixing them in stable is a pita as it requires a good rewrite of the
            #      calendar engine)
            'start_date': date_start.strftime(dtf),
            'start_datetime': date_start.strftime(dtf),
            'stop': date_end.strftime(dtf),
            'stop_datetime': date_end.strftime(dtf),
            'allday': False,
            'duration': appointment_type.appointment_duration,
            'description': description,
            'alarm_ids': alarm_ids,
            'location': appointment_type.location,
            'partner_ids': [(4, pid, False) for pid in partner_ids],
            'categ_ids': [(4, categ_id.id, False)],
            'appointment_type_id': appointment_type.id,
            'user_id': Employee.user_id.id,
            'property_sale_id': property_sale_id,
        })
        event.attendee_ids.write({'state': 'accepted'})
        return request.redirect('/website/calendar/view/' + event.access_token + '?message=new')

    @http.route([
        '/website/calendar',
        '/website/calendar/<model("calendar.appointment.type"):appointment_type>',
    ], type='http', auth="public", website=True)
    def calendar_appointment_choice(self,
                                    appointment_type=None,
                                    employee_id=None,
                                    message=None,
                                    **kwargs):
        if request.env.user.partner_id == request.env.ref('base.public_partner'):
            return http.local_redirect('/web/login')
        response = super(WebsiteCalendar, self).calendar_appointment_choice(appointment_type,
                                                                            employee_id,
                                                                            message,
                                                                            **kwargs)
        appointment_type_id = response.qcontext['appointment_type'].id
        partner = request.env.user.partner_id
        domain = [('partner_ids', 'in', partner.id),
                  ('appointment_type_id', '=', appointment_type_id)]
        calendar_event = request.env['calendar.event'].sudo().search(domain)
        response.qcontext.update({
                'calendar_event': calendar_event
            })
        return response

    @http.route(['/website/calendar/get_appointment_info'], type='json', auth="public", methods=['POST'], website=True)
    def get_appointment_info(self, appointment_id, prev_emp=False, **kwargs):
        result = super(WebsiteCalendar, self).get_appointment_info(appointment_id,
                                                                   prev_emp,
                                                                   **kwargs)
        partner = request.env.user.partner_id
        domain = [('partner_ids', 'in', partner.id),
                  ('appointment_type_id', '=', int(appointment_id))]
        calendar_event = request.env['calendar.event'].search(domain)
        scheduled_appointment_table = request.env.ref('skit_customer_portal.scheduled_appointment_table')
        result['calendar_event_table_html'] = scheduled_appointment_table.render({
                'calendar_event': calendar_event,
            })
        return result
