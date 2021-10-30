# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.helpdesk.controllers.rating import WebsiteHelpdesk


class WebsiteHelpdesk(WebsiteHelpdesk):

    @http.route(['/helpdesk/rating'], type='http', auth="public", website=True)
    def index(self, **kw):
        if request.env.user.partner_id == request.env.ref('base.public_partner'):
            return http.local_redirect('/web/login')
        response = super(WebsiteHelpdesk, self).index(**kw)
        return response
