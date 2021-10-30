from odoo import http
from odoo.http import request
from odoo.addons.website_form.controllers.main import WebsiteForm


class WebsiteForm(WebsiteForm):

    @http.route('''/helpdesk/<model("helpdesk.team", "[('use_website_helpdesk_form','=',True)]"):team>/submit''', type='http', auth="public", website=True)
    def website_helpdesk_form(self, team, **kwargs):
        if request.env.user.partner_id == request.env.ref('base.public_partner'):
            return http.local_redirect('/web/login')
        response = super(WebsiteForm, self).website_helpdesk_form(team, **kwargs)
        partner = request.env.user.partner_id
        property_sale = request.env['property.admin.sale']
        property_sales = property_sale.sudo().search([('partner_id',
                                                       '=',
                                                       partner.id)])
        ticket_types = request.env['helpdesk.ticket.type'].sudo().search([])
        response.qcontext.update({
            'property_sales': property_sales,
            'ticket_types': ticket_types
            })
        return response

    @http.route('/website_form/<string:model_name>',
                type='http',
                auth="public",
                methods=['POST'],
                website=True)
    def website_form(self, model_name, **kwargs):
        formbuilder_whitelist = []
        if (request.params.get('property_sale_id')):
            formbuilder_whitelist.append('property_sale_id')
        if(request.params.get('so_number')):
            formbuilder_whitelist.append('so_number')
        if(request.params.get('ticket_type_id')):
            formbuilder_whitelist.append('ticket_type_id')
        if len(formbuilder_whitelist):
            # request.env['ir.model.fields'].formbuilder_whitelist('helpdesk.ticket', ['property_sale_id', 'so_number'])
            # the ORM only allows writing on custom fields and will trigger a
            # registry reload once that's happened. We want to be able to
            # whitelist non-custom fields and the registry reload absolutely
            # isn't desirable, so go with a method and raw SQL
            request.env.cr.execute(
                "UPDATE ir_model_fields"
                " SET website_form_blacklisted=false"
                " WHERE model=%s AND name in %s", (model_name, tuple(formbuilder_whitelist)))
        if request.params.get('partner_email'):
            Partner = request.env['res.partner'].sudo().search([('email',
                                                                 '=',
                                                                 kwargs.get('partner_email'))], limit=1)
            if Partner:
                request.params['partner_id'] = Partner.id
        return super(WebsiteForm, self).website_form(model_name, **kwargs)
