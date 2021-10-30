# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.tools import image_process
import base64
from odoo.addons.web.controllers.main import Binary
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.website.controllers.main import Website
from datetime import date, datetime
import json
from odoo.osv.expression import OR
import re
import logging
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):

    @http.route(['/my/dashboard'], type='http', auth="user", website=True)
    def dashboard(self, **kw):
        " Get State count"
        values = self._prepare_dashboard_portal_values()
        values['no_breadcrumbs'] = True
        values['rfq'] = True
        values['ps_state_wise'] = self._prepare_ps_state_wise_count()
        values['rfq_state_wise'] = self._prepare_rfq_state_wise_count()
        values['rfp_state_wise'] = self._prepare_rfp_state_wise_count()
        values['rfi_state_wise'] = self._prepare_rfi_state_wise_count()
        values['bid_state_wise'] = self._prepare_bid_state_wise_count()
        values['po_state_wise'] = self._prepare_po_state_wise_count()
        values['payment_state_wise'] = self._prepare_payment_state_wise_count()
        values['si_state_wise'] = self._prepare_si_state_wise_count()
        partner_evaluation_obj = request.env['partner.evaluation']
        partner = request.env.user.partner_id
        partner_evaluation = partner_evaluation_obj.sudo().search([
            ('partner_id', '=', partner.id)
        ], order='id desc', limit=1)
        is_customer_vendor = False
        if partner.is_vportal_vendor() and partner.is_vportal_customer():
            is_customer_vendor = True
        values['is_customer_vendor'] = is_customer_vendor
        if(partner_evaluation.state in ('draft', 'submitted', 'confirmed', 'verified')):
            vendor_status = 'Processing'
        elif(partner_evaluation.state == 'approved'):
            vendor_status = 'Accredited'
        elif(partner_evaluation.state == 'cancelled'):
            vendor_status = 'Cancelled'
        else:
            vendor_status = 'Expired'
        values['vendor_status'] = vendor_status

        return request.render("skit_vendor_portal.portal_my_dashboard", values)

    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(SUPERUSER_ID).exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))

        return document_sudo

    # Property Sales States
    def _prepare_ps_state_wise_count(self):
        """ Get PS count state wise """
        values = {}
        pro_sale_status = request.env['property.sale.status'].sudo().search([])
        property_sales = request.env['property.admin.sale']

        partner = request.env.user.partner_id

        for sale_status in pro_sale_status:
            ps_count = property_sales.sudo().search_count([
                                            ('stage_id', '=', sale_status.id),
                                            ('partner_id', '=', partner.id)
                                            ])
            values[sale_status.name] = {'stage_id': sale_status.id,
                                        'ps_count': ps_count,
                                        'state': sale_status.name
                                        }
        return values

    def _prepare_rfq_state_wise_count(self):
        """ Get RFQ count state wise """
        values = {}
        admin_vendor_rfq = request.env['admin.vendor.rfq']
        partner = request.env.user.partner_id
        rfq_datas = request.env['admin.request.for.quotation'].sudo().search([
                            ('vendor_ids', 'in', partner.ids),
                            '|', ('close_date', '>=', date.today()),
                            ('close_date', '=', False),
                            ])
        values['Waiting for Acceptance'] = admin_vendor_rfq.sudo().search_count([
            ('state', '=', 'waiting_for_acceptance'),
            ('partner_id', '=', partner.id),
            ('rfq_id', 'in', rfq_datas.ids)
        ])
        values['Submitted'] = admin_vendor_rfq.sudo().search_count([
            ('state', '=', 'submitted'), ('partner_id', '=', partner.id)
        ])
        values['Accepted'] = admin_vendor_rfq.sudo().search_count([
            ('state', '=', 'accepted'), ('partner_id', '=', partner.id)
        ])
        values['Cancelled'] = admin_vendor_rfq.sudo().search_count([
            ('state', '=', 'canceled'), ('partner_id', '=', partner.id)
        ])
        values['Done'] = admin_vendor_rfq.sudo().search_count([
            ('state', '=', 'done'), ('partner_id', '=', partner.id)
        ])
        return values

    def _prepare_rfp_state_wise_count(self):
        """ Get RFP count state wise """
        values = {}
        partner = request.env.user.partner_id
        rfp_datas = request.env['admin.request.for.proposals'].sudo().search([
                            ('vendor_ids', 'in', partner.ids),
                            '|', ('close_date', '>=', date.today()),
                            ('close_date', '=', False),
                            ])
        admin_request_for_proposal_line = request.env['admin.request.for.proposal.line'].sudo()
        values['Waiting for Acceptance'] = admin_request_for_proposal_line.search_count([
            ('state', '=', 'waiting_for_acceptance'),
            ('partner_id', '=', partner.id),
            ('rfp_id', 'in', rfp_datas.ids)
        ])
        values['Submitted'] = admin_request_for_proposal_line.search_count([
            ('state', '=', 'submitted'), ('partner_id', '=', partner.id)
        ])
        values['Accepted'] = admin_request_for_proposal_line.search_count([
            ('state', '=', 'accepted'), ('partner_id', '=', partner.id)
        ])
        values['Selected as Vendor'] = admin_request_for_proposal_line.search_count([
            ('state', '=', 'selected_as_vendor'),
            ('partner_id', '=', partner.id)
        ])
        values['Done'] = admin_request_for_proposal_line.search_count([
            ('state', '=', ['done']), ('partner_id', '=', partner.id)
        ])
        values['Declined'] = admin_request_for_proposal_line.search_count([
            ('state', '=', 'declined'), ('partner_id', '=', partner.id)
        ])
        return values

    def _prepare_rfi_state_wise_count(self):
        """ Get RFI count state wise """
        values = {}
        partner = request.env.user.partner_id
        rfi_datas = request.env['admin.request.for.information'].sudo().search([
                            ('vendor_ids', 'in', partner.ids),
                            '|', ('close_date', '>=', date.today()),
                            ('close_date', '=', False),
                            ])
        admin_request_for_information_line = request.env['admin.request.for.information.line'].sudo()
        values['Waiting for Acceptance'] = admin_request_for_information_line.search_count([
            ('state', '=', 'waiting_for_acceptance'),
            ('partner_id', '=', partner.id),
            ('rfi_id', 'in', rfi_datas.ids)
        ])
        values['Submitted'] = admin_request_for_information_line.search_count([
            ('state', '=', 'submitted'), ('partner_id', '=', partner.id)
        ])
        values['Accepted'] = admin_request_for_information_line.search_count([
            ('state', '=', 'accepted'), ('partner_id', '=', partner.id)
        ])
        values['Selected as Vendor'] = admin_request_for_information_line.search_count([
            ('state', '=', 'selected_as_vendor'),
            ('partner_id', '=', partner.id)
        ])
        values['Approved'] = admin_request_for_information_line.search_count([
            ('state', '=', ['approved']), ('partner_id', '=', partner.id)
        ])

        values['Done'] = admin_request_for_information_line.search_count([
            ('state', '=', 'done'), ('partner_id', '=', partner.id)
        ])
        return values

    def _prepare_bid_state_wise_count(self):
        """ Get BID count state wise """
        values = {}
        partner = request.env.user.partner_id
        bid_datas = request.env['purchase.bid'].sudo().search([
                            '|', ('bid_closing_date', '>=', datetime.today()),
                            ('bid_closing_date', '=', False),
                            ])
        purchase_bid_vendor = request.env['purchase.bid.vendor'].sudo()
        values['Waiting for Acceptance'] = purchase_bid_vendor.search_count([
            ('state', '=', 'waiting_for_acceptance'),
            ('partner_id', '=', partner.id),
            ('bid_id', 'in', bid_datas.ids)
        ])
        values['Bidding In-Progress'] = purchase_bid_vendor.search_count([
            ('state', '=', 'bidding_in_progress'),
            ('partner_id', '=', partner.id)
        ])
        values['Bidding Halted'] = purchase_bid_vendor.search_count([
            ('state', '=', ['bidding_halt']),
            ('partner_id', '=', partner.id)
        ])
        values['Bidding Cancelled'] = purchase_bid_vendor.search_count([
            ('state', '=', 'bidding_cancel'),
            ('partner_id', '=', partner.id)
        ])
        values['Done'] = purchase_bid_vendor.search_count([
            ('state', '=', 'done'), ('partner_id', '=', partner.id)
        ])
        values['Cancelled'] = purchase_bid_vendor.search_count([
            ('state', '=', 'cancel'), ('partner_id', '=', partner.id)
        ])
        return values

    def _prepare_po_state_wise_count(self):
        """ Get PO count state wise """
        values = {}
        partner = request.env.user.partner_id
        purchase_order = request.env['purchase.order'].sudo()
        values['Undelivered'] = purchase_order.search_count([
            ('sap_delivery_status', '=', 'undelivered'),
            ('partner_id', '=', partner.id),
            ('state', 'in', ['purchase', 'done'])
        ])
        values['Partially Delivered'] = purchase_order.search_count([
            ('sap_delivery_status', '=', 'partially_delivered'),
            ('partner_id', '=', partner.id),
            ('state', 'in', ['purchase', 'done'])
        ])
        values['Fully Delivered'] = purchase_order.search_count([
            ('sap_delivery_status', '=', ['fully_delivered']),
            ('partner_id', '=', partner.id),
            ('state', 'in', ['purchase', 'done'])
        ])
        return values

    def _prepare_payment_state_wise_count(self):
        """ Get Payment count state wise """
        values = {}
        partner = request.env.user.partner_id
        payment = request.env['admin.invoice.payment'].sudo()
        values['Awaiting Original'] = payment.search_count([
            ('original_or_received', '=', False),
            ('vendor_partner_id', '=', partner.id)
        ])
        values['Received'] = payment.search_count([
            ('original_or_received', '=', True),
            ('vendor_partner_id', '=', partner.id)
        ])
        return values

    def _prepare_si_state_wise_count(self):
        """ Get SI count state wise """
        values = {}
        partner = request.env.user.partner_id
        si_order = request.env['admin.sales.invoice'].sudo()
        values['Original Documents Received'] = si_order.search_count([
            ('document_status', '=', 'Original Documents Received'),
            ('vendor_partner_id', '=', partner.id)
        ])
        values['Original Documents Review'] = si_order.search_count([
            ('document_status', '=', 'Original Documents Review'),
            ('vendor_partner_id', '=', partner.id)
        ])
        values['Awaiting Original Documents'] = si_order.search_count([
            ('document_status', '=', ['Awaiting Original Documents']),
            ('vendor_partner_id', '=', partner.id)
        ])
        values['Returned to Vendor'] = si_order.search_count([
            ('document_status', '=', 'Returned to Vendor'),
            ('vendor_partner_id', '=', partner.id)
        ])
        return values

    def _prepare_dashboard_portal_values(self):
        """ Add Property Sale, RFQ, RFP, RFI, etc details to Dash board page """
        values = {}
        partner = request.env.user.partner_id

        rfi_datas = request.env['admin.request.for.information'].sudo().search([
                            ('vendor_ids', 'in', partner.ids),
                            '|', ('close_date', '>=', date.today()),
                            ('close_date', '=', False),
                            ])
        rfp_datas = request.env['admin.request.for.proposals'].sudo().search([
                            ('vendor_ids', 'in', partner.ids),
                            '|', ('close_date', '>=', date.today()),
                            ('close_date', '=', False),
                            ])
        rfq_datas = request.env['admin.request.for.quotation'].sudo().search([
                            ('vendor_ids', 'in', partner.ids),
                            '|', ('close_date', '>=', date.today()),
                            ('close_date', '=', False),
                            ])
        rfi_count = 0
        rfq_count = 0
        rfp_count = 0
        values['pro_sale_count'] = request.env['property.admin.sale'].sudo().search_count([('partner_id', '=', partner.id)
        ]) if request.env['property.admin.sale'].check_access_rights('read', raise_exception=False) else 0

        rfq_count = rfq_count + request.env['admin.vendor.rfq'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'waiting_for_acceptance'), ('state', 'not in', ('canceled', 'declined', 'no_response')), ('rfq_id', 'in', rfq_datas.ids)
        ]) if request.env['admin.vendor.rfq'].check_access_rights('read', raise_exception=False) else 0

        rfq_count = rfq_count + request.env['admin.vendor.rfq'].sudo().search_count([('partner_id', '=', partner.id), ('state', 'not in', ('canceled', 'declined', 'waiting_for_acceptance', 'no_response'))
        ]) if request.env['admin.vendor.rfq'].check_access_rights('read', raise_exception=False) else 0

        values['rfq_count'] = rfq_count

        rfi_count = rfi_count + request.env['admin.request.for.information.line'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'waiting_for_acceptance'), ('state', 'not in', ('canceled', 'declined', 'no_response')), ('rfi_id', 'in', rfi_datas.ids)
        ]) if request.env['admin.request.for.information'].check_access_rights('read', raise_exception=False) else 0

        rfi_count = rfi_count + request.env['admin.request.for.information.line'].sudo().search_count([('partner_id', '=', partner.id), ('state', 'not in', ('canceled', 'declined', 'waiting_for_acceptance', 'no_response'))
        ])

        values['rfi_count'] = rfi_count

        rfp_count = rfp_count + request.env['admin.request.for.proposal.line'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'waiting_for_acceptance'), ('state', 'not in', ('canceled', 'declined', 'no_response')), ('rfp_id', 'in', rfp_datas.ids)
        ]) if request.env['admin.request.for.proposals'].check_access_rights('read', raise_exception=False) else 0

        rfp_count = rfp_count + request.env['admin.request.for.proposal.line'].sudo().search_count([('partner_id', '=', partner.id), ('state', 'not in', ('canceled', 'declined', 'waiting_for_acceptance', 'no_response'))
        ]) if request.env['admin.request.for.proposals'].check_access_rights('read', raise_exception=False) else 0

        values['rfp_count'] = rfp_count

        bid_count = 0
        if request.env.user.has_group('base.group_portal'):
            bidder = request.env['purchase.bid.vendor'].search([('partner_id', '=', partner.id),
                                                                ('state', 'not in', ['draft', 'decline'])])
            waiting_bidder = request.env['purchase.bid.vendor'].search([('id', 'in', bidder.ids), ('state', '=', 'waiting_for_acceptance')])
            other_bidder = request.env['purchase.bid.vendor'].search([('id', 'in', bidder.ids), ('state', 'not in', ('waiting_for_acceptance', 'no_response'))])
            bid_count = bid_count + request.env['purchase.bid'].sudo().search_count([('vendor_line','in', waiting_bidder.ids), '|', ('bid_closing_date', '>=', datetime.today()),
                            ('bid_closing_date', '=', False)
            ]) if request.env['purchase.bid'].check_access_rights('read', raise_exception=False) else 0
            bid_count = bid_count + request.env['purchase.bid'].sudo().search_count([('vendor_line','in', other_bidder.ids)
            ]) if request.env['purchase.bid'].check_access_rights('read', raise_exception=False) else 0
        else:
            bid_count = bid_count + request.env['purchase.bid'].sudo().search_count([
            ]) if request.env['purchase.bid'].check_access_rights('read', raise_exception=False) else 0
        values['bid_count'] = bid_count
        # PO count - based on state (purchase and done)
        values['purchase_count'] = request.env['purchase.order'].sudo().search_count([
                                    ('partner_id', '=', partner.id),
                                    ('state', 'in', ['purchase', 'done'])
        ]) if request.env['purchase.order'].check_access_rights('read', raise_exception=False) else 0

        values['payment_count'] = request.env['admin.invoice.payment'].sudo().search_count([('vendor_partner_id', '=', partner.id)
        ]) if request.env['admin.invoice.payment'].check_access_rights('read', raise_exception=False) else 0

        values['si_count'] = request.env['admin.sales.invoice'].sudo().search_count([('vendor_partner_id', '=', partner.id)
        ]) if request.env['admin.sales.invoice'].check_access_rights('read', raise_exception=False) else 0
        return values

    def _rfq_order_get_page_view_values(self, order, access_token, **kwargs):
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_rfq_history', True, **kwargs)

    @http.route(['/my/rfq/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_rfq_order(self, order_id=None, access_token=None, **kw):
        " Display RFQ Details"
        try:
            order_sudo = self._document_check_access('admin.vendor.rfq', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._rfq_order_get_page_view_values(order_sudo, access_token, **kw)
        values['page_name'] = 'rfq'
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', order_sudo.id),
                            ('res_model', '=', 'admin.vendor.rfq')])
        values['attachments'] = attachments
        return request.render("skit_vendor_portal.portal_my_rfq_order", values)

    @http.route(['/my/rfq', '/my/rfq/page/<int:page>', '/my/rfq/<string:state>'], type='http', auth="user", website=True)
    def portal_my_rfq_orders(self, page=1, state=None, date_begin=None, date_end=None, sortby=None, filterby=None,search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        rfq_mail = request.env['admin.vendor.rfq'].sudo()
        domain = []
        domain += [('partner_id', '=', partner.id)]
        domain += [('state', '!=', 'declined')]
        domain += [('state', '!=', 'canceled')]
        domain += [('state', '!=', 'no_response')]
        if(state):
            if(state == 'Waiting for Acceptance'):
                state = 'waiting_for_acceptance'
            domain += [('state', '=', state.lower())]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'id': {'label': _('RFQ Ref No.'), 'order': 'id desc'},
            'create_date': {'label': _('Date of Request'), 'order': 'create_date desc'},
            'state': {'label': _('Status'), 'order': 'state asc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'create_date'
        order = searchbar_sortings[sortby]['order']
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }
        # search
        if search and search_in:
            search_domain = []
            rfqsearch_domain = []
            search_state = search
            if search_in in ('content', 'all'):
                if (search == 'Waiting for Acceptance'):
                    search_state = 'waiting_for_acceptance'
                if (search == 'Accepted'):
                    search_state = 'accepted'
                if (search == 'Submitted'):
                    search_state = 'submitted'
                if (search == 'Saved as Draft'):
                    search_state = 'saved_as_draft'
                if (search == 'Done'):
                    search_state = 'done'
                if (search == 'Declined'):
                    search_state = 'declined'
                if (search == 'Cancelled'):
                    search_state = 'canceled'
                search_from = None
                search_to = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')

                rfqsearch_domain = OR([rfqsearch_domain, ['|', '|','|',('name', 'ilike', search),
                                                   '&', ('create_date', '>=', search_from),('create_date', '<=', search_to),
                                                   '&', ('open_date', '>=', search_from),('open_date', '<=', search_to),
                                                   '&', ('close_date', '>=', search_from),('close_date', '<=', search_to)
                                                  ]])
                rfq = request.env['admin.request.for.quotation'].search(rfqsearch_domain)
                search_domain = OR([search_domain, ['|', ('rfq_id', 'in', (rfq.ids)),
                                                   ('state', 'ilike', search_state)
                                                  ]])
            domain += search_domain
        # default filter by value
        if not filterby:
            filterby = 'rfq'
        # count for pager
        rfq_count = rfq_mail.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/rfq",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=rfq_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = rfq_mail.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_rfq_history'] = orders.ids[:100]
        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'rfq',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'default_url': '/my/rfq',
            'partner_id': partner.id,
            'today_date': date.today()
        })
        return request.render("skit_vendor_portal.portal_my_rfq_orders", values)

    def _rfi_order_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_rfi_history', True, **kwargs)

    @http.route(['/my/rfi', '/my/rfi/page/<int:page>', '/my/rfi/<string:state>'], type='http', auth="user", website=True)
    def portal_my_rfi_orders(self, page=1, state=None, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        rfi_order = request.env['admin.request.for.information.line'].sudo()
        partner = request.env.user.partner_id
        domain = []
        domain += [('partner_id', '=', partner.id), ('state', 'not in', ('canceled', 'declined', 'no_response'))]
        if(state):
            if(state == 'Waiting for Acceptance'):
                state = 'waiting_for_acceptance'
            if (search == 'Accepted'):
                state = 'accepted'
            if (search == 'Declined'):
                state = 'declined'
            if (search == 'Cancelled'):
                state = 'canceled'
            domain += [('state', '=', state.lower())]
        archive_groups = self._get_archive_groups('admin.request.for.information.line', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'name': {'label': _('RFI NO.'), 'order': 'id desc'},
            'create_date': {'label': _('Date of Request'), 'order': 'create_date desc'},
            'state': {'label': _('Status'), 'order': 'state asc'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }
        # search
        if search and search_in:
            search_domain = []
            search_state = search
            if search_in in ('content', 'all'):
                if (search == 'Waiting for Acceptance' or search == 'Sent'):
                    search_state = 'waiting_for_acceptance'
                if (search == 'Accepted'):
                    search_state = 'accepted'
                if (search == 'Submitted'):
                    search_state = 'submitted'
                if (search == 'Done'):
                    search_state = 'done'
                if (search == 'Declined'):
                    search_state = 'declined'
                if (search == 'Cancelled'):
                    search_state = 'canceled'
                search_from = None
                search_to = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
                search_domain = OR([search_domain, ['|', '|','|','|',('rfi_id.name', 'ilike', search),
                                                   '&', ('create_date', '>=', search_from),('create_date', '<=', search_to),
                                                   '&', ('rfi_id.open_date', '>=', search_from),('rfi_id.open_date', '<=', search_to),
                                                   '&', ('rfi_id.close_date', '>=', search_from),('rfi_id.close_date', '<=', search_to),
                                                   ('state', 'ilike', search_state)]])
            domain += search_domain

        # default sort by value
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'rfi'

        # count for pager
        rfi_count = rfi_order.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/rfi",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=rfi_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = rfi_order.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_rfi_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'rfi',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'default_url': '/my/rfi',
            'today_date': date.today()
        })
        return request.render("skit_vendor_portal.portal_my_rfi_orders", values)

    @http.route(['/my/rfi/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_rfi_order(self, order_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('admin.request.for.information.line', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._rfi_order_get_page_view_values(order_sudo, access_token, **kw)
        partner = request.env.user.partner_id
        rfi_order_line = request.env['admin.request.for.information.line'].sudo().search([('id', '=', order_sudo.id)])
        values['page_name'] = 'rfi'
        values['order_line'] = rfi_order_line
        return request.render("skit_vendor_portal.portal_my_rfi_order", values)

    @http.route(['/rfi/decline_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def rfi_decline_popup(self, **kw):
        """ Display PO Decline form.
            @return popup.
        """
        decline_reason = request.env['admin.declined.reason'].sudo().search([])
        values = ({
                    'decline_reason': decline_reason,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.rfi_decline_popup",
                                                         values)

    @http.route(['/update/rfi/declined_status'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_rfi_declined_status(self, **kw):
        """ Update RFI Declined status.
            @return popup.
        """
        rfi_order_line = request.env['admin.request.for.information.line'].sudo().search([
                                        ('rfi_id', '=', int(kw.get('rfi_id')))])
        if rfi_order_line:
            rfi_order_line.update({'state': 'declined',
                                   'declined_note': kw.get('declined_note'),
                                   'declined_reason_id': int(kw.get('reason_id'))
                                   })

    @http.route(['/update/rfi/accept_status'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_rfi_accepted_status(self, **kw):
        """ Update RFI Accepted status.
            @return popup.
        """
        rfi_order_line = request.env['admin.request.for.information.line'].sudo().search([
                                        ('rfi_id', '=', int(kw.get('rfi_id')))])
        if rfi_order_line:
            rfi_order_line.update({'state': 'accepted',
                                   })

    def _prepare_home_portal_values(self):
        values = super(CustomerPortal, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id
        PurchaseRfp = request.env['admin.request.for.proposal.line']
        rfp_domain = [('partner_id', '=', partner.id)]
        rfp_count = PurchaseRfp.search_count(rfp_domain) if PurchaseRfp.check_access_rights('read', raise_exception=False) else 0
        values['rfp_count'] = rfp_count
        RFIOrder = request.env['admin.request.for.information.line']
        rfi_domain = [('partner_id', '=', partner.id)]
        rfi_count = RFIOrder.search_count(rfi_domain) if RFIOrder.check_access_rights('read', raise_exception=False) else 0
        values['rfi_count'] = rfi_count
        return values

    def _rfp_order_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))
        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_rfp_history', True, **kwargs)

    @http.route(['/my/rfp', '/my/rfp/page/<int:page>', '/my/rfp/<string:state>'], type='http', auth="user", website=True)
    def portal_my_rfp_orders(self, page=1, state=None, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        rfp_order = request.env['admin.request.for.proposal.line'].sudo()
        partner = request.env.user.partner_id

        domain = []
        domain += [('partner_id', '=', partner.id), ('state', 'not in', ('canceled', 'declined', 'no_response'))]
        if(state):
            if(state == 'Waiting for Acceptance'):
                state = 'waiting_for_acceptance'
            if(state == 'Submitted'):
                state = 'submitted'
            if(state == 'Accepted'):
                state = 'accepted'
            if(state == 'Selected as Vendor'):
                state = 'selected_as_vendor'
            if(state == 'Done'):
                state = 'done'
            if(state == 'Declined'):
                state = 'declined'
            if (search == 'Cancelled'):
                state = 'canceled'
            domain += [('state', '=', state.lower())]

        archive_groups = self._get_archive_groups('admin.request.for.proposal.line', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'name': {'label': _('RFP NO.'), 'order': 'id desc'},
            'create_date': {'label': _('Date of Request'), 'order': 'create_date desc'},
            'state': {'label': _('Status'), 'order': 'state asc'},
        }

        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},

        }
        # search
        if search and search_in:
            search_domain = []
            search_state = search
            if search_in in ('content', 'all'):
                if(search == 'Waiting for Acceptance'):
                    search_state = ' waiting_for_acceptance'
                if(search == 'Submitted'):
                    search_state = 'submitted'
                if(search == 'Accepted'):
                    search_state = 'accepted'
                if(search == 'Selected as Vendor'):
                    search_state = 'selected_as_vendor'
                if(search == 'Done'):
                    search_state = 'done'
                if(search == 'Declined'):
                    search_state = 'declined'
                if (search == 'Cancelled'):
                    search_state = 'canceled'
                search_from = None
                search_to = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
                search_domain = OR([search_domain, ['|', '|', '|', '|', ('rfp_id.name', 'ilike', search),
                                                    '&', ('create_date', '>=', search_from), ('create_date', '<=', search_to),
                                                    '&', ('rfp_id.open_date', '>=', search_from), ('rfp_id.open_date', '<=', search_to),
                                                    '&', ('rfp_id.close_date', '>=', search_from), ('rfp_id.close_date', '<=', search_to),
                                                    ('state', 'ilike', search_state)]])
            domain += search_domain

        # default sort by value
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # count for pager
        rfp_count = rfp_order.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/rfp",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=rfp_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = rfp_order.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_rfp_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'rfp',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'default_url': '/my/rfp',
            'partner_id': partner.id,
            'today_date': date.today()
        })
        return request.render("skit_vendor_portal.portal_my_rfp_orders", values)

    @http.route(['/my/rfp/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_rfp_order(self, order_id=None, access_token=None, **kw):
        partner = request.env.user.partner_id
        try:
            order_sudo = self._document_check_access('admin.request.for.proposal.line', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._rfp_order_get_page_view_values(order_sudo, access_token, **kw)
        rfp_mail = request.env['admin.request.for.proposal.line'].sudo().search([
                                ('id', '=', order_sudo.id)], limit=1)
        values.update({
            'rfp_mail': rfp_mail
        })
        values['page_name'] = 'rfp'

        return request.render("skit_vendor_portal.portal_my_rfp_order", values)

    def _payment_order_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_payment_history', True, **kwargs)

    @http.route(['/my/payment', '/my/payment/page/<int:page>', '/my/payment/<string:state>'], type='http', auth="user", website=True)
    def portal_my_payment_orders(self, page=1, state=None, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        payment_release = request.env['admin.invoice.payment'].sudo()
        partner = request.env.user.partner_id
        domain = []
        domain += [('vendor_partner_id', '=', partner.id)]
        if(state == 'Awaiting Original'):
            domain += [('original_or_received', '=', False)]
        if(state == 'Received'):
            domain += [('original_or_received', '=', True)]
        archive_groups = self._get_archive_groups('admin.invoice.payment', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'admin_si_number': {'label': _('SI Number'), 'order': 'admin_si_number desc'},
            'name': {'label': _('Payment Transaction No.'), 'order': 'id desc'},
            'payment_release_date': {'label': _('Released Date'), 'order': 'payment_release_date desc'},
            'amount': {'label': _('Released Amount'), 'order': 'amount desc'},
            'or_number': {'label': _('OR No'), 'order': 'or_number desc'},
            'or_date': {'label': _('OR Date'), 'order': 'or_date desc'},
            'amount': {'label': _('OR Amount'), 'order': 'amount desc'},
            'state': {'label': _('OR Copy Status'), 'order': 'original_or_received asc'},
        }

        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},

        }

        if search and search_in:
            search_domain = []
            original_or_received = None
            if search_in in ('content', 'all'):
                if (search.lower() in 'awaiting original'):
                    original_or_received = False
                if (search.lower() in 'received'):
                    original_or_received = True

                search_from = None
                search_to = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
                search_amount = None
                if(self.is_float(search)):
                    search_amount = search
                search_domain = OR([search_domain, ['|', '|','|','|','|','|',('admin_si_number', 'ilike', search),
                                                    ('or_number', 'ilike', search),
                                                    ('name', 'ilike', search),
                                                    ('original_or_received', '=', original_or_received),
                                                    ('amount', '=', search_amount),
                                                    '&', ('payment_release_date', '>=', search_from), ('payment_release_date', '<=', search_to),
                                                    '&', ('or_date', '>=', search_from),('or_date', '<=', search_to)
                                                  ]])
            domain += search_domain

        # default sort by value
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # count for pager
        payment_count = payment_release.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/payment",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=payment_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = payment_release.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_payment_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'pr',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'default_url': '/my/payment',
        })
        return request.render("skit_vendor_portal.portal_my_payments", values)

    @http.route(['/my/payment/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_payment_order(self, order_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('admin.invoice.payment', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._payment_order_get_page_view_values(order_sudo, access_token, **kw)
        values['page_name'] = 'pr'
        # Get Payment Attachments
        payment_attachments = request.env['ir.attachment'].sudo().search(
                                    [('res_model', '=', 'admin.invoice.payment'),
                                     ('res_id', '=', order_id)])
        values['attachments'] = payment_attachments
        return request.render("skit_vendor_portal.portal_my_payment", values)

    def _bid_order_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_bid_history', True, **kwargs)

    def is_date(self, string):
        match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', string)
        return match

    def is_float(self, float):
        match = re.search('^[1-9]\d*(\.\d+)?$', float)
        return match

    @http.route(['/my/bid', '/my/bid/page/<int:page>', '/my/bid/<string:state>'], type='http', auth="user", website=True)
    def portal_my_bid_orders(self, page=1, state=None, date_begin=None, date_end=None, sortby=None, filterby=None,search=None, search_in='content', **kw):
        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        bid_order = request.env['purchase.bid.vendor'].sudo()
        domain = []

        domain += [('partner_id', '=', partner.id)]
        domain += [('state', '!=', 'decline')]
        domain += [('state', '!=', 'cancel')]
        domain += [('state', '!=', 'no_response')]
        if(state):
            if(state == 'Waiting for Acceptance'):
                state = 'waiting_for_acceptance'
            if(state == 'Bidding In-Progress'):
                state = 'bidding_in_progress'
            if(state == 'Bidding Halted'):
                state = 'bidding_halt'
            if(state == 'Bidding Cancelled'):
                state = 'bidding_cancel'
            if(state == 'Declined'):
                state = 'decline'
            if(state == 'Cancelled'):
                state = 'cancel'
            domain += [('state', '=', state.lower())]
        else:
            domain += [('state', '!=', 'draft')]
        archive_groups = self._get_archive_groups('purchase.bid.vendor', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        searchbar_sortings = {
            'bid_id': {'label': _('Bid Ref No.'), 'order': 'id desc'},
            'scope_of_work': {'label': _('Scope of Work'), 'order': 'scope_of_work desc'},
            'create_date': {'label': _('Date of Request'), 'order': 'create_date desc'},
            'bid_opening_date': {'label': _('Open Date'), 'order': 'bid_opening_date desc'},
            'bid_closing_date': {'label': _('Close Date'), 'order': 'bid_closing_date desc'},
            'state': {'label': _('Status'), 'order': 'state asc'},
        }

        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        }
        # search
        if search and search_in:
            search_domain = []
            search_state = search
            if search_in in ('content', 'all'):
                if (search == 'Waiting for Verification'):
                    search_state = 'waiting_for_verification'
                if (search == 'Waiting for Approval'):
                    search_state = 'waiting_for_approval'
                if (search == 'Sending Bid Invitation'):
                    search_state = 'send_bid_invitation'
                if (search == 'Bid Invitation Sent'):
                    search_state = 'invitation_sent'
                if (search == 'Pre-Bidding'):
                    search_state = 'pre_bidding'
                if (search == 'Halted'):
                    search_state = 'halted'
                if (search == 'Post-Bidding'):
                    search_state = 'post_bidding'
                if (search == 'Bid Selection'):
                    search_state = 'bid_selection'
                if (search == 'Waiting for Bid Selection Verification'):
                    search_state = 'waiting_bid_selection_ver'
                if (search == 'Waiting for Bid Selection Confirmation'):
                    search_state = 'waiting_bid_selection_con'
                if (search == 'Waiting for Bid Selection Approval'):
                    search_state = 'waiting_bid_selection_app'
                if (search == 'cancel'):
                    search_state = 'Cancelled'
                search_from = None
                search_to = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
                search_domain = OR([search_domain, ['|', '|','|','|','|',('bid_ref_no', 'ilike', search), ('scope_of_work', 'ilike', search),
                                                   '&', ('create_date', '>=', search_from),('create_date', '<=', search_to),
                                                   '&', ('bid_opening_date', '>=', search_from),('bid_opening_date', '<=', search_to),
                                                   '&', ('bid_closing_date', '>=', search_from),('bid_closing_date', '<=', search_to),
                                                   ('state', 'ilike', search_state)]])
            domain += search_domain

        # default sort by value
        if not sortby:
            sortby = 'bid_id'
        order = searchbar_sortings[sortby]['order']
        searchbar_filters = {
            'bid': {'label': _('BID Order'), 'domain': [('state', '=', 'draft')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'bid'

        # count for pager
        bid_count = bid_order.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/bid",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=bid_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = bid_order.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_bid_history'] = orders.ids[:100]
        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'bid',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'default_url': '/my/bid',
            'partner_id': partner.id,
            'today_date': datetime.today()
        })
        return request.render("skit_vendor_portal.portal_my_bid_orders", values)

    @http.route(['/my/bid/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_bid_order(self, order_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('purchase.bid.vendor', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._bid_order_get_page_view_values(order_sudo, access_token, **kw)
        values['page_name'] = 'bid'
        bidding = order_sudo.bid_id
        messages = request.env['mail.message'].sudo().search([('model', '=', 'purchase.bid.vendor'),
                                                              ('res_id', '=', bidding.ids),
                                                              ('partner_ids', 'in', request.env.user.partner_id.ids)], limit=1)
        bidder = request.env['purchase.bid.vendor'].sudo().search([('bid_id', '=', bidding.id),
                                                          ('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        email_message = request.env['mail.message'].sudo().search([('model', '=', 'purchase.bid.vendor'),
                                                              ('res_id', 'in', bidder.ids),
                                                              ('partner_ids', 'in', request.env.user.partner_id.ids)], limit=1)
        messages = messages + email_message
        messages = request.env['mail.message'].sudo().search([('id', 'in', messages.ids)], order='id desc')
        bid_requirements = request.env['document.requirement'].sudo().search([])
        events = request.env['event.event'].sudo().search([('bid_id', '=', bidding.id),
                                                           ('state', '!=', 'draft'),
                                                           ('is_published', '=', True)])
        show_contract = False
        if bidder.state == 'done':
            if bidder.id == bidder.bid_id.vendor_id.id:
                show_contract = True
        values['messages'] = messages
        values['bidder'] = bidder
        values['bid_requirements'] = bid_requirements
        values['events'] = events
        values['show_contract'] = show_contract
        return request.render("skit_vendor_portal.portal_my_bid_order", values)

    @http.route(['/my/bid/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
    def portal_my_bid_event_view(self, event, access_token=None, **kw):
        urls = event._get_event_resource_urls()
        bidder = request.env['purchase.bid.vendor'].sudo().search([('bid_id', '=', event.bid_id.id),
                                                          ('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        values = {
            'event': event,
            'main_object': event,
            'range': range,
            'registrable': event.sudo()._is_event_registrable(),
            'google_url': urls.get('google_url'),
            'iCal_url': urls.get('iCal_url'),
            'page_name': 'bid',
            'order': bidder,
            'is_bid_event': True
        }

        return request.render("skit_vendor_portal.portal_my_bid_event", values)

    def _si_order_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_bid_history', True, **kwargs)

    @http.route('/save/rfq_mail/', type='json', auth='user', website=True)
    def rfq_mail_save(self, **kw):
        post_all_vals = kw.get('RfqValues')
        rfq_mail_vals = post_all_vals['rfq_mail_vals']
        rfq_mail_line_vals = post_all_vals['rfq_mail_line_vals']
        other_info = rfq_mail_vals.get('other_info')
        state = rfq_mail_vals.get('state')
        kw.pop('RfqValues')
        for rfq_line_id in rfq_mail_line_vals.keys():
            rfq_line_vals = rfq_mail_line_vals.get(rfq_line_id)
            _logger.info('***RFQ LINES*** %s', rfq_line_vals)
            # <-- START Convert date widget data to database format
            if(rfq_line_vals.get('validity_from')):
                validity_from = rfq_line_vals['validity_from']
                try:
                    lang = request.env['ir.qweb.field'].user_lang()
                    dt = datetime.strptime(validity_from, lang.date_format)
                except ValueError:
                    dt = datetime.strptime(validity_from, DEFAULT_SERVER_DATE_FORMAT)
                rfq_line_vals['validity_from'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
            if(rfq_line_vals.get('validity_to')):
                validity_to = rfq_line_vals['validity_to']
                try:
                    lang = request.env['ir.qweb.field'].user_lang()
                    dt = datetime.strptime(validity_to, lang.date_format)
                except ValueError:
                    dt = datetime.strptime(validity_to, DEFAULT_SERVER_DATE_FORMAT)
                rfq_line_vals['validity_to'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
            # Convert date widget data to database format END-->
            # Convert float to int when delivery lead time is float
            if (rfq_line_vals.get('delivery_lead_time')):
                delivery_lead_time = rfq_line_vals['delivery_lead_time']
                rfq_line_vals['delivery_lead_time'] = int(float(delivery_lead_time))
            rfq_line = request.env['admin.request.for.quotation.line.vendor'].sudo().search([('id', '=', int(rfq_line_id))])
            rfq_line.sudo().write(rfq_line_vals)
            rfq_line.vendor_rfq_id.sudo().write({'state':state, 'other_information': other_info})
        return json.dumps({'id': rfq_line.id})

    @http.route('/rfq_mail/accept_state/', type='json', auth='user', website=True)
    def accepted_rfq_mail(self, **kw):
        post = kw.get('post')
        rfq_mail_id = int(post.get('rfq_mail_id'))
        rfq_mail = request.env['admin.vendor.rfq'].sudo().search([('id', '=', rfq_mail_id)])
        rfq_mail.sudo().write({'state': 'accepted'})
        return json.dumps({
            'id': rfq_mail.id
        })

    @http.route('/accreditation', type="http",
                auth="user", website=True)
    def accreditation_form(self, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        accreditation = request.env['partner.evaluation'].sudo().search([('partner_id','=',partner.id),
                                                                         ('state', 'not in', ('canceled', 'rejected'))], order="id desc",limit=1)
        accreditation_docs_ids = accreditation.document_accreditation_requirement_ids
        vendor_eval_docs = request.env['vendor.evaluation.template'].sudo().search([])
        default_eval_tmpl_ids = vendor_eval_docs.document_accreditation_requirement_ids
        file_attached = False
        file_attachments = []
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', accreditation.id),
                            ('res_model', '=', 'partner.evaluation')])
        if attachments:
            file_attached = True
            for attachment in attachments:
                file_attachments.append({'pfile_content': attachment.datas,
                                         'pfile_name': attachment.name,
                                         'type': attachment.type,
                                         'mimetype': attachment.mimetype,
                                         'id': attachment.id})
        values.update({'page_name': 'accreditation_view',
                       'vendor': partner,
                       'accreditation': accreditation,
                       'default_eval_tmpl_ids': default_eval_tmpl_ids,
                       'accreditation_docs_ids': accreditation_docs_ids,
                       'file_attached': file_attached,
                       'file_attachments': file_attachments
                       })
        return request.env['ir.ui.view'].render_template(
            "skit_vendor_portal.portal_accreditation", values)

    @http.route(['/upload/accreditation/attachment'], type='json', auth="public",
                methods=['POST'], website=True)
    def upload_accreditation_attachment(self, **kw):
        file_details = kw.get('dl_attch_file_list')
        if(file_details and file_details[0].get('file_content')):
            for file in file_details:
                Attachments = request.env['ir.attachment']
            file_content = file['file_content']

            file_content = file_content.split(',')[1]
            Attachments.sudo().create({
                'name': file['file_name'],
                'res_name': file['file_name'],
                'type': 'binary',
                'res_model': kw.get('modal_name'),
                'datas': file_content,
                'res_id': int(kw.get('id'))
            })
        return True

    @http.route(['/delete/accreditation/attachment'], type='json', auth="public",
                methods=['POST'], website=True)
    def delete_accreditation_attachment(self, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(int(kw.get('id')))
        attachment.unlink()
        return True


    @http.route('/rqmt/save', type='json', auth='user', website=True)
    def accreditation_rqmt_save(self, **kw):
        partner = request.env.user.partner_id
        accreditation = request.env['partner.evaluation'].sudo().search([('partner_id', '=', partner.id)])
        checked_req_ids = list()
        for val in kw.get('checked_rqmt_ids'):
            checked_req_ids.append(int(val))
        accreditation.write({
            'document_accreditation_requirement_ids': [(6, 0, checked_req_ids)],
            })

    @http.route('/performance', type="http",
                auth="user", website=True)
    def performance_view(self, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner_evaluation = request.env['partner.regular.evaluation'].sudo().search([('partner_id','=',partner.id)])
        values.update({'page_name': 'performance_view',
                       'partner_eval': partner_evaluation,
                       })
        return request.env['ir.ui.view'].render_template(
            "skit_vendor_portal.portal_performance", values)

    @http.route('/vendor/view_full_profile', type="http",
                auth="public", website=True)
    def vendor_registration(self, **kw):
        """ Render Vendor Registration Form """
        industry = request.env['res.partner.industry'].sudo().search([])
        country = request.env['res.country'].sudo().search([])
        barangay = request.env['res.barangay'].sudo().search([])
        province = request.env['res.country.province'].sudo().search([])
        cities = request.env['res.country.city'].sudo().search([])
        regions = request.env['res.continent.region'].sudo().search([])
        product_classifications = request.env['product.classification'].sudo().search([])
        partner = request.env.user.partner_id
        is_show_other = False
        if((partner.business_type == 'Individual') and
                (partner.is_vportal_vendor() and partner.is_vportal_customer())):
            is_show_other = True
        values = ({'countries': country,
                   'barangaies': barangay,
                   'regions': regions,
                   'province': province,
                   'cities': cities,
                   'product_classifications': product_classifications,
                   'industries': industry,
                   'partner': partner,
                   'is_show_other': is_show_other
                   })
        return request.render("skit_vendor_portal.view_full_profile_form",
                              values)

    @http.route('/site_address/update/site_address', type="http",
                auth="public", website=True)
    def update_site_address(self, **kw):
        """ Render Vendor Registration Form """
        industry = request.env['res.partner.industry'].sudo().search([])
        country = request.env['res.country'].sudo().search([])
        barangay = request.env['res.barangay'].sudo().search([])
        province = request.env['res.country.province'].sudo().search([])
        cities = request.env['res.country.city'].sudo().search([])
        regions = request.env['res.continent.region'].sudo().search([])
        product_classifications = request.env['product.classification'].sudo().search([])
        partner = request.env.user.partner_id
        values = ({'countries': country,
                   'barangaies': barangay,
                   'regions': regions,
                   'province': province,
                   'cities': cities,
                   'product_classifications': product_classifications,
                   'industries': industry,
                   'partner': partner
                   })
        return request.render("skit_vendor_portal.view_full_profile_form",
                              values)


class VendorBidEventController(WebsiteEventController):

    @http.route(['/my/bid/event/<model("event.event"):event>/registration/new'], type='json', auth="public", methods=['POST'], website=True)
    def bid_registration_new(self, event, **post):
        tickets = self._process_tickets_details(post)
        availability_check = True
        if event.seats_availability == 'limited':
            ordered_seats = 0
            for ticket in tickets:
                ordered_seats += ticket['quantity']
            if event.seats_available < ordered_seats:
                availability_check = False
        if not tickets:
            return False
        return request.env['ir.ui.view'].render_template("website_event.registration_attendee_details", {'tickets': tickets, 'event': event, 'availability_check': availability_check, 'is_bid_event': True})

    @http.route(['''/bid/event/<model("event.event", "[('website_id', 'in', (False, current_website_id))]"):event>/registration/confirm'''], type='http', auth="public", methods=['POST'], website=True)
    def bid_registration_confirm(self, event, **post):
        order = request.website.sale_get_order(force_create=1)
        attendee_ids = set()

        registrations = self._process_registration_details(post)
        for registration in registrations:
            ticket = request.env['event.event.ticket'].sudo().browse(int(registration['ticket_id']))
            cart_values = order.with_context(event_ticket_id=ticket.id, fixed_price=True)._cart_update(product_id=ticket.product_id.id, add_qty=1, registration_data=[registration])
            attendee_ids |= set(cart_values.get('attendee_ids', []))

        # free tickets -> order with amount = 0: auto-confirm, no checkout
        if not order.amount_total:
            order.action_confirm()  # tde notsure: email sending ?
            attendees = request.env['event.registration'].browse(list(attendee_ids)).sudo()
            # clean context and session, then redirect to the confirmation page
            request.website.sale_reset()
            urls = event._get_event_resource_urls()
            bidder = request.env['purchase.bid.vendor'].sudo().search([('bid_id', '=', event.bid_id.id),
                                                          ('partner_id', '=', request.env.user.partner_id.id)], limit=1)
            return request.render("skit_vendor_portal.portal_my_bid_event_confirmation", {
                'attendees': attendees,
                'event': event,
                'google_url': urls.get('google_url'),
                'iCal_url': urls.get('iCal_url'),
                'page_name': 'bid',
                'order': bidder,
                'is_bid_event': True
            })

        return request.redirect("/shop/checkout")


class VendorDashboard(Website):

    @http.route(['/bid/decline'], type='json', auth="public",
                methods=['POST'], website=True)
    def bid_decline(self, **kw):
        """ set status to decline for bidder.
            @return true.
        """
        bidder = request.env['purchase.bid.vendor'].sudo().browse(int(kw.get('id')))
        bidder.write({'state': 'decline'})
        return True

    @http.route(['/bid/accept'], type='json', auth="public",
                methods=['POST'], website=True)
    def bid_accept(self, **kw):
        """ set status to accept for bidder.
            @return true.
        """
        bidder = request.env['purchase.bid.vendor'].sudo().browse(int(kw.get('id')))
        bidder.action_accept()
        bidder.write({'non_disc_agreement': True,
                      'date_aggreed': date.today()})
        """ Create Signature attachment"""
        Attachments = request.env['ir.attachment']
        Attachments.sudo().create({
            'name': kw.get('name'),
            'res_name': kw.get('name'),
            'type': 'binary',
            'res_model': 'purchase.bid.vendor',
            'datas': kw.get('signature'),
            'res_id': bidder.id
        })
        return True

    @http.route(['/show/nda'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_nda(self, **kw):
        bid = request.env['purchase.bid'].sudo().browse(int(kw.get('bid_id')))
        bidder = request.env['purchase.bid.vendor'].sudo().search([('bid_id', '=', bid.id),
                                                          ('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        nda_title = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.nda_title')
        nda_body = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.nda_body')
        values = {'bidder': bidder,
                  'nda_title': nda_title,
                  'nda_body': nda_body}
        if bidder.non_disc_agreement:
            return 'no_record'
        else:
            return request.env['ir.ui.view'].render_template(
                    "skit_vendor_portal.bid_nda_popup", values)

    @http.route(['/my_rfq_line/edit_view'], type='json', auth="public",
                methods=['POST'], website=True)
    def edit_office_address(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        rfq_mail_line_id = kw.get('rfq_mail_line_id')
        rfq_mail_line_vals = kw.get(rfq_mail_line_id)
        if(rfq_mail_line_vals):
            if(rfq_mail_line_vals.get('validity_from')):
                validity_from = rfq_mail_line_vals['validity_from']
                try:
                    lang = request.env['ir.qweb.field'].user_lang()
                    dt = datetime.strptime(validity_from, lang.date_format)
                except ValueError:
                    dt = datetime.strptime(validity_from, DEFAULT_SERVER_DATE_FORMAT)
                rfq_mail_line_vals['validity_from'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
            if(rfq_mail_line_vals.get('validity_to')):
                validity_to = rfq_mail_line_vals['validity_to']
                try:
                    lang = request.env['ir.qweb.field'].user_lang()
                    dt = datetime.strptime(validity_to, lang.date_format)
                except ValueError:
                    dt = datetime.strptime(validity_to, DEFAULT_SERVER_DATE_FORMAT)
                rfq_mail_line_vals['validity_to'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
            rfq_mail_line_vals = rfq_mail_line_vals
        else:
            rfq_mail_line_vals = {}

        rfq_mail_line = request.env['admin.request.for.quotation.line.vendor'].sudo().search([('id', '=', int(rfq_mail_line_id))])
        values = (rfq_mail_line_vals)
        values['line'] = rfq_mail_line
        if values.get('price'):
            price = float(values.get('price'))
        else:
            price = rfq_mail_line.price
        price = ('{:.2f}').format(price)
        values['price'] = price
        if values.get('gross_total'):
            gross_total = float(values.get('gross_total'))
        else:
            gross_total = rfq_mail_line.gross_total
        gross_total = ('{:.2f}').format(gross_total)
        values['gross_total'] = gross_total
        if values.get('delivery_cost'):
            delivery_cost = float(values.get('delivery_cost'))
        else:
            delivery_cost = rfq_mail_line.delivery_cost
        delivery_cost = ('{:.2f}').format(delivery_cost)
        values['delivery_cost'] = delivery_cost
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.view_rfq_line_popup",
                                                         values)

    @http.route(['/update/rfq/declined_status'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_rfq_declined_status(self, **kw):
        """ Update RFI Declined status.
            @return popup.
        """
        rfq_mail = request.env['admin.vendor.rfq'].sudo().search([
                                        ('id', '=', int(kw.get('rfq_mail_id')))])
        if rfq_mail:
            rfq_mail.update({'state': 'declined',
                             'declined_note': kw.get('declined_note'),
                             'declined_reason_id': int(kw.get('reason_id'))
                            })
            """ Send email for purchasing Officer """
            template = request.env.ref('skit_vendor_portal.mail_template_rfq_decline_email', raise_if_not_found=False)
            mail_template = request.env['mail.template'].sudo().browse(template.id)

            mail_id = mail_template.send_mail(rfq_mail.id, force_send=True)
            mail_mail_obj = request.env['mail.mail'].sudo().search(
                            [('id', '=', mail_id)]
                            )
            mail_mail_obj.send()

    @http.route(['/rfq/decline_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def rfq_decline_popup(self, **kw):
        """ Display PO Decline form.
            @return popup.
        """
        decline_reason = request.env['admin.declined.reason'].sudo().search([])
        values = ({
                    'decline_reason': decline_reason,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.rfq_decline_popup",
                                                         values)

    @http.route(['/my_rfp_line/edit_view'], type='json', auth="public",
                methods=['POST'], website=True)
    def edit_rfp_line(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        rfp_mail_line_id = kw.get('rfp_mail_line_id')
        rfp_mail_line = request.env['admin.request.for.proposal.line.product'].sudo().search([('id', '=', rfp_mail_line_id)])
        values = (kw)
        values['line'] = rfp_mail_line

        return request.env['ir.ui.view'].render_template("skit_vendor_portal.edit_rfp_line_details",
                                                         values)

    @http.route(['/my_rfp_line/delete_view'], type='json', auth="public",
                methods=['POST'], website=True)
    def delete_rfp_line(self, **kw):
        """ Render the new site address row template """
        rfp_line_id = kw.get('rfq_mail_line_delete_id')
        rfp_mail_line = request.env['admin.request.for.proposal.line.product'].sudo().search([('id', '=', rfp_line_id)])
        rfp_mail_line.unlink()

    @http.route(['/update/rfp/declined_status'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_rfp_declined_status(self, **kw):
        """ Update RFP Declined status.
            @return popup.
        """
        rfp_mail = request.env['admin.request.for.proposal.line'].sudo().search([
                                        ('rfp_id', '=', int(kw.get('rfp_mail_id')))])
        if rfp_mail:
            rfp_mail.update({'state': 'declined',
                             'declined_note': kw.get('declined_note'),
                             'declined_reason_id': int(kw.get('reason_id'))
                             })

    @http.route(['/rfp/decline_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def rfp_decline_popup(self, **kw):
        """ Display PO Decline form.
            @return popup.
        """
        decline_reason = request.env['admin.declined.reason'].sudo().search([])
        values = ({
                    'decline_reason': decline_reason,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.rfp_decline_popup",
                                                         values)

    @http.route('/rfp_mail/accept_state/', type='json', auth='user', website=True)
    def accepted_rfp_mail(self, **kw):
        post = kw.get('post')
        partner = request.env.user.partner_id
        rfp_mail_id = int(post.get('rfp_mail_id'))
        rfp_mail = request.env['admin.request.for.proposal.line'].sudo().search([
                            ('rfp_id', '=', rfp_mail_id),
                            ('partner_id', '=', partner.id)], limit=1)

        rfp_mail.sudo().write({'state': 'accepted'})
        return json.dumps({
            'id': rfp_mail.id
        })

    @http.route('/rfp_mail_line/save/', type='json', auth='user', website=True)
    def send_validation_email(self, **kw):
        post = kw.get('post_all')
        if post:
            for rfp_line_id in post.keys():
                rfp_line_vals = post.get(rfp_line_id)
                rfp_line = request.env['admin.request.for.proposal.line.product'].sudo().search([('id', '=', int(rfp_line_id))])
                if rfp_line.display_type == 'line_section' or rfp_line.display_type == 'line_note':
                    rfp_line_vals['name'] = rfp_line_vals.get('product_name')
                    rfp_line_vals['product_name'] = ''
                rfp_line.sudo().write(rfp_line_vals)
                if rfp_line.rfp_line_id.state != 'accepted':
                    rfp_line.rfp_line_id.sudo().write({'state':'accepted'})

        for new_rfp in kw.get('new_rfp_line'):
            rfp_line = request.env['admin.request.for.proposal.line'].sudo().browse(int(kw.get('new_rfp_id')))
            new_rfp['rfp_line_id'] = rfp_line.id
            request.env['admin.request.for.proposal.line.product'].sudo().create(new_rfp)
            if rfp_line.state != 'accepted':
                rfp_line.sudo().write({'state': 'accepted'})
        # Update other info in rfp mail
        if kw.get('rfp_id') and kw.get('other_info'):
            rfp_line = request.env['admin.request.for.proposal.line'].sudo().search(
                                [('id', '=', int(kw.get('rfp_id')))])
            rfp_line.write({'other_term_warranty': kw.get('other_info')})
        return True

    @http.route('/rfp_mail_line/submit_as_proposal/', type='json', auth='user', website=True)
    def rfp_submit_as_proposal(self, **kw):
        post = kw.get('post_all')
        if post:
            for rfp_line_id in post.keys():
                rfp_line_vals = post.get(rfp_line_id)
                rfp_line = request.env['admin.request.for.proposal.line.product'].sudo().search([('id', '=', int(rfp_line_id))])
                if rfp_line.display_type == 'line_section' or rfp_line.display_type == 'line_note':
                    rfp_line_vals['name'] = rfp_line_vals.get('product_name')
                    rfp_line_vals['product_name'] = ''
                rfp_line.sudo().write(rfp_line_vals)
                rfp_line.rfp_line_id.sudo().write({'state':'submitted'})
        for new_rfp in kw.get('new_rfp_line'):
            rfp_line = request.env['admin.request.for.proposal.line'].sudo().browse(int(kw.get('new_rfp_id')))
            new_rfp['rfp_line_id'] = rfp_line.id
            request.env['admin.request.for.proposal.line.product'].sudo().create(new_rfp)
            if rfp_line.state != 'submitted':
                rfp_line.sudo().write({'state':'submitted'})
        # Update other info in rfp mail
        if kw.get('rfp_id') and kw.get('other_info'):
            rfp_line = request.env['admin.request.for.proposal.line'].sudo().search(
                                [('id', '=', int(kw.get('rfp_id')))])
            rfp_line.write({'other_term_warranty': kw.get('other_info')})
        return True

    @http.route(['/save/edit_or'], type='json', auth="user", website=True)
    def save_edit_or_Details(self, **kw):
        """ Update Payment Details"""

        payment = request.env['admin.invoice.payment'].sudo().search(
                            [('id', '=', int(kw.get('pay_id')))])
        datas = kw.get('datas')
        # <-- START Convert date widget data to database format
        or_date = datas['or_date']
        if or_date:
            try:
                lang = request.env['ir.qweb.field'].user_lang()
                dt = datetime.strptime(or_date, lang.date_format)
            except ValueError:
                dt = datetime.strptime(or_date, DEFAULT_SERVER_DATE_FORMAT)
            datas['or_date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        if payment:
            payment.write(datas)
        file_details = kw.get('pay_files')
        if(file_details and file_details[0].get('file_content')):
            # Create Attachment
            self.payment_create_attachment(payment, file_details)

    # Create Attachments
    def payment_create_attachment(self, payment, file_datas):
        """ Create attachment in Payments"""
        IrAttachment = request.env['ir.attachment'].sudo()
        attachment = False
        for file in file_datas:
            file_content = file['file_content']
            file_content = file_content.split(',')[1]
            attachment = IrAttachment.create({
                    'name': file['file_name'],
                    'res_name': file['file_name'],
                    'datas': file_content,
                    'res_model': 'admin.invoice.payment',
                    'type': 'binary',
                    'res_id': payment.id
            })
        return attachment

    @http.route(['/save/bidder/requirement'], type='json', auth="user", website=True)
    def save_bidder_document(self, **kw):
        if kw.get('bidder_id'):
            bidder = request.env['purchase.bid.vendor'].sudo().browse(int(kw.get('bidder_id')))
            bidder.write({'document_requirement_id': [(6, 0, kw.get('required_ids'))]})
        return True

    @http.route(['/save/accredit/requirement'], type='json', auth="user", website=True)
    def save_accredit_document(self, **kw):
        if kw.get('acc_id'):
            accredit = request.env['partner.evaluation'].sudo().browse(int(kw.get('acc_id')))
            accredit.write({'document_accreditation_requirement_ids': [(6, 0, kw.get('accr_doc_ids'))]})
        return True
