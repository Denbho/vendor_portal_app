# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import date, datetime, timedelta, time
from odoo.exceptions import ValidationError


class AdminRequestForProposalLineProduct(models.Model):
    _name = 'admin.request.for.proposal.line.product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Proposal"

    rfp_line_id = fields.Many2one('admin.request.for.proposal.line', string="RFP Line", ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Product", track_visibility="always")
    product_name = fields.Char(string="Material/Service Name", track_visibility="always")
    name = fields.Text(string="Description", required=True, track_visibility="always")
    qty = fields.Float(string="Quantity", track_visibility="always")
    unit_name = fields.Char(string="UOM", track_visibility="always")
    price = fields.Float(string="Price", track_visibility="always")
    total = fields.Float(string="Subtotal", compute="_get_total", store=True)
    delivery_lead_time = fields.Float(string="Delivery Lead Time", help="In Days")
    validity_from = fields.Date(string="Valid From", track_visibility="always")
    validity_to = fields.Date(string="Valid To", track_visibility="always")
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')

    @api.depends('qty', 'price')
    def _get_total(self):
        for r in self:
            r.total = r.price * r.qty


class AdminRequestForProposalLine(models.Model):
    _name = 'admin.request.for.proposal.line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'admin.email.notif']
    _description = 'Request for Proposal Line'
    _rec_name = 'partner_id'

    rfp_id = fields.Many2one('admin.request.for.proposals', string="RFP", ondelete="cascade")
    notes = fields.Html(string="Notes", track_visibility="always")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    proposal_line_ids = fields.One2many('admin.request.for.proposal.line.product', 'rfp_line_id')
    total = fields.Float(string="Grand Total", compute="_get_total", store=True)
    payment_terms = fields.Html(string="Payment Terms", track_visibility="always")
    other_term_warranty = fields.Html(string="Other Terms and Warranty", track_visibility="always")
    state = fields.Selection([
                          ('waiting_for_acceptance', 'Waiting for Acceptance'),
                          ('accepted', 'Accepted'),
                          ('submitted', 'Submitted'),
                          ('selected_as_vendor', 'Selected as Vendor'),
                          ('done', 'Done'),
                          ('declined', 'Declined'),
                          ('canceled', 'Cancelled'),
                          ('no_response', 'No Response')], string="Status",
                         default='waiting_for_acceptance', readonly=True, copy=False, track_visibility="always")
    declined_reason_id = fields.Many2one('admin.declined.reason', string='Declined Reason')
    declined_note = fields.Text(string='Declined Note')
    company_id = fields.Many2one(related='rfp_id.company_id', store=True)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    def btn_accept(self):
        if self.rfp_id and self.rfp_id.close_date < fields.Date.today():
            raise ValidationError('RFP has already lapsed the closing date, please coordinate with the Purchasing Team.')
        proposal_line_items = self.env['admin.request.for.proposal.line.product'].sudo().search([('rfp_line_id', '=', self.id)])
        if not proposal_line_items:
            raise ValidationError("Please add a proposal item/s.")
        self.state = 'accepted'

    def btn_submit(self):
      if self.rfp_id and self.rfp_id.close_date < fields.Date.today():
          raise ValidationError('RFP has already lapsed the closing date, please coordinate with the Purchasing Team.')
      self.state = 'submitted'

    def select_as_vendor(self):
        zero_product_price = self.env['admin.request.for.proposal.line.product'].sudo().search([('rfp_line_id', '=', self.id), ('price', '<=', 0)])
        if zero_product_price:
            items = ""
            count = 1
            for item in zero_product_price:
                items += f"\n\t{count}. {item.product_name}"
                count += 1
            raise ValidationError(_(f"The price of the following item/s must be greater than zero: {items}"))
        self.state = 'selected_as_vendor'

    def cancel(self):
        self.state = 'canceled'

    def create_update_pricelist(self):
        not_linked_products = self.env['admin.request.for.proposal.line.product'].sudo().search([('rfp_line_id', '=', self.id), ('product_id', '=', False)])
        if not_linked_products:
            items = ""
            count = 1
            for item in not_linked_products:
                items += f"\n\t{count}. {item.product_name}"
                count += 1
            raise ValidationError(_(f"Please link the following item/s to product: {items}"))
        for line in self.proposal_line_ids:
            vendor_pricelist = []
            create_update_pricelist = True
            if line.validity_from and line.validity_to:
                vendor_pricelist = self.env['product.supplierinfo'].sudo().search([('product_id', '=', line.product_id.id), ('name', '=', self.partner_id.id), ('date_start', '>=', line.validity_from), ('date_end', '<=', line.validity_to), ('price', '=', line.price)])
                between_validity_pricelist = self.env['product.supplierinfo'].sudo().search([('product_id', '=', line.product_id.id), ('name', '=', self.partner_id.id), ('date_start', '<=', line.validity_from), ('date_end', '>=', line.validity_to), ('price', '=', line.price)])
                if between_validity_pricelist:
                    create_update_pricelist = False
            else:
                vendor_pricelist = self.env['product.supplierinfo'].sudo().search([('product_id', '=', line.product_id.id), ('name', '=', self.partner_id.id), ('date_start', '=', False), ('date_end', '=', False)])
            if create_update_pricelist:
                if vendor_pricelist:
                    for ln in vendor_pricelist:
                        ln.write({
                            'date_start': line.validity_from,
                            'date_end': line.validity_to,
                            'product_name': line.product_name,
                            'min_qty': line.qty,
                            'product_uom': line.product_id.uom_po_id.id,
                            'price': line.price,
                            'delay': line.delivery_lead_time,
                        })
                else:
                    self.env['product.supplierinfo'].sudo().create({
                        'product_id': line.product_id.id,
                        'name': self.partner_id.id,
                        'date_start': line.validity_from,
                        'date_end': line.validity_to,
                        'product_name': line.product_name,
                        'min_qty': line.qty,
                        'product_uom': line.product_id.uom_po_id.id,
                        'price': line.price,
                        'delay': line.delivery_lead_time,
                    })

    @api.depends('proposal_line_ids', 'proposal_line_ids.qty', 'proposal_line_ids.price')
    def _get_total(self):
        for r in self:
            r.total = sum(i.total for i in r.proposal_line_ids)


class AdminRequestForProposals(models.Model):
    _name = 'admin.request.for.proposals'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'document.default.approval']
    _description = 'Request for Proposals'
    _order = 'create_date desc'

    @api.model
    def default_get(self, default_fields):
        res = super(AdminRequestForProposals, self).default_get(default_fields)
        body = '<div style="margin:0px;padding: 0px;">' \
               '<p style="padding: 0px; font-size: 13px;">' \
               '--Your Email Body Here.<br><br><span class="fontstyle0">Regards.' \
               '<br>Vistaland Purchasing Team</span> </p></div>'
        res.update({
            'body_html': body
        })
        return res

    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Waiting for Confirmation'),
                              ('confirmed', 'Waiting for Verification'),
                              ('verified', 'Waiting for Approval'),
                              ('approved', 'Approved'),
                              ('done', 'Done'),
                              ('canceled', 'Cancelled')], string="Status",
                             default='draft', readonly=True, copy=False, track_visibility="always")
    name = fields.Char('Request Reference', copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', 'Company',
                        default=lambda self: self.env.company, track_visibility="always",
                        states={'draft': [('readonly', False)]}, readonly=True)
    company_code = fields.Char(string='Company Code', track_visibility="always",
                        states={'draft': [('readonly', False)]}, readonly=True)
    user_id = fields.Many2one('res.users', string='Purchasing Officer', index=True, tracking=True, required=True,
                              default=lambda self: self.env.user, track_visibility="always", readonly=True,
                              states={'draft': [('readonly', False)]})
    create_date = fields.Datetime(string="Created Date", required=True, readonly=True, copy=False,
                                  default=fields.Datetime.now)
    est_del_date = fields.Date(string="Required Delivery Date", copy=True, readonly=True,
                               states={'draft': [('readonly', False)]},
                               help="Admin/Managers can set their estimated delivery date for this rfq, "
                                    "this information will be sent to the vendors.")
    due_date = fields.Date(string="Due Date", copy=True, readonly=True,
                           states={'draft': [('readonly', False)]})
    open_date = fields.Date(string="Opening Date", copy=False, readonly=True,
                             states={'draft': [('readonly', False)]})
    close_date = fields.Date(string="Closing Date", copy=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    vendor_ids = fields.Many2many('res.partner', 'purchase_vendor_rfp_rel', string="Vendors", required=True,
                                  copy=True, states={'draft': [('readonly', False)]}, readonly=True,
                                  help="Admin/Managers can add the vendors and invite for this RFP.")
    attachment_ids = fields.Many2many('ir.attachment', 'rfp_mail_rel', string="Email Attachments", readonly=True,
                                      states={'draft': [('readonly', False)]}, copy=False)
    subject = fields.Char(string="Subject", required=True, track_visibility="always", readonly=True,
                          states={'draft': [('readonly', False)]})
    body_html = fields.Html(string="Email Body", required=True, tracking=True, track_visibility="always", readonly=True,
                            states={'draft': [('readonly', False)]})
    sent_rfp = fields.Boolean(string="RFP Sent", copy=False)
    pr_related_ids = fields.Many2many('purchase.requisition.material.details', 'pr_rfp_rel', string='PR Related',
                                      readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    rtd_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reset to Draft Reason', track_visibility='always', copy=False)
    rtd_description = fields.Text(string='Reset to Draft Reasons Description', track_visibility='always', copy=False)
    cancel_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Cancelation Reason', track_visibility='always', copy=False)
    cancel_description = fields.Text(string='Cancelation Description', track_visibility='always', copy=False)

    def send_email_to_vendors(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        rfp_mails = self.env['admin.request.for.proposal.line'].sudo().search([('rfp_id','=',self.ids[0]),('state','not in',['canceled','declined','no_response'])])
        partner_ids = []
        for line in rfp_mails:
            partner_ids.append(line.partner_id.id)
        ctx = dict(self.env.context or {})
        ctx.update({
            'custom_layout': "mail.mail_notification_paynow",
            'default_model': 'admin.request.for.proposals',
            'default_name': 'Send Email to Vendors',
            'default_composition_mode': 'comment',
            'default_partner_ids': partner_ids,
            'default_res_id': self.ids[0],
            'force_email': True,
            'send_email_to_vendors': True,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('send_email_to_vendors'):
            partner_ids = kwargs['partner_ids']
            rfp_mails = self.env['admin.request.for.proposal.line'].sudo().search([('rfp_id','=',self.ids[0]),('partner_id','in',partner_ids)])
            for line in rfp_mails:
                kwargs['partner_ids'] = [line.partner_id.id]
                line.message_post(**kwargs)
            kwargs['partner_ids'] = []
        return super(AdminRequestForProposals, self).message_post(**kwargs)

    def log_assigned_and_removed_vendors(self, vals):
          current_vendor = self.vendor_ids.ids
          added_vendor = list()
          removed_vendor = list()
          for d in vals.get('vendor_ids')[0][2]:
              if not d in current_vendor:
                  added_vendor.append(d)
          for d in current_vendor:
              if not d in vals.get('vendor_ids')[0][2]:
                  removed_vendor.append(d)
          body = ''
          if added_vendor:
              body += '<p> <strong><em>The following vendors has been added: </em></strong></p>'
              count = 0
              for r in self.env['res.partner'].browse(added_vendor):
                  count += 1
                  body += f"<ul>{count}. {r.name}</ul>"
              body += '<br/>'
          if removed_vendor:
              body += '<p><em>The following assigned vendors has been removed: </em></p>'
              count = 0
              for r in self.env['res.partner'].browse(removed_vendor):
                  count += 1
                  body += f"<ul>{count}. {r.name}</ul>"
              body += '<br/>'
          self.message_post(body=body, subject="Assigned Vendors Update")

    def write(self, vals):
      if 'vendor_ids' in vals and vals.get('vendor_ids'):
          self.log_assigned_and_removed_vendors(vals)
      return super(AdminRequestForProposals, self).write(vals)

    def unlink(self):
        for rfp_detail in self:
            if not rfp_detail.state == 'canceled':
                raise ValidationError('In order to delete request for proposal, you must cancel it first.')
        return super(AdminRequestForProposals, self).unlink()

    @api.constrains('open_date', 'close_date', 'due_date')
    def _date_validation(self):
        for rec in self:
            if rec.open_date:
                if rec.open_date < date.today():
                    raise ValidationError("Opening date shoud not be less than date today.")
                elif rec.close_date and rec.open_date > rec.close_date:
                    raise ValidationError("Closing date shoud not be less than opening date.")
                elif rec.close_date and rec.open_date == rec.close_date:
                    raise ValidationError("Closing date should not be equal to opening date.")
                elif rec.due_date and rec.due_date < rec.open_date:
                    raise ValidationError("Due date shoud not be earlier than opening date.")
                elif rec.est_del_date and rec.est_del_date < rec.open_date:
                    raise ValidationError("Required delivery date should not be earlier than opening date.")
            if rec.due_date and rec.close_date and rec.due_date > rec.close_date:
                raise ValidationError("Due date should be on or before closing date.")

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.model
    def create(self, vals):
        res = super(AdminRequestForProposals,self).create(vals)
        res.onchange_company_code()
        return res

    def submit_request(self):
        return self.write({
            'name': self.env['ir.sequence'].get('vendor.request.for.proposal'),
            'state': 'submitted',
            'submitted_by': self._uid,
            'submitted_date': datetime.now()
        })

    def send_rfp_email(self):
        subtype_id = self.env['mail.message.subtype'].sudo().search([('default','=',True)], limit=1)
        for r in self.vendor_ids:
            res = self.env['admin.request.for.proposal.line'].sudo().create(
                {
                    'partner_id': r.id,
                    'rfp_id': self.id
                }
            )
            body = f"<p>Dear <b>{r.name}</b></p><br/> {self.body_html}"
            mail_values = {
                'subject': self.subject,
                'email_to': r.email,
                'body_html': body,
                'model': 'admin.request.for.proposal.line',
                'res_id': res.id,
                'attachment_ids': self.attachment_ids.ids,
            }
            res = res.with_context(default_message_type='comment', default_recipient_ids=[r.id],
                                    default_notification=True, default_partner_ids=[r.id], default_body=body)
            if subtype_id:
                res = res.with_context(default_subtype_id=subtype_id.id)
            res.env['mail.mail'].create(mail_values).send()
        self.write({'sent_rfp': True})
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Congratulation! '
                           f'Your RFP has been successfully sent to vendors',
                'type': 'rainbow_man',
            }
        }

    def set_to_done(self):
        selected_vendor = False
        rfp_lines = self.env['admin.request.for.proposal.line'].sudo().search([('rfp_id', '=', self.id), ('state', 'not in', ['declined', 'no_response'])])
        for line in rfp_lines:
            if line.state == 'selected_as_vendor':
                line.create_update_pricelist()
                selected_vendor = True
            else:
                line.state = 'done'
        if not selected_vendor:
            raise ValidationError("Please select/assign a vendor.")
        self.state = 'done'

    @api.model
    def _opening_date_send_invitation_email(self):
        records = self.search([('state', '=', 'approved'),('sent_rfp', '=', False),('open_date', '<=', fields.Date.today())])
        for rec in records:
            rec.send_rfp_email()

    @api.model
    def _update_no_response_vendor(self):
        records = self.sudo().search([('state', '=', 'approved'),('close_date', '<=', fields.Date.today())])
        for rec in records:
            for line in self.env['admin.request.for.proposal.line'].sudo().search([('rfp_id', '=', rec.id), ('state', '=', 'waiting_for_acceptance')]):
                line.state = 'no_response'
