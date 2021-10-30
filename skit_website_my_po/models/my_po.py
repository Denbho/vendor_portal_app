from odoo import models, fields, api, _
from datetime import date


class MyPurchase(models.Model):

    _inherit = "purchase.order"

    isprint = fields.Boolean("Print", default=False)
    
    
    @api.model
    def send_po_notifications(self):
        purchase_orders = self.env['purchase.order'].search([])
        for purchase_order in purchase_orders:
            late_values = self.po_reminder("Late", purchase_order)
            today_values = self.po_reminder("Today", purchase_order)
            future_values = self.po_reminder("Future", purchase_order)
            count = 0
            count = count + int(late_values['count'])+ int(today_values['count'])+ int(future_values['count'])
            if count > 0:
                template_context = {
                        'late_values': late_values,
                        'today_values': today_values,
                        'future_values': future_values
                }
                template = self.env.ref('skit_website_my_po.mail_template_vendor_po_notifications')
                if template:
                    template.with_context(**template_context).send_mail(purchase_order.id, force_send=True)
    
    def po_reminder(self, status, purchase_order):
        " Get respective PO details"
        values = {}
        partner = purchase_order.partner_id
        if status == 'Late':
            query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                    on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                    and ((po.expected_delivery_date::DATE - now()::DATE) < 0) and po.partner_id = %s and po.id = %s
                    group by pol.order_id """
        if status == 'Today':
            query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                    on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                    and ((po.expected_delivery_date::DATE - now()::DATE) = 0) and po.partner_id = %s and po.id = %s
                    group by pol.order_id """
        if status == 'Future':
            query = """ select pol.order_id from purchase_order po inner join purchase_order_line pol 
                    on po.id = pol.order_id where po.acceptance_status='accepted' and ((pol.product_qty - COALESCE(pol.qty_delivered, cast(0 AS DOUBLE PRECISION))) >0)
                    and ((po.expected_delivery_date::DATE - now()::DATE) > 0) and po.partner_id = %s and po.id = %s
                    group by pol.order_id """

        self.env.cr.execute(query, (partner.id, purchase_order.id))
        result = self.env.cr.fetchall()
        po_ids = []
        for value in result:
            po_ids.append(value[0])
        purchase_orders = self.env['purchase.order'].sudo().search([('id', 'in', po_ids)])
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
    
    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
            else:
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "skit_website_my_po.po_mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
                
        
