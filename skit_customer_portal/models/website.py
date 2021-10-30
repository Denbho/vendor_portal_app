# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    enable_privacy_policy = fields.Boolean('Enable Privacy Policy')
    privacy_policy_title = fields.Char('Title')
    privacy_policy_body = fields.Html('Body')
    privacy_policy_info = fields.Text('Privacy Policy Info')
    body_bg_color = fields.Char('Body Background Color')
    body_bg_image = fields.Binary('Login Background Image')
    login_panel_bg_color = fields.Char('Login Panel BG color')
    terms_and_condition_title = fields.Char('Title')
    terms_and_condition_body = fields.Html('Body')
    
    def get_po_status(self):
        partner = self.env.user.partner_id
        late_count = 0
        today_count = 0
        future_count = 0
        today_query = """ select count(*) from purchase_order where id in (select (pol.order_id) from purchase_order po inner join purchase_order_line pol 
                on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                and ((po.expected_delivery_date::DATE - now()::DATE) = 0) and po.partner_id = %s
                group by pol.order_id) """
        self.env.cr.execute(today_query, (partner.id,))
        today_result = self.env.cr.fetchall()
        for value in today_result:
            today_count = value[0]
        late_query = """ select count(*) from purchase_order where id in (select (pol.order_id) from purchase_order po inner join purchase_order_line pol 
                on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                and ((po.expected_delivery_date::DATE - now()::DATE) < 0) and po.partner_id = %s
                group by pol.order_id) """
        self.env.cr.execute(late_query, (partner.id,))
        late_result = self.env.cr.fetchall()
        for value in late_result:
            late_count = value[0]
        future_query = """ select count(*) from purchase_order where id in (select (pol.order_id) from purchase_order po inner join purchase_order_line pol 
                on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                and ((po.expected_delivery_date::DATE - now()::DATE) > 0) and po.partner_id = %s
                group by pol.order_id) """
        self.env.cr.execute(future_query, (partner.id,))
        future_result = self.env.cr.fetchall()
        for value in future_result:
            future_count = value[0]
        total_count = late_count + today_count + future_count
        return {'late_count': late_count,
                'today_count': today_count,
                'future_count': future_count,
                'total_count': total_count}
