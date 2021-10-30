# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError


class AdminRequestForInformationLine(models.Model):
    _name = 'admin.request.for.information.line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'admin.email.notif']
    _description = 'Request for product information'
    _rec_name = 'partner_id'

    rfi_id = fields.Many2one('admin.request.for.information', string="RFI", ondelete="cascade")
    notes = fields.Html(string="Notes")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    state = fields.Selection([
        ('waiting_for_acceptance', 'Waiting for Acceptance'),
        ('accepted', 'Accepted'),
        ('submitted', 'Submitted'),
        ('done', 'Done'),
        ('declined', 'Declined'),
        ('canceled', 'Cancelled'),
        ('no_response', 'No Response')],
        string='Status', readonly=True, copy=False, default='waiting_for_acceptance')
    declined_reason_id = fields.Many2one('admin.declined.reason', string='Declined Reason')
    declined_note = fields.Text(string='Declined Note')
    company_id = fields.Many2one(related='rfi_id.company_id', store=True)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    def btn_accept(self):
          if self.rfi_id and self.rfi_id.close_date < fields.Date.today():
              raise ValidationError('RFI has already lapsed the closing date, please coordinate with the Purchasing Team.')
          self.state = 'accepted'

    def btn_submit(self):
      if self.rfi_id and self.rfi_id.close_date < fields.Date.today():
          raise ValidationError('RFI has already lapsed the closing date, please coordinate with the Purchasing Team.')
      self.state = 'submitted'


class AdminRequestForInformation(models.Model):
    _name = 'admin.request.for.information'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'document.default.approval']
    _description = 'Request for product information'
    _order = 'create_date desc'

    @api.model
    def default_get(self, default_fields):
        res = super(AdminRequestForInformation, self).default_get(default_fields)
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
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                        default=lambda self: self.env.company, track_visibility="always",
                        states={'draft': [('readonly', False)]})
    company_code = fields.Char(string='Company Code', readonly=True, track_visibility="always",
                        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', string='Purchasing Officer', index=True, tracking=True, required=True,
                              default=lambda self: self.env.user, track_visibility="always", readonly=True,
                              states={'draft': [('readonly', False)]})
    create_date = fields.Datetime(string="Created Date", required=True, readonly=True, copy=False,
                                  default=fields.Datetime.now)
    due_date = fields.Date(string="Due Date", copy=True, readonly=True,
                           states={'draft': [('readonly', False)]}, track_visibility="always",)
    open_date = fields.Date(string="Opening Date", copy=False, readonly=True,
                             states={'draft': [('readonly', False)]}, track_visibility="always",)
    close_date = fields.Date(string="Closing Date", copy=True, readonly=True,
                             states={'draft': [('readonly', False)]}, track_visibility="always",)
    vendor_ids = fields.Many2many('res.partner', 'purchase_vendor_rfi_rel', string="Vendors", required=True,
                                  copy=True, states={'draft': [('readonly', False)]}, readonly=True,
                                  help="Admin/Managers can add the vendors and invite for this RFI")
    attachment_ids = fields.Many2many('ir.attachment', 'rfi_mail_rel', string="Email Attachments", readonly=True,
                                      states={'draft': [('readonly', False)]}, copy=False)
    subject = fields.Char(string="Subject", required=True, track_visibility="always", readonly=True,
                          states={'draft': [('readonly', False)]})
    body_html = fields.Html(string="Email Body", required=True, tracking=True, track_visibility="always", readonly=True,
                            states={'draft': [('readonly', False)]})
    sent_rfi = fields.Boolean(string="RFI Sent", copy=False)
    rtd_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reset to Draft Reason', track_visibility='always', copy=False)
    rtd_description = fields.Text(string='Reset to Draft Reasons Description', track_visibility='always', copy=False)
    cancel_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Cancelation Reason', track_visibility='always', copy=False)
    cancel_description = fields.Text(string='Cancelation Description', track_visibility='always', copy=False)

    def send_email_to_vendors(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        rfi_mails = self.env['admin.request.for.information.line'].sudo().search([('rfi_id','=',self.ids[0]),('state','not in',['canceled','declined','no_response'])])
        partner_ids = []
        for line in rfi_mails:
            partner_ids.append(line.partner_id.id)
        ctx = dict(self.env.context or {})
        ctx.update({
            'custom_layout': "mail.mail_notification_paynow",
            'default_model': 'admin.request.for.information',
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
            rfi_mails = self.env['admin.request.for.information.line'].sudo().search([('rfi_id','=',self.ids[0]),('partner_id','in',partner_ids)])
            for line in rfi_mails:
                kwargs['partner_ids'] = [line.partner_id.id]
                line.message_post(**kwargs)
            kwargs['partner_ids'] = []
        return super(AdminRequestForInformation, self).message_post(**kwargs)

    def log_assigned_and_removed_vendors(self, vals, action_type):
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
        if action_type == 'create':
            return body
        else:
            self.message_post(body=body, subject="Assigned Vendors Update")

    def write(self, vals):
        if 'vendor_ids' in vals and vals.get('vendor_ids'):
            self.log_assigned_and_removed_vendors(vals, 'write')
        return super(AdminRequestForInformation, self).write(vals)

    def unlink(self):
        for rfi_detail in self:
            if not rfi_detail.state == 'canceled':
                raise ValidationError('In order to delete request for information, you must cancel it first.')
        return super(AdminRequestForInformation, self).unlink()

    def set_to_done(self):
        rfi_lines = self.env['admin.request.for.information.line'].sudo().search([('rfi_id', '=', self.id)])
        for line in rfi_lines:
            if line.state not in ['declined', 'no_response']:
                line.state = 'done'
        self.state = 'done'

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
        body = ''
        if 'vendor_ids' in vals and vals.get('vendor_ids'):
            body = self.log_assigned_and_removed_vendors(vals, 'create')
        res = super(AdminRequestForInformation,self).create(vals)
        res.onchange_company_code()
        if 'vendor_ids' in vals and vals.get('vendor_ids'):
            res.message_post(body=body, subject="Assigned Vendors Update")
        return res

    def submit_request(self):
        return self.write({
            'name': self.env['ir.sequence'].get('vendor.request.for.information'),
            'state': 'submitted',
            'submitted_by': self._uid,
            'submitted_date': datetime.now()
        })

    def send_rfi_email(self):
        subtype_id = self.env['mail.message.subtype'].sudo().search([('default','=',True)], limit=1)
        for r in self.vendor_ids:
            res = self.env['admin.request.for.information.line'].sudo().create(
                {
                    'partner_id': r.id,
                    'rfi_id': self.id
                }
            )
            body = f"<p>Dear <b>{r.name}</b></p><br/> {self.body_html}"
            mail_values = {
                'subject': self.subject,
                'email_to': r.email,
                'body_html': body,
                'model': 'admin.request.for.information.line',
                'res_id': res.id,
                'attachment_ids': self.attachment_ids.ids,
            }
            res = res.with_context(default_message_type='comment', default_recipient_ids=[r.id],
                                    default_notification=True, default_partner_ids=[r.id], default_body=body)
            if subtype_id:
                res = res.with_context(default_subtype_id=subtype_id.id)
            res.env['mail.mail'].create(mail_values).send()
        self.write({'sent_rfi': True})
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Congratulation! '
                           f'Your RFI has been successfully sent to vendors',
                'type': 'rainbow_man',
            }
        }

    @api.model
    def _opening_date_send_invitation_email(self):
        records = self.search([('state', '=', 'approved'),('sent_rfi', '=', False),('open_date', '<=', fields.Date.today())])
        for rec in records:
            rec.send_rfi_email()

    @api.model
    def _update_no_response_vendor(self):
        records = self.sudo().search([('state', '=', 'approved'),('close_date', '<=', fields.Date.today())])
        for rec in records:
            for line in self.env['admin.request.for.information.line'].sudo().search([('rfi_id', '=', rec.id), ('state', '=', 'waiting_for_acceptance')]):
                line.state = 'no_response'
