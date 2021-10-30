# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from datetime import date


class MyPONotification(Website):

    @http.route(['/purchase_order/notification/late'], type='http', auth="user", website=True)
    def late_notification(self, **kw):
        """ Get Past Purchase Order Details """
        values = {}
        partner = request.env.user.partner_id
        po_datas = []
        query = """ select po.expected_delivery_date from purchase_order po inner join purchase_order_line pol 
                on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                and ((po.expected_delivery_date::DATE - now()::DATE) < 0) and po.partner_id = %s
                group by po.expected_delivery_date """
        request.env.cr.execute(query, (partner.id,))
        result = request.env.cr.fetchall()
        for value in result:
            po_query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                        on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                        and ((po.expected_delivery_date::DATE - now()::DATE) < 0) and po.expected_delivery_date = %s and po.partner_id = %s
                        group by pol.order_id """
            request.env.cr.execute(po_query, (value[0], partner.id,))
            po_result = request.env.cr.fetchall()
            po_ids = []
            for po_value in po_result:
                po_ids.append(po_value[0])
            datas = {}
            datas['key'] = value[0]
            purchase_orders = request.env['purchase.order'].sudo().search([('id', 'in', po_ids)])
            datas['count'] = len(purchase_orders)
            datas['orders'] = purchase_orders
            if(len(purchase_orders) > 0):
                date_diff = purchase_orders[0].expected_delivery_date - date.today()
                days = date_diff.days
                if days < 0:
                    days = -(days)
                datas['days'] = days
                datas['vendor_name'] = purchase_orders[0].partner_id.name
            else:
                datas['days'] = 0
                datas['vendor_name'] = ''
            po_datas.append(datas)
        values['status'] = 'Late'
        values['po_datas'] = po_datas
        return request.render("skit_website_my_po.po_notification_template", values)

    @http.route(['/purchase_order/notification/today'], type='http', auth="user", website=True)
    def today_notification(self, **kw):
        """ Get Today Purchase Order Details """
        values = {}
        partner = request.env.user.partner_id
        po_datas = []
        query = """ select po.expected_delivery_date from purchase_order po inner join purchase_order_line pol 
                on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                and ((po.expected_delivery_date::DATE - now()::DATE) = 0) and po.partner_id = %s
                group by po.expected_delivery_date """
        request.env.cr.execute(query, (partner.id,))
        result = request.env.cr.fetchall()
        for value in result:
            po_query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                        on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                        and ((po.expected_delivery_date::DATE - now()::DATE) = 0) and po.expected_delivery_date = %s and po.partner_id = %s
                        group by pol.order_id """
            request.env.cr.execute(po_query, (value[0], partner.id,))
            po_result = request.env.cr.fetchall()
            po_ids = []
            for po_value in po_result:
                po_ids.append(po_value[0])
            datas = {}
            datas['key'] = value[0]
            purchase_orders = request.env['purchase.order'].sudo().search([('id', 'in', po_ids)])
            datas['count'] = len(purchase_orders)
            datas['orders'] = purchase_orders
            if(len(purchase_orders) > 0):
                date_diff = purchase_orders[0].expected_delivery_date - date.today()
                days = date_diff.days
                if days < 0:
                    days = -(days)
                datas['days'] = days
                datas['vendor_name'] = purchase_orders[0].partner_id.name
            else:
                datas['days'] = 0
                datas['vendor_name'] = ''
            po_datas.append(datas)
        values['status'] = 'Today'
        values['po_datas'] = po_datas
        return request.render("skit_website_my_po.po_notification_template", values)

    @http.route(['/purchase_order/notification/future'], type='http', auth="user", website=True)
    def future_notification(self, **kw):
        """ Get Future Purchase Order Details """
        values = {}
        partner = request.env.user.partner_id
        po_datas = []
        query = """ select po.expected_delivery_date from purchase_order po inner join purchase_order_line pol 
                on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                and ((po.expected_delivery_date::DATE - now()::DATE) > 0) and po.partner_id = %s
                group by po.expected_delivery_date """
        request.env.cr.execute(query, (partner.id,))
        result = request.env.cr.fetchall()
        for value in result:
            po_query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                        on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                        and ((po.expected_delivery_date::DATE - now()::DATE) > 0) and po.expected_delivery_date = %s and po.partner_id = %s
                        group by pol.order_id """
            request.env.cr.execute(po_query, (value[0], partner.id,))
            po_result = request.env.cr.fetchall()
            po_ids = []
            for po_value in po_result:
                po_ids.append(po_value[0])
            datas = {}
            datas['key'] = value[0]
            purchase_orders = request.env['purchase.order'].sudo().search([('id', 'in', po_ids)])
            datas['count'] = len(purchase_orders)
            datas['orders'] = purchase_orders
            if(len(purchase_orders) > 0):
                date_diff = purchase_orders[0].expected_delivery_date - date.today()
                days = date_diff.days
                if days < 0:
                    days = -(days)
                datas['days'] = days
                datas['vendor_name'] = purchase_orders[0].partner_id.name
            else:
                datas['days'] = 0
                datas['vendor_name'] = ''
            po_datas.append(datas)
        values['status'] = 'Future'
        values['po_datas'] = po_datas
        return request.render("skit_website_my_po.po_notification_template", values)

    @http.route(['/po/reminder'], type='json', auth="public",
                methods=['POST'], website=True)
    def purchase_order_reminder(self, **kw):
        """ Display Remainder popup
            @ return: popup
        """
        late_values = self.reminder("Late")
        today_values = self.reminder("Today")
        future_values = self.reminder("Future")
        values = {'late_values': late_values,
                  'today_values': today_values,
                  'future_values': future_values}
        count = 0
        count = count + int(late_values['count'])+ int(today_values['count'])+ int(future_values['count'])
        if count > 0:
            return request.env['ir.ui.view'].render_template(
                    "skit_website_my_po.po_reminder_popup",values)
        else:
            return 'no_record'

    def reminder(self, status):
        " Get respective PO details"
        values = {}
        partner = request.env.user.partner_id
        if status == 'Late':
            query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                    on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                    and ((po.expected_delivery_date::DATE - now()::DATE) < 0) and po.partner_id = %s
                    group by pol.order_id """
        if status == 'Today':
            query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                    on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                    and ((po.expected_delivery_date::DATE - now()::DATE) = 0) and po.partner_id = %s
                    group by pol.order_id """
        if status == 'Future':
            query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                    on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                    and ((po.expected_delivery_date::DATE - now()::DATE) > 0) and po.partner_id = %s
                    group by pol.order_id """

        request.env.cr.execute(query, (partner.id,))
        result = request.env.cr.fetchall()
        po_ids = []
        for value in result:
            po_ids.append(value[0])
        purchase_orders = request.env['purchase.order'].sudo().search([('id', 'in', po_ids)])
        values['count'] = len(purchase_orders)
        values['orders'] = purchase_orders
        if(len(purchase_orders) > 0):
            date_diff = purchase_orders[0].expected_delivery_date - date.today()
            days = date_diff.days
            if days < 0:
                days = -(days)
            values['days'] = days
            values['vendor_name'] = purchase_orders[0].partner_id.name
        values['status'] = status
        return values
