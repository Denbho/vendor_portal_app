# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import base64
import requests


class CustomerPortal(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["phone", "street", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode",
                               "vat",
                               "company_name",
                               "image_1920",
                               "clear_image",
                               "partner_assign_number",
                               "function",
                               "mobile",
                               "website_link",
                               "title",
                               "date_of_birth",
                               "nationality_country_id",
                               "religion_id",
                               "age",
                               "monthly_income",
                               "mobile2",
                               "social_twitter",
                               "social_facebook",
                               "social_github",
                               "social_linkedin",
                               "social_youtube",
                               "social_instagram",
                               "gender",
                               "marital",
                               "employment_status_id",
                               "employment_country_id",
                               "profession_id",
                               "city_id",
                               "province_id",
                               "barangay_id",
                               "street2",
                               "state_id"
                               ]

    def _prepare_home_portal_values(self):
        """ Add Property Sale details to main account page """

        values = super(CustomerPortal, self)._prepare_home_portal_values()
        PropertySale = request.env['property.admin.sale']
        partner = request.env.user.partner_id
        domain = [('partner_id', '=', partner.id)]
        property_sale_count = PropertySale.search_count(domain) if PropertySale.check_access_rights('read', raise_exception=False) else 0
        values['property_sale_count'] = property_sale_count
#         so_number = request.session.get('selected_property_so_number')
#         if (so_number):
#             domain += [('so_number', '=', so_number)]
#         values['ticket_count'] = (
#             request.env['helpdesk.ticket'].search_count(domain)
#             if request.env['helpdesk.ticket'].check_access_rights('read', raise_exception=False)
#             else 0
#         )
        return values

    # ------------------------------------------------------------
    # My Property Sale
    # ------------------------------------------------------------
    def _property_sale_get_page_view_values(self,
                                            property_sale,
                                            access_token,
                                            **kwargs):

        PropertyAdminSale = request.env['property.admin.sale']
        values = PropertyAdminSale._get_property_info(property_sale.id)
        soa_history_ids = property_sale.soa_history_ids.ids
        # To Remove the latest SOA details from the history view
        if(property_sale.soa_id.id):
            soa_history_ids.remove(property_sale.soa_id.id)
        property_soa = request.env['property.sale.statement.of.account']
        soa_list = property_soa.sudo().search([('id', 'in', soa_history_ids)])
        values.update({
            'page_name': 'property_sale',
            'property_sale': property_sale,
            'is_show': True,
            'soa_ids': soa_list,
        })
        return self._get_page_view_values(property_sale,
                                          access_token,
                                          values,
                                          'my_property_sales_history',
                                          False,
                                          **kwargs)

    @http.route(['/my/property_sales',
                 '/my/property_sales/page/<int:page>',
                 '/my/property_sales/<int:stage_id>'],
                type='http',
                auth="user",
                website=True)
    def portal_my_property_sale_orders(self,
                                       page=1,
                                       stage_id=None,
                                       date_begin=None,
                                       date_end=None,
                                       sortby=None,
                                       filterby=None,
                                       **kw):
        # values = self._prepare_portal_layout_values()
        values = {}
        partner = request.env.user.partner_id
        PropertyAdminSale = request.env['property.admin.sale']
        # count for pager
        # property_sale_count = PropertyAdminSale.search_count([])
        # make pager
#         pager = portal_pager(
#             url="/my/property_sales",
#             total=property_sale_count,
#             page=page,
#             step=self._items_per_page
#         )
        # search the property sales to display, according to the pager data
#         property_sales = PropertyAdminSale.search(
#             [('partner_id', '=', partner.id)],
#             limit=self._items_per_page,
#             offset=pager['offset']
#         )
        # Filter based on stage
        if stage_id:
            property_sales = PropertyAdminSale.sudo().search([
                                        ('stage_id', '=', stage_id),
                                        ('partner_id', '=', partner.id)])
        else:
            property_sales = PropertyAdminSale._get_customer_properties(partner.id)
        request.session['my_property_sales_history'] = property_sales.ids[:100]

        values.update({
            'property_sales': property_sales,
            'page_name': 'property_sale',
            # 'pager': pager,
            'default_url': '/my/property_sales',
        })
        return request.render("skit_customer_portal.portal_my_property_sale_orders",
                              values)

    @http.route(['/my/property_sale/<int:property_sale_id>'],
                type='http',
                auth="public",
                website=True)
    def portal_my_property_sale_order(self,
                                      property_sale_id=None,
                                      access_token=None,
                                      page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content',
                                      **kw):
        try:
            property_sale_sudo = self._document_check_access('property.admin.sale',
                                                             property_sale_id,
                                                             access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._property_sale_get_page_view_values(property_sale_sudo,
                                                          access_token,
                                                          **kw)
        request.session['selected_property_so_number'] = property_sale_sudo.so_number
        request.session['selected_property_so_id'] = property_sale_sudo.id
        
        response = self.my_helpdesk_tickets(page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content',**kw)
        so_number = request.session.get('selected_property_so_number')
        tickets = response.qcontext['tickets']
        domain = [('id', 'in', tickets.ids)]
        if (so_number):
            domain += [('so_number', '=', so_number)]
        # domain = [('so_number', '=', so_number), ('id', 'in', tickets.ids)]
        tickets = request.env['helpdesk.ticket'].search(domain)
        tickets_count = request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )
        request.session['my_tickets_history'] = tickets.ids[:100]
#         response.qcontext.update({
#            'tickets': tickets,
#            'pager': pager,
#            'show_border_top': True
#         })
        values.update(response.qcontext)
        values.update({
           'tickets': tickets,
           'pager': pager,
           'show_border_top': True
        })
        
        return request.render("skit_customer_portal.portal_my_property_sale_order",
                              values)

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        """ Inherited to save the User Profile Avatar """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })
        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(['country_id',
                                  'state_id',
                                  'title',
                                  'nationality_country_id',
                                  'religion_id',
                                  'employment_status_id',
                                  'employment_country_id',
                                  'profession_id',
                                  'city_id',
                                  'barangay_id',
                                  'province_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                # saves profile avatar
                if post.get('image_1920'):
                    profile_image = post.get('image_1920').read()
                    values['image_1920'] = base64.b64encode(profile_image)
                else:
                    values.pop('image_1920')
                if 'clear_image' in post:
                    values['image_1920'] = False
                    values.pop('clear_image')
                if post.get('website_link'):
                    values['website'] = post.get('website_link')
                    values.pop('website_link')
                else:
                    values.pop('website_link')
                values.update({'zip': values.pop('zipcode', '')})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        titles = request.env['res.partner.title'].sudo().search([])
        religions = request.env['res.partner.religion'].sudo().search([])
        employment_status = request.env['res.partner.employment.status'].sudo().search([])
        professions = request.env['res.partner.profession'].sudo().search([])
        province_ids = request.env['res.country.province'].sudo().search([])
        cities = request.env['res.country.city'].sudo().search([])
        barangay_ids = request.env['res.barangay'].sudo().search([])
        values.update({
            'user': request.env.user,
            'is_public_user': request.website.is_public_user(),
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
            'website_link': partner.website,
            'titles': titles,
            'religions': religions,
            'nationalities': countries,
            'employment_status': employment_status,
            'employment_countries': countries,
            'professions': professions,
            'barangay_ids': barangay_ids,
            'province_ids': province_ids,
            'cities': cities
        })
        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/download/billing_statement/<int:property_sale_id>'],
                type='http',
                auth="public",
                website=True)
    def download_billing_stmt(self,
                              property_sale_id=None,
                              access_token=None,
                              **kw):
        """ Print Billing Statement report """
        property_sale_id = int(property_sale_id)
        soa = request.env['property.sale.statement.of.account']
        property_sale = soa.sudo().search([('id', '=', property_sale_id)])
        report = request.env.ref('skit_customer_portal.action_report_billing_statement')
        pdf, _ = report.sudo().render_qweb_pdf([property_sale.id])
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', u'%s' % len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/web/binary/download_document', type='http', auth="public")
    def download_document(self, model, field, id, filename=None, **kw):
        """ Download link for files stored as binary fields.
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str id: id of the record from which to fetch the binary
        :param str filename: field holding the file's name, if any
            :returns: :class:`werkzeug.wrappers.Response`
        """
        Model = request.env[model]
        attachment = Model.sudo().search([('id', '=', id)])
        filecontent = base64.b64decode(attachment.attachment_file)
        # filename = attachment.attachment_file_name
        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = '%s_%s' % (model.replace('.', '_'), id)
            return request.make_response(filecontent, headers=[
                ('Content-Disposition', content_disposition(filename)),
                ('Content-Type', 'application/octet-stream'),
                ('Content-Length', len(filecontent)),
            ], )

    @http.route('/web/binary/preview_document', type='http', auth="public")
    def preview_document(self, model, field, id, filename=None, **kw):
        """ Get file content stored as binary fields.
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str id: id of the record from which to fetch the binary
        :param str filename: field holding the file's name, if any
            :returns: :class:`werkzeug.wrappers.Response`
        """
        Model = request.env[model]
        attachment = Model.sudo().search([('id', '=', int(id))])
        filecontent = base64.b64decode(attachment.preview_file)
        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = '%s_%s' % (model.replace('.', '_'), id)
            return request.make_response(filecontent, headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(filecontent)),
            ], )

#     @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
#     def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', **kw):
#         response = super(CustomerPortal, self).my_helpdesk_tickets(page, date_begin, date_end, sortby, search, search_in, **kw)
# 
#         so_number = request.session.get('selected_property_so_number')
#         tickets = response.qcontext['tickets']
#         domain = [('id', 'in', tickets.ids)]
#         if (so_number):
#             domain += [('so_number', '=', so_number)]
#         # domain = [('so_number', '=', so_number), ('id', 'in', tickets.ids)]
#         tickets = request.env['helpdesk.ticket'].search(domain)
#         tickets_count = request.env['helpdesk.ticket'].search_count(domain)
#         pager = portal_pager(
#             url="/my/tickets",
#             url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
#             total=tickets_count,
#             page=page,
#             step=self._items_per_page
#         )
#         request.session['my_tickets_history'] = tickets.ids[:100]
#         response.qcontext.update({
#            'tickets': tickets,
#            'pager': pager,
#         })
#         return response
