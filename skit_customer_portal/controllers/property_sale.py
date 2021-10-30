# -*- coding: utf-8 -*-

# from odoo import http
# from odoo.http import request
# import json
# from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
# from odoo.exceptions import AccessError, MissingError
# 
# 
# class WebsitePropertySale(http.Controller):

#     def __init__(self):
#         pass

#     @http.route('/property_sale/list', type='http', website=True,
#                 sitemap=False)
#     def list_property_sale(self, **kw):
#         property_sale = request.env['property.admin.sale']
#         partner = request.env.user.partner_id
#         domain = [
#             ('partner_id', '=', partner.id)
#         ]
#         property_sale_id = property_sale.sudo().search(domain)
#         value = list()
#         for i in property_sale_id:
#             value.append(i.so_number)
#         values = dict()
#         values['value'] = value
#         return request.render('skit_customer_portal.property_sale_list_view',values)

#     @http.route('/PropertySaleDetail/<string:so_number>', type='http', website=True,
#                 sitemap=False)
#     def PropertySaleDetail(self, **kw):
#         property_sale = request.env['property.admin.sale']
#         partner = request.env.user.partner_id
#         domain = [
#             ('partner_id', '=', partner.id), ('so_number', '=', kw.get('so_number'))
#         ]
#         property_sale_id = property_sale.sudo().search(domain)
#         values = {
#                 'property_sale_id': property_sale_id,
#                 'is_show': True,
#                 'so_number': property_sale_id.so_number,
#                 'soa_ids': property_sale_id.soa_history_ids,
#                   }
#         return request.render('skit_customer_portal.property_sale_detail_view', values)

#     @http.route('/view_history/popup', type='json',
#                 methods=['POST'], website=True)
#     def show_view_history_popup(self, **kw):
#         soa_list = request.env['property.sale.statement.of.account'].sudo().search([
#             ('so_number', '=', kw.get('so_number'))
#         ])
#         values = {'soa_list': soa_list}
#         return request.env['ir.ui.view'].render_template(
#             'skit_customer_portal.view_history_popup', values)

#     @http.route('/view_preview/popup', type='json',
#                 methods=['POST'], website=True)
#     def view_preview_popup(self, **kw):
#         soa = request.env['property.sale.statement.of.account'].sudo().search([
#             ('id', '=', kw.get('soa_id'))
#         ])
#         values = {'soa_id': soa, 'is_show': False}
#         return request.env['ir.ui.view'].render_template(
#             'skit_customer_portal.view_preview_popup', values)

#     @http.route('/ViewHistory/<string:so_number>', type='http', website=True,
#                 sitemap=False)
#     def ViewHistory(self, **kw):
#         property_sale = request.env['property.admin.sale'].sudo().search([
#             ('so_number', '=', kw.get('so_number'))
#         ])
#         soa_list = request.env['property.sale.statement.of.account'].sudo().search([
#             ('so_number', '=', kw.get('so_number')), ('id', '!=', property_sale.soa_id.id)])
# 
# #         soa_list = request.env['property.sale.statement.of.account'].sudo().search([
# #             ('so_number', '=', kw.get('so_number'))
# #         ])
#         values = {'soa_list': soa_list}
#         return request.render('skit_customer_portal.property_sale_history_view', values)

#     @http.route(['/download/billing_statement/<int:property_sale_id>'], type='http', auth="public", website=True)
#     def download_billing_stmt(self, property_sale_id=None, access_token=None, **kw):
#         """ Print Billing Statement report """
#         property_sale_id = int(property_sale_id)
#         property_sales = request.env['property.sale.statement.of.account'].sudo().search([('id', '=', property_sale_id)])
#         pdf, _ = request.env.ref('skit_customer_portal.action_print_report').sudo().render_qweb_pdf([property_sales.id])
#         pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
#         return request.make_response(pdf, headers=pdfhttpheaders)

#     @http.route(['/print/billing_statement'], type='http', auth="public", website=True)
#     def get_reports(self, **post):
#         property_sale_id = post.get('property_sale_id')
#         url = "/report/billing_statement/?property_sale_id="+property_sale_id
#         return (json.dumps({'url': url}))
# 
#     @http.route(['/report/billing_statement'], type='http', auth="public", website=True)
#     def print_billing_statement(self, **kw):
#         property_sale_id = int(kw.get('property_sale_id'))
#         property_sales = request.env['property.admin.sale'].sudo().search([('id', '=', property_sale_id)])
#         value = []
#         for property_sale in property_sales:
#             value.append(property_sale.id)
#         pdf, _ = request.env.ref('skit_customer_portal.action_print_report').sudo().render_qweb_pdf(value)
#         pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
#         return request.make_response(pdf, headers=pdfhttpheaders)
