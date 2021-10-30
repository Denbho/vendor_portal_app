from odoo import fields, models, api
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning

class AdminBidSelectionApproval(models.TransientModel):
    _name = 'admin.bid.selection.approval'
    _description = 'Admin Bid Selection Approval'

    bid_id = fields.Many2one('purchase.bid', string='Bid')
    attachment_ids = fields.Many2many('ir.attachment', 'bid_approval_mail_rel', required=True, string="Email Attachments")

    def btn_approve(self):
        if not self.attachment_ids:
            raise Warning("File attachment is required.")
        self.bid_id.write({
            'bs_approved_by': self._uid,
            'bs_approved_date': datetime.now(),
            'state': 'done',
        })
        for line in self.bid_id.vendor_line:
            if not line.is_kicked and line.state not in ['bidding_cancel','cancel','decline','no_response']:
                line.state = 'done'
                # Send notif to awarded and not awarded bidders.
                if line.id == self.bid_id.vendor_id.id:
                    m_subject = 'Bid Result - Successful Bidder'
                    start_date = line.bid_id.start_date and line.bid_id.start_date.strftime('%m/%d/%Y') or ''
                    end_date = line.bid_id.end_date and line.bid_id.end_date.strftime('%m/%d/%Y') or ''
                    project_location = line.project_location or ''
                    # if line.partner_id.accredited and line.partner_id.end_date > fields.Date.today():
                    mail_body = '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                                    <b>Dear '+line.partner_id.name+',</b><br/><br/>\
                                    Congratulations! You have been awarded below stated Work Package:<br/><br/>\
                                    Bid Number: '+self.bid_id.name+'<br/>\
                                    Description of Work: '+line.scope_of_work+'<br/>\
                                    Project: '+line.project_name+'<br/>\
                                    Location: '+project_location+'<br/>\
                                    Contract Price: Php '+str(line.negotiated_amount)+'<br/>\
                                    Contract Duration: '+start_date+' to '+end_date+'<br/><br/>\
                                    While we prepare the contract of agreement, please refer to the attached \
                                    file for the letter of award and negotiation checklist for your signature.<br/><br/>\
                                    If you have any clarifications, you may contact us \
                                    <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a><br/><br/><br/>\
                                    Regards,<br/>'+self.env.company.name+'</p></div>'
                    mail_values = {
                        'subject': m_subject,
                        'email_to': line.partner_id.email,
                        'body_html': mail_body,
                        'model': 'purchase.bid.vendor',
                        'res_id': line.id,
                        'attachment_ids': self.attachment_ids.ids,
                    }
                    line = line.with_context(default_message_type='comment', default_recipient_ids=[line.partner_id.id],
                                            default_subject=m_subject, default_body_html=mail_body, default_notification=True,
                                            default_partner_ids=[line.partner_id.id], default_body=mail_body)
                    subtype_id = self.env['mail.message.subtype'].sudo().search([('default','=',True)], limit=1)
                    if subtype_id:
                        line = line.with_context(default_subtype_id=subtype_id.id)
                    line.env['mail.mail'].create(mail_values).send()
                else:
                    m_subject = 'Bid Result - Unsuccessful Bidder'
                    line.send_admin_email_notif('bid_not_winner', m_subject, line.partner_id.email, 'purchase.bid.vendor')
        return {'type': 'ir.actions.act_window_close'}
