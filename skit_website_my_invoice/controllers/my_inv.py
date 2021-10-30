# -*- coding: utf-8 -*-

from odoo import api, http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo.exceptions import AccessError, MissingError
from odoo.tools import image_process

from odoo.tools.translate import _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv.expression import OR
import re

from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager, CustomerPortal


class PortalMyinvoice(CustomerPortal):

    def _prepare_home_portal_values(self):
        values = super(PortalMyinvoice, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id
        invoice_count = request.env['admin.sales.invoice'].search_count(
                                [('vendor_partner_id', '=', partner.id)])
        values['invoice_count'] = invoice_count
        return values

    def is_date(self, string):
        match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', string)
        return match

    def is_float(self, pricefloat):
        match = re.search('^[1-9]\d*(\.\d+)?$', pricefloat)
        return match

    @http.route(['/my/myinvoices', '/my/myinvoices/page/<int:page>', '/my/myinvoices/<string:state>'], type='http', auth="user", website=True)
    def sks_portal_my_invoices(self, page=1, state=None, date_begin=None, date_end=None, sortby=None,search=None, search_in='content', **kw):
        values = {}
        domain = []
        partner = request.env.user.partner_id
        domain += [('vendor_partner_id','=',partner.id)]
        if(state):
            if(state == 'Original Documents Received'):
                state = "Original Documents Received"
            elif(state == 'Original Documents Review'):
                state = "Original Documents Review"
            elif(state == 'Waiting for Accounting Validation'):
                state = "Waiting for Accounting Validation"
            elif(state == 'Awaiting Original Document'):
                state = "Awaiting Original Document"
            elif(state == 'Returned to Vendor'):
                state = "Returned to Vendor"

            domain += [('document_status', '=', state)]

        searchbar_sortings = {
            'invoice_date': {'label': _('Invoice Date'), 'order': 'invoice_date desc'},
            'vendor_si_number': {'label': _('SI No'), 'order': 'vendor_si_number desc'},
            'document_status': {'label': _('Status'), 'order': 'document_status desc'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},

        }
        # search
        if search and search_in:
            search_domain = []
            search_state = search
            if search_in in ('content', 'all'):
                if (search == 'Original Documents Received'):
                    search_state = 'Original Documents Received'
                if (search == 'Original Documents Review'):
                    search_state = 'Original Documents Review'
                if (search == 'Waiting for Accounting Validation'):
                    search_state = 'Waiting for Accounting Validation'
                if (search == 'Awaiting Original Documents'):
                    search_state = 'Awaiting Original Documents'
                if (search == 'Returned to Vendor'):
                    search_state = 'Returned to Vendor'

                search_amount = None
                if(self.is_float(search)):
                    search_amount = search
                search_from = None
                search_to = None
                if(self.is_date(search)):
                    search_from = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
                    search_to = datetime.strptime(search, '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
                search_domain = OR([search_domain, ['|', '|','|', ('vendor_si_number', 'ilike', search), ('amount', '=', search_amount),
                                                   '&', ('invoice_date', '>=', search_from), ('invoice_date', '<=', search_to), 
                                                   ('document_status', 'ilike', search_state)]])
            domain += search_domain
        # default sort by order
        if not sortby:
            sortby = 'invoice_date'
        order = searchbar_sortings[sortby]['order']

        # count for pager
        invoice_count = request.env['admin.sales.invoice'].search_count(domain)

        # pager
        pager = portal_pager(
            url="/my/myinvoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        invoices = request.env['admin.sales.invoice'].search(domain, order=order, limit=self._items_per_page,
                                                             offset=pager['offset'])

        vals = []
        for invoice in invoices:
            payment = request.env['admin.invoice.payment'].search([('admin_si_id', '=', invoice.id)])
            delivery = request.env['po.delivery.line'].search([('po_id', '=', invoice.purchase_id.id)])
            inv_payment = request.env['admin.invoice.payment'].search([('admin_si_id', '=', invoice.id)],order="id desc",limit=1)
            vals.append({'invoices': invoice,
                         'payments': payment,
                         'delivery_line': delivery,
                         'inv_payment':inv_payment})
        request.session['my_saleinvoices_history'] = invoices.ids[:100]
 
        values.update({
            'sendsi': True,
            'date': date_begin,
            'invoices': vals,
            'page_name': 'invoice',
            'pager': pager,
            'default_url': '/my/myinvoices',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
        })

        return request.render("skit_website_my_invoice.sks_portal_my_invoices", values)

    @http.route(['/my/myinvoice/<int:invoice_id>'], type='http', auth="public", website=True)
    def sks_portal_my_invoices_form(self, invoice_id=None, access_token=None, **kw):
        " Get Respective Sale Invoice Details "
        values = {}
        my_invoice_form = request.env['admin.sales.invoice'].sudo().search(
                                        [('id', '=', invoice_id)])
        payment = request.env['admin.invoice.payment'].sudo().search(
                                    [('admin_si_id', '=', my_invoice_form.id)])
        # Get SI Attachments
        si_attachments = request.env['ir.attachment'].sudo().search(
                                    [('res_model', '=', 'admin.sales.invoice'),
                                     ('res_id', '=', my_invoice_form.id)])
        values['my_invoice_form'] = my_invoice_form
        values['page_name'] = 'invoice'
        values['my_payment'] = payment
        values['my_delivery'] = my_invoice_form.po_delivery_ids
        values['attachments'] = si_attachments
        # Get pager navigation
        history = request.session.get('my_saleinvoices_history', [])
        values.update(get_records_pager(history, my_invoice_form))
        return request.render("skit_website_my_invoice.sks_portal_my_invoices_form", values)

    @http.route(['/si/edit_payment'], type='json', auth="public",
                methods=['POST'], website=True)
    def edit_si_payment(self, **kw):
        " Edit Payment Line"
        values = {}
        payment = request.env['admin.invoice.payment'].sudo().search(
                                    [('id', '=', kw.get('pay_id'))])
        file_attached = False
        file_attachments = []
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', int(kw.get('pay_id'))),
                            ('res_model', '=', 'admin.invoice.payment')])
        if attachments:
            file_attached = True
            for attachment in attachments:
                file_attachments.append({'pfile_content': attachment.datas,
                                         'pfile_name': attachment.name,
                                         'type': attachment.type,
                                         'id': attachment.id})
        values['file_attached'] = file_attached
        values['file_attachments'] = file_attachments
        values['payment'] = payment
        return request.env['ir.ui.view'].render_template(
            "skit_website_my_invoice.si_payment_edit_popup", values)

    @http.route(['/save/si_payment'], type='json', auth="public",
                methods=['POST'], website=True)
    def save_pro_service(self, **kw):
        """ Update Edited SI Payments.
            @return True.
        """
        si_payment = request.env['admin.invoice.payment'].sudo().browse(int(kw.get('pay_id')))
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', si_payment.id),
                            ('res_model', '=', 'admin.invoice.payment')])
        datas = kw.get('datas')
        # <-- START Convert date widget data to database format
        if(datas.get('or_date')):
            or_date = datas['or_date']
            try:
                lang = request.env['ir.qweb.field'].user_lang()
                dt = datetime.strptime(or_date, lang.date_format)
            except ValueError:
                dt = datetime.strptime(or_date, DEFAULT_SERVER_DATE_FORMAT)
            datas['or_date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if datas['name']:
            datas.pop('relesed_amount')
            datas.pop('payment_release_date')
            datas.pop('name')
        amount = datas['amount']
        if amount:
            datas['amount'] = float(amount)
        if si_payment:
            si_payment.write(datas)
        """ Attachment """
        file_att_ids = []
        file_details = kw.get('pay_files')
        if(file_details and file_details[0].get('file_content')):
            for file in file_details:
                file_att_id = int(file['att_id'])
                if(file_att_id > 0):
                    file_att_ids.append(file_att_id)
                else:
                    attachment = self.payment_orcopy_attachment(file)
                    attachment.write({'res_id': si_payment.id})
        else:
            if kw.get('file_attach'):
                attachment = request.env['ir.attachment'].sudo().search([
                                ('res_id', '=', si_payment.id)])
                if attachment:
                    attachment.unlink()
        remove_att_ids = list(set(attachments.ids) - set(file_att_ids)) 
        if len(remove_att_ids) > 0:
            attachment = request.env['ir.attachment'].sudo().search([
                                ('id', 'in', remove_att_ids)])
            if attachment:
                attachment.unlink()
        values = {}
        values['si_payment_line'] = si_payment
        return values

    # Create OR copy
    def payment_orcopy_attachment(self, file):
        " Create Attachment in payment"
        Attachments = request.env['ir.attachment']
        file_content = file['file_content']
        file_content = file_content.split(',')[1]
        attachment = Attachments.sudo().create({
            'name': file['file_name'],
            'res_name': file['file_name'],
            'type': 'binary',
            'res_model': 'admin.invoice.payment',
            'datas': file_content
        })
        return attachment

    @http.route(['/show/sipaymentattach/popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def sipayment_multi_file_popup(self, **kw):
        """ Show multi attachment.
        @return popup.
        """
        attachments = request.env['ir.attachment'].sudo().search([
                        ('res_id', '=', int(kw.get('pay_id'))),
                        ('res_model', '=', 'admin.invoice.payment')])
        values = {'attachments': attachments}
        return request.env['ir.ui.view'].render_template("skit_website_my_po.show_dl_attachments_template",
                                                         values)

    @http.route(['/send_si/popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def send_sales_invoice(self, **kw):
        """ Display Send SI form
            @return: popup
        """
        values = {}
        partner = request.env.user.partner_id
        # Get Locked and Purchase PO
        purchase_orders = request.env['purchase.order'].sudo().search([
                                            ('state', 'in', ['purchase', 'done']),
                                            ('partner_id', '=', partner.id)])
        selected_po_order = request.env['purchase.order'].sudo().browse(int(kw.get('po_id')))
        values['purchase_orders'] = purchase_orders
        values['selected_po_order'] = selected_po_order
        return request.env['ir.ui.view'].render_template(
                    "skit_website_my_invoice.sales_invoice_popup",values)

    @http.route(['/show/dr_number_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_dr_number_popup(self, **kw):
        """ Display Delivery form
            @return: popup
        """
        values = {}
        purchase_order = False
        if kw.get('selected_po') and kw.get('with_po'):
            purchase_order = request.env['purchase.order'].sudo().search(
                                [('id', '=', int(kw.get('selected_po')))])
            po_delivery_lns = request.env['po.delivery.line'].sudo().search(
                                [('po_id', '=', int(kw.get('selected_po')))])
            sales_invoices = request.env['admin.sales.invoice'].sudo().search(
                                [('purchase_id', '=', int(kw.get('selected_po')))])
        else:
            po_delivery_lns = request.env['po.delivery.line'].sudo().search([
                                    ('partner_id', '=', request.env.user.partner_id.id),
                                    ('po_id', '=', None),
                                    ])
            sales_invoices = request.env['admin.sales.invoice'].sudo().search([
                    ('vendor_partner_id', '=', request.env.user.partner_id.id)
                    ])
        si_po_delivery_ids = []
        for data in sales_invoices:
            for d_id in data.po_delivery_ids.ids:
                si_po_delivery_ids.append(d_id)
        dr_no = list(set(po_delivery_lns.ids) - set(si_po_delivery_ids))
        dr_items = list(sorted(set(dr_no) - set(kw.get('added_drs'))))
        values['dr_ids'] = dr_items
        values['purchase_order'] = purchase_order

        return request.env['ir.ui.view'].render_template(
                    "skit_website_my_invoice.dr_number_popup",values)

    @http.route(['/show/linked_dr_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_linked_dr_popup(self, **kw):
        """While select DR and Send SI....
        if that DR already in SI, need to pop up alert msg."""
        values = {'linked_dr': kw.get('linked_dr')}
        return request.env['ir.ui.view'].render_template(
                            "skit_website_my_invoice.selected_dr_warning_popup", values)

    # Create Attachments
    def si_create_attachment(self, salesinvoice, file_datas):
        """ Create attachment in Sales Invoice """
        IrAttachment = request.env['ir.attachment'].sudo()
        attachment = False
        for file in file_datas:
            file_content = file['file_content']
            file_content = file_content.split(',')[1]
            attachment = IrAttachment.create({
                    'name': file['file_name'],
                    'res_name': file['file_name'],
                    'datas': file_content,
                    'res_model': 'admin.sales.invoice',
                    'type': 'binary',
                    'res_id': salesinvoice.id
            })
        return attachment

    @http.route(['/save/sales_invoice'], type='json', auth="public",
                methods=['POST'], website=True)
    def save_sales_invoice(self, **kw):
        """ Create Sales Invoice """
        partner = request.env.user.partner_id
        if kw.get('po_number'):
            po = request.env['purchase.order'].sudo().browse(int(kw.get('po_number')))
            po_amt = po.amount_total
            inv = request.env['admin.sales.invoice'].sudo().search(
                            [('purchase_id', '=', int(kw.get('po_number')))])
            if po_amt < (float(kw.get('si_amount')) + sum([r.amount for r in inv])):
                return request.env['ir.ui.view'].render_template(
                            "skit_website_my_invoice.amount_warning_popup")
        si_data = {
            'admin_si_type': 'with_po' if kw.get('with_po') else 'no_po' if kw.get('without_po') else '',
            'po_si_type': 'Goods or Services' if kw.get('good_serv') else 'Hauler/Delivery Charge' if kw.get('delivery_charge') else '',
            'vendor_si_number': kw.get('si_number') if kw.get('si_number') else None,
            'company_code': kw.get('si_company') if kw.get('si_company') else None,
            'service_order_number': kw.get('serv_order_no') if kw.get('serv_order_no') else None,
            'vendor_partner_id': partner.id,
            'purchase_id': int(kw.get('po_number')) if kw.get('po_number') else False,
            'vendor_remarks': kw.get('vendor_remarks') if kw.get('vendor_remarks') else None,
            'amount': float(kw.get('si_amount')),
            'invoice_date': kw.get('si_date'),
            'po_delivery_ids': [(4, request.env['po.delivery.line'].sudo().search([('id', '=', dr_line)]).id, None) for dr_line in kw.get('dr_list')],  
        }
        # <-- START Convert date widget data to database format
        invoice_date = si_data['invoice_date']
        try:
            lang = request.env['ir.qweb.field'].user_lang()
            dt = datetime.strptime(invoice_date, lang.date_format)
        except ValueError:
            dt = datetime.strptime(invoice_date, DEFAULT_SERVER_DATE_FORMAT)
        si_data['invoice_date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        vendor_si = request.env['admin.sales.invoice'].sudo().create(si_data)
        file_details = kw.get('si_files')
        if(file_details and file_details[0].get('file_content')):
            # Create Attachment
            self.si_create_attachment(vendor_si, file_details)
        if vendor_si.id:
            return request.env['ir.ui.view'].render_template(
                    "skit_website_my_invoice.si_submit_popup")

    @http.route(['/get/po_company'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_po_company(self, **kw):
        " Get company code "
        if kw.get('po'):
            po = request.env['purchase.order'].sudo().search(
                            [('id', '=', int(kw.get('po')))])
            return po.company_code
        
    @http.route(['/show/vp_si_document'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_si_documents(self, **kw):
        """ Display sales invoice document.
        @return popup.
        """
        attachment = request.env['ir.attachment'].sudo().browse(int(kw.get('att_id')))
        values = {'attachment': attachment}
        return request.env['ir.ui.view'].render_template("skit_website_my_invoice.show_inv_si_attached_files", values)
