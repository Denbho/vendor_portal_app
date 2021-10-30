import pytz
import werkzeug
import json
import logging
from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import vobject
except ImportError:
    _logger.warning("`vobject` Python module not found, iCal file generation disabled. Consider installing this module if you want to generate iCal files")
    vobject = None

GOOGLE_CALENDAR_URL = 'https://www.google.com/calendar/render?'


class Event(models.Model):
    _inherit = 'event.event'

    location = fields.Char(string="Meeting location")

    def _get_event_resource_urls(self):
        url_date_start = self.date_begin.strftime('%Y%m%dT%H%M%SZ')
        url_date_stop = self.date_end.strftime('%Y%m%dT%H%M%SZ')
        params = {
            'action': 'TEMPLATE',
            'text': self.name,
            'dates': url_date_start + '/' + url_date_stop,
            'details': self.name,
        }
        if self.location:
            params.update(location=self.sudo().location)
        elif self.address_id:
            params.update(location=self.sudo().address_id.contact_address.replace('\n', ' '))
        encoded_params = werkzeug.url_encode(params)
        google_url = GOOGLE_CALENDAR_URL + encoded_params
        iCal_url = '/event/%d/ics?%s' % (self.id, encoded_params)
        return {'google_url': google_url, 'iCal_url': iCal_url}

    def _get_ics_file(self):
        """ Returns iCalendar file for the event invitation.
            :returns a dict of .ics file content for each event
        """
        result = {}
        if not vobject:
            return result

        for event in self:
            cal = vobject.iCalendar()
            cal_event = cal.add('vevent')

            cal_event.add('created').value = fields.Datetime.now().replace(tzinfo=pytz.timezone('UTC'))
            cal_event.add('dtstart').value = fields.Datetime.from_string(event.date_begin).replace(tzinfo=pytz.timezone('UTC'))
            cal_event.add('dtend').value = fields.Datetime.from_string(event.date_end).replace(tzinfo=pytz.timezone('UTC'))
            cal_event.add('summary').value = event.name

            if self.location:
                cal_event.add('location').value = self.sudo().location            
            elif event.address_id:
                cal_event.add('location').value = event.sudo().address_id.contact_address

            result[event.id] = cal.serialize().encode('utf-8')
        return result
