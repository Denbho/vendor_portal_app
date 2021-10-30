# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv.expression import OR
import re
from odoo.addons.website.controllers.main import Website
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal


class MyPurchaseOrderPortal(Website):

    @http.route(['/po/decline_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def po_decline_popup(self, **kw):
        """ Display PO Decline form.
            @return popup.
        """
        decline_reason = request.env['admin.declined.reason'].sudo().search([])
        values = ({
                    'decline_reason': decline_reason,
                   })
        return request.env['ir.ui.view'].render_template("skit_website_my_po.po_decline_popup",
                                                         values)

    @http.route(['/update/po/declined_status'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_declined_status(self, **kw):
        """ Update PO Declined status.
            @return popup.
        """
        purchase_order = request.env['purchase.order'].sudo().search([
                                        ('id', '=', int(kw.get('order_id')))])
        if purchase_order:
            purchase_order.update({'acceptance_status': 'declined',
                                   'declined_note': kw.get('declined_note'),
                                   'declined_reason_id': int(kw.get('reason_id'))
                                   })

    @http.route(['/update/po/accept_status'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_accepted_status(self, **kw):
        """ Update PO Accepted status.
            @return popup.
        """
        purchase_order = request.env['purchase.order'].sudo().search([
                                        ('id', '=', int(kw.get('order_id')))])
        if purchase_order:
            purchase_order.update({'acceptance_status': 'accepted',
                                   })

    @http.route(['/create/po_delivery'], type='json', auth="public",
                methods=['POST'], website=True)
    def create_po_delivery(self, **kw):
        """ Create and edit purchase order delivery.
            @return popup.
        """
        values = kw.get('datas')
        values['po_id'] = kw.get('po_id')
        values['dl_id'] = kw.get('id')
        file_attached = False
        file_attachments = []
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', int(kw.get('id'))),
                            ('res_model', '=', 'po.delivery.line')])
        if attachments:
            file_attached = True
            for attachment in attachments:
                file_attachments.append({'pfile_content': attachment.datas,
                                         'pfile_name': attachment.name,
                                         'type': attachment.type,
                                         'id': attachment.id})
        values['file_attached'] = file_attached
        values['file_attachments'] = file_attachments
        sales_invoice = request.env['admin.sales.invoice'].sudo().search([('po_delivery_ids', 'in', [int(kw.get('id'))])], limit=1)
        values['sales_invoice'] = sales_invoice
        delivery_data = request.env['po.delivery.line'].sudo().browse(int(kw.get('id')))
        values['delivery_data'] = delivery_data
        return request.env['ir.ui.view'].render_template(
            "skit_website_my_po.po_delivery_creation_popup", values)

    @http.route(['/save/po_delivery'], type='json', auth="public",
                methods=['POST'], website=True)
    def save_po_delivery(self, **kw):
        """ Save the purchase order delivery.
            @return True.
        """
        po_delivery = request.env['po.delivery.line'].sudo().browse(int(kw.get('dl_id')))
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', po_delivery.id),
                            ('res_model', '=', 'po.delivery.line')])
        datas = kw.get('datas')
        if kw.get('po_id'):
            datas['po_id'] = int(kw.get('po_id'))
        # <-- START Convert date widget data to database format
        received_date = datas['receiving_date']
        try:
            lang = request.env['ir.qweb.field'].user_lang()
            dt = datetime.strptime(received_date, lang.date_format)
        except ValueError:
            dt = datetime.strptime(received_date, DEFAULT_SERVER_DATE_FORMAT)
        datas['receiving_date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        dr_date = datas['dr_date']
        try:
            lang = request.env['ir.qweb.field'].user_lang()
            dt = datetime.strptime(dr_date, lang.date_format)
        except ValueError:
            dt = datetime.strptime(dr_date, DEFAULT_SERVER_DATE_FORMAT)
        datas['dr_date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        # Convert date widget data to database format END-->

        if(int(kw.get('dl_id')) > 0):
            po_delivery.write(datas)
        else:
            # update vendor details in DR
            datas['partner_id'] = request.env.user.partner_id.id
            po_delivery = request.env['po.delivery.line'].sudo().create(datas)
        """ Attachment """
        file_att_ids = []
        file_details = kw.get('dl_files')
        if(file_details and file_details[0].get('file_content')):
            for file in file_details:
                file_att_id = int(file['att_id'])
                if(file_att_id > 0):
                    file_att_ids.append(file_att_id)
                else: 
                    attachment = self.po_create_attachment(file)
                    attachment.write({'res_id': po_delivery.id})
        else:
            if kw.get('file_attch'):
                attachment = request.env['ir.attachment'].sudo().search([
                                ('res_id', '=', po_delivery.id)])
                if attachment:
                    attachment.unlink()
        remove_att_ids = list(set(attachments.ids) - set(file_att_ids)) 
        if len(remove_att_ids) > 0:
            attachment = request.env['ir.attachment'].sudo().search([
                                ('id', 'in', remove_att_ids)])
            if attachment:
                attachment.unlink()
        values = {}
        values['delivery_line'] = po_delivery
        if kw.get('po_id'):
            values['po_id'] = int(kw.get('po_id'))
        return request.env['ir.ui.view'].render_template("skit_website_my_po.new_delivery_line", values)

    def po_create_attachment(self, file):
        " Create attachment for PO delivery line"
        Attachments = request.env['ir.attachment']
        file_content = file['file_content']

        file_content = file_content.split(',')[1]
        attachment = Attachments.sudo().create({
            'name': file['file_name'],
            'res_name': file['file_name'],
            'type': 'binary',
            'res_model': 'po.delivery.line',
            'datas': file_content
        })
        return attachment

    @http.route(['/show/dl_document'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_documents(self, **kw):
        """ Display delivery document.
        @return popup.
        """
        attachment = request.env['ir.attachment'].sudo().browse(int(kw.get('att_id')))
        values = {'attachment': attachment}
        return request.env['ir.ui.view'].render_template("skit_website_my_po.show_dl_attached_files", values)

    @http.route(['/show/attach/popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_multi_attchment_popup(self, **kw):
        """ Show multi attachment.
        @return popup.
        """
        attachments = request.env['ir.attachment'].sudo().search([
                        ('res_id', '=', kw.get('po_del_id')),
                        ('res_model', '=', 'po.delivery.line')])
        values = {'attachments': attachments}
        return request.env['ir.ui.view'].render_template("skit_website_my_po.show_dl_attachments_template", values)

    @http.route(['/delete/po_delivery'], type='json', auth="public",
                methods=['POST'], website=True)
    def delete_delivery_line(self, **kw):
        """ Delete the delivery line.
        @return popup.
        """
        delivery_line = request.env['po.delivery.line'].sudo().browse(int(kw.get('id')))
        delivery_line.unlink()
        return True

    @http.route(['/print/pdf/<int:order_id>'],  type='http', auth="public",
                website=True)
    def print_pdf(self, order_id=None, **kw):
        """ Print - PO
            if PO is already Printed
            @ return reprint template
        """
        purchase_order = request.env['purchase.order'].sudo().search([
                                        ('id', '=', int(order_id))])
        isprint = purchase_order.isprint
        if purchase_order and not purchase_order.isprint:
            purchase_order.update({'isprint': True,
                                   })
        if (isprint):
            return request.redirect('/report/pdf/skit_website_my_po.watermark_report_purchaseorder/'+str(order_id))
        else:
            return request.redirect('/report/pdf/purchase.report_purchaseorder/'+str(order_id))

    @http.route(['/update/or_number'],  type='json', auth="public",
                methods=['POST'], website=True)
    def update_or_number(self, **kw):
        " Update OR number in Payment"
        payment = request.env['admin.invoice.payment'].sudo().search([
                                        ('id', '=', int(kw.get('id')))])
        payment.write({'or_number': kw.get('or_number')})
        return True

    @http.route(['/upload/payment/attachment'], type='json', auth="public",
                methods=['POST'], website=True)
    def upload_payment_attachment(self, **kw):
        " Upload file in Payment from PO screen"
        file_details = kw.get('po_pay_attch_file_list')
        if(file_details and file_details[0].get('file_content')):
            for file in file_details:
                Attachments = request.env['ir.attachment']
            file_content = file['file_content']

            file_content = file_content.split(',')[1]
            Attachments.sudo().create({
                'name': file['file_name'],
                'res_name': file['file_name'],
                'type': 'binary',
                'res_model': 'admin.invoice.payment',
                'datas': file_content,
                'res_id': int(kw.get('id'))
            })
        return True


class PortalMyPurchase(CustomerPortal):

    def is_date(self, string):
        match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', string)
        return match

    def is_float(self, pricefloat):
            match = re.search('^[1-9]\d*(\.\d+)?$', pricefloat)
            return match

    # Overwrite this method to add searchbar

    @http.route(['/my/purchase', '/my/purchase/page/<int:page>', '/my/purchase/<string:state>'], type='http',
                auth="user", website=True)
    def portal_my_purchase_orders(self, page=1, state=None, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()

        PurchaseOrder = request.env['purchase.order']

        domain = []
        # Display only Purchase and Done PO
        domain += [('state', 'in', ['purchase', 'done'])]
        if(state):
            if(state == 'Undelivered'):
                state = "undelivered"
            elif(state == 'Partially Delivered'):
                state = "partially_delivered"
            elif(state == 'Fully Delivered'):
                state = "fully_delivered"
            domain += [('sap_delivery_status', '=', state.lower())]
        archive_groups = self._get_archive_groups('purchase.order', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'name': {'label': _('PO No'), 'order': 'name desc, id desc'},
            'company_code': {'label': _('Company'), 'order': 'company_code desc, id desc'},
            'date_order': {'label': _('PO Date'), 'order': 'date_order desc, id desc'},
            'amount_total': {'label': _('PO Amount'), 'order': 'amount_total desc, id desc'},
            'company_code': {'label': _('Company'), 'order': 'company_code desc, id desc'},
            'acceptance_status': {'label': _('Acceptance Status'), 'order': 'acceptance_status asc, id asc'},
            'sap_delivery_status': {'label': _('Delivery Status'), 'order': 'sap_delivery_status asc, id asc'},
            }
        # default sort by value
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},

        }
        # search
        if search and search_in:
            search_domain = []
            search_state = search
            if search_in in ('content', 'all'):
                if (search == 'Declined'):
                    search_state = 'declined'
                if (search == 'Accepted'):
                    search_state = 'accepted'
                if (search == 'Waiting for Acceptance'):
                    search_state = None
                if (search == 'Undelivered'):
                    search_state = 'undelivered'
                if (search == 'Partially Delivered'):
                    search_state = 'partially_delivered'
                if (search == 'Fully Delivered'):
                    search_state = 'fully_delivered'
                search_from = None
                search_to = None
                search_amount = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
                if(self.is_float(search)):
                    search_amount = search
                if (search_state.upper() in 'WAITING FOR ACCEPTANCE'):
                    search_domain = OR([search_domain, ['|', '|','|','|', '|', '|', ('name', 'ilike', search),
                                                    ('amount_total', '=', search_amount),
                                                    ('company_code', 'ilike', search),
                                                    ('acceptance_status', '=', False),
                                                    ('acceptance_status', 'ilike', search_state),
                                                    ('sap_delivery_status', 'ilike', search_state),
                                                    '&', ('date_order', '>=', search_from), ('date_order', '<=', search_to)
                                                    ]])
                else:
                    search_domain = OR([search_domain, ['|', '|','|','|', '|', ('name', 'ilike', search),
                                                        ('amount_total', '=', search_amount),
                                                        ('company_code', 'ilike', search),
                                                        ('acceptance_status', 'ilike', search_state),
                                                        ('sap_delivery_status', 'ilike', search_state),
                                                        '&', ('date_order', '>=', search_from), ('date_order', '<=', search_to)
                                                        ]])
            domain += search_domain

        # count for pager
        purchase_count = PurchaseOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=purchase_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchases_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'purchase',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'default_url': '/my/purchase',
        })
        return request.render("purchase.portal_my_purchase_orders", values)
