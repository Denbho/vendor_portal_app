# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AdminVendorRFQ(models.Model):
    _inherit = 'admin.vendor.rfq'

    def _compute_access_url(self):
        super(AdminVendorRFQ, self)._compute_access_url()
        for rfq_mail in self:
            rfq_mail.access_url = '/my/rfq/%s' % rfq_mail.id


class AdminRequestForQuotation(models.Model):
    _inherit = 'admin.request.for.quotation'

    def _compute_access_url(self):
        super(AdminRequestForQuotation, self)._compute_access_url()
        for rfq_mail in self:
            rfq_mail.access_url = '/my/rfq/%s' % rfq_mail.id


class AdminRequestForInformationLine(models.Model):
    _name = 'admin.request.for.information.line'
    _inherit = ['admin.request.for.information.line', 'portal.mixin']

    def _compute_access_url(self):
        super(AdminRequestForInformationLine, self)._compute_access_url()
        for rfi in self:
            rfi.access_url = '/my/rfi/%s' % rfi.id


class AdminRequestForProposalsLine(models.Model):
    _name = 'admin.request.for.proposal.line'
    _inherit = ['admin.request.for.proposal.line', 'portal.mixin']

    def _compute_access_url(self):
        super(AdminRequestForProposalsLine, self)._compute_access_url()
        for rfp in self:
            rfp.access_url = '/my/rfp/%s' % rfp.id


class AdminInvoicePayment(models.Model):
    _name = 'admin.invoice.payment'
    _inherit = ['admin.invoice.payment', 'portal.mixin']

    def _compute_access_url(self):
        super(AdminInvoicePayment, self)._compute_access_url()
        for payment in self:
            payment.access_url = '/my/payment/%s' % payment.id


class PurchaseBid(models.Model):
    _name = "purchase.bid.vendor"
    _inherit = ["purchase.bid.vendor", "portal.mixin"]

    def _compute_access_url(self):
        super(PurchaseBid, self)._compute_access_url()
        for bid in self:
            bid.access_url = '/my/bid/%s' % bid.id

    # Inherited this filed to store values in db
    scope_of_work = fields.Char(related='bid_id.scope_of_work', store=True)
    bid_opening_date = fields.Datetime(related='bid_id.bid_opening_date',
                                       store=True)
    bid_closing_date = fields.Datetime(related='bid_id.bid_closing_date',
                                       store=True)


class AdminRequestForProposalLineProductPortal(models.Model):
    _inherit = 'admin.request.for.proposal.line.product'

    product_name = fields.Char(string="Material/Service Name", track_visibility="always", required=False)


class AdminRequestForInformation(models.Model):
    _inherit = 'admin.request.for.information'


    def send_rfi_email(self):
        subtype_id = self.env['mail.message.subtype'].sudo().search([('default','=',True)], limit=1)
        for r in self.vendor_ids:
            res = self.env['admin.request.for.information.line'].sudo().create(
                {
                    'partner_id': r.id,
                    'rfi_id': self.id
                }
            )
            href_link = f"<div style='margin: 16px 0px 16px 0px;'><a href='/my/rfi/$res_id'"\
                        "style='background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;'>"\
                               " View Request for Information"\
                    "</a>"\
                "</div><span></span><br><br>"
            href_link = href_link.replace("$res_id", f"{res.id}")
            body = f"<p>Dear <b>{r.name}</b></p><br/> {href_link}<br/> {self.body_html}"
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


class AdminRequestForProposals(models.Model):
    _inherit = 'admin.request.for.proposals'


    def send_rfp_email(self):
        subtype_id = self.env['mail.message.subtype'].sudo().search([('default','=',True)], limit=1)
        for r in self.vendor_ids:
            res = self.env['admin.request.for.proposal.line'].sudo().create(
                {
                    'partner_id': r.id,
                    'rfp_id': self.id
                }
            )
            href_link = f"<div style='margin: 16px 0px 16px 0px;'><a href='/my/rfp/$res_id'"\
                        "style='background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;'>"\
                               " View Request for Proposal"\
                    "</a>"\
                "</div><span></span><br><br>"
            href_link = href_link.replace("$res_id", f"{res.id}")
            body = f"<p>Dear <b>{r.name}</b></p><br/> {href_link}<br/> {self.body_html}"
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


class AdminEmailNotif(models.Model):
    _inherit = 'admin.email.notif'

    def get_notif_body(self, type):
        # Share url
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        mail_body = ""
        if type == "accreditation_result":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Congratulations '+self.partner_id.name+'!</b><br/><br/>\
                            You have successfully qualified as an accredited supplier of '+self.env.company.name+'.<br/>\
                            Please expect to receive and accept purchase orders from us.<br/><br/>\
                            In the meantime, please explore the features of the Vendor Hub with the following  instructional videos and manuals:<br/>\
                            <span style="margin-left: 15px;">• Navigating Vendor Hub</span><br/>\
                            <span style="margin-left: 15px;">• Updating your profile</span><br/>\
                            <span style="margin-left: 15px;">• Monitoring purchase orders and deliveries</span><br/>\
                            <span style="margin-left: 15px;">• Uploading sales invoices, delivery receipts and official receipts</span><br/>\
                            <span style="margin-left: 15px;">• Monitoring billing payment status</span><br/><br/>\
                            We also conduct online training programs. We will inform you of the next schedule so you can attend.\
                            If you have any queries, you may contact us at <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a>.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "regular_evaluation_result":
            evaluation_date = self.evaluation_date and str(self.evaluation_date) or ""
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            Please see the result of your regular evaluation below:  <br/><br/>\
                            Evaluation Date: '+ evaluation_date +'<br/>\
                            Evaluation Number: '+ self.name +'<br/>\
                            Type of Evaluation: '+ self.type_of_evaluation +'<br/>\
                            Technical Evaluation Score: '+ str(self.technical_valuation_score) +'<br/>\
                            Commercial Evaluation Score: '+ str(self.commercial_valuation_score) +'<br/>\
                            Overall Score: '+ str(self.overall_score) +'<br/>\
                            Link: <a href="'+ base_url+'">'+base_url +'</a><br/><br/><br/>\
                            Regards,<br/>'+ self.env.company.name +'</p></div>'
        elif type == "accreditation_request":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            '+self.env.company.name+' is pleased to invite you to be an accredited supplier of the Company. \
                            You may proceed with the accreditation process through the Vendor Hub. \
                            Kindly submit the following requirements.<br/><br/>'
            for docs_line in self.required_document_accreditation_requirement_ids:
                mail_body += '<span style="margin-left: 15px;">• '+docs_line.name+'</span><br/>'
            mail_body += '<br/>Please click the link below to submit the accreditation requirements.<br/><br/>\
                            <div style="margin: 16px 0px 16px 0px;"><a href="/accreditation" style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;">\
                            View Accreditation Request </a></div><span></span><br/><br/>\
                            If you encounter any issue during the process, you may contact us at \
                            <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a>.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "re_accreditation_request":
            default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', True)], limit=1)
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.name+',</b><br/><br/>\
                            Our records show that your accreditation has already expired as of today '+self.end_date.strftime("%B %d, %Y")+'. \
                            Kindly submit the following requirements.<br/><br/>'
            for line in default_template_data.document_accreditation_requirement_ids:
                mail_body += '<span style="margin-left: 15px;">• '+line.name+'</span><br/>'
            mail_body += '<br/>Please click the link below to complete your re-accreditation requirements.<br/><br/>[link]<br/><br/>\
                            If you encounter any issue on the re-accreditation, you may contact us at \
                            <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a>.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "accreditation_submitted":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            Thank you for completing the accreditation requirements through the Vendor Hub!<br/>\
                            We will review and validate your submission and let you know should there be additional requirements. <br/>\
                            We look forward to developing a mutually beneficial relationship with you!<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_evaluation":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.evaluator_id.name+',</b><br/><br/>\
                            You are selected as the evaluator for vendor '+ self.vendor_bid_id.partner_id.name +' \
                            on bid reference '+ self.bid_id.name +'.Please click the link below to evaluate the vendor.\
                            <br/><br/><a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "vendor_evaluation":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.evaluator_id.name+',</b><br/><br/>\
                            You are selected as the evaluator for vendor '+ self.partner_evaluation_id.partner_id.name +' \
                            on accreditation number '+ self.partner_evaluation_id.name +'.Please click the link below to evaluate the vendor.\
                            <br/><br/><a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "regular_evaluation":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.evaluator_id.name+',</b><br/><br/>\
                            You are selected as the evaluator for vendor '+ self.partner_evaluation_id.partner_id.name +' \
                            on evaluation number '+ self.partner_evaluation_id.name +'. Please click the link below to evaluate the vendor.\
                            <br/><br/><a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_cancelation":
            cancel_description = self.bid_id.cancel_description or ' '
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            We would like to inform you that the bidding with reference <b>'+ self.bid_id.name +'</b> has been canceled. \
                            <br/><br/>Reason: '+ self.bid_id.cancel_reason_id.name +' <br/> \
                            Description: '+ cancel_description +' <br/><br/> \
                            Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_halted":
            halt_description = self.halt_description or ' '
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            We would like to inform you that the bidding with reference <b>'+ self.bid_id.name +'</b> has been halted. \
                            <br/><br/>Reason: '+ self.halt_reason_id.name +' <br/> \
                            Description: '+ halt_description +' <br/><br/> \
                            Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_resumed":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            We would like to inform you that the bidding with reference <b>'+ self.bid_id.name +'</b> has been resumed. \
                            <br/><br/> Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "rfq_cancelation":
            cancel_description = self.rfq_id.cancel_description or ' '
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            We would like to inform you that the request for quotation with reference <b>'+ self.rfq_id.name +'</b> has been canceled. \
                            <br/><br/>Reason: '+ self.rfq_id.cancel_reason_id.name +' <br/> \
                            Description: '+ cancel_description +' <br/><br/> \
                            Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "rfp_cancelation":
            cancel_description = self.rfp_id.cancel_description or ' '
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            We would like to inform you that the request for proposal with reference <b>'+ self.rfp_id.name +'</b> has been canceled. \
                            <br/><br/>Reason: '+ self.rfp_id.cancel_reason_id.name +' <br/> \
                            Description: '+ cancel_description +' <br/><br/> \
                            Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "rfi_cancelation":
            cancel_description = self.rfi_id.cancel_description or ' '
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            We would like to inform you that the request for information with reference <b>'+ self.rfi_id.name +'</b> has been canceled. \
                            <br/><br/>Reason: '+ self.rfi_id.cancel_reason_id.name +' <br/> \
                            Description: '+ cancel_description +' <br/><br/> \
                            Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_winner_unaccredited":
            start_date = self.bid_id.start_date and self.bid_id.start_date.strftime('%m/%d/%Y') or ''
            end_date = self.bid_id.end_date and self.bid_id.end_date.strftime('%m/%d/%Y') or ''
            project_location = self.project_location or ''
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            Congratulations! You have been awarded below stated Work Package:<br/><br/>\
                            Bid Number: '+self.bid_id.name+'<br/>\
                            Description of Work: '+self.scope_of_work+'<br/>\
                            Project: '+self.project_name+'<br/>\
                            Location: '+project_location+'<br/>\
                            Contract Price: Php '+str(self.negotiated_amount)+'<br/>\
                            Contract Duration: '+start_date+' to '+end_date+'<br/><br/>\
                            Before we proceed with the contract, please complete your accreditation requirements.<br/><br/>\
                            If you have any issues during accreditation, you may contact us \
                            <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_not_winner":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            Thank you so much for participating in the bidding for '+ self.scope_of_work +' \
                            at <b>'+ self.project_name +'</b> with reference <b>'+ self.bid_id.name +'</b>. We appreciate your \
                            participation and we hope that you will continue to participate in our upcoming events.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        return mail_body
