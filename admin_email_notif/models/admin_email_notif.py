# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AdminEmailNotif(models.Model):
    _name = 'admin.email.notif'

    def get_notif_body(self, type):
        # Share url
        pure_base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url = pure_base_url+'/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
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
            mail_body += '<br/>Please click the link below to submit the accreditation requirements.<br/><br/>[link]<br/><br/>\
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

    def send_admin_email_notif(self, type, mail_subject, email_to, model):
        mail_body = self.get_notif_body(type)
        mail_values = {
            'subject': mail_subject,
            'email_to': email_to,
            'body_html': mail_body,
            'model': model,
            'res_id': self.id,
        }
        if model != 'purchase.bid.vendor':
            self.message_post(body=mail_body)
        else:
            self = self.with_context(default_message_type='comment', default_recipient_ids=[self.partner_id.id],
                                    default_subject=mail_subject, default_body_html=mail_body, default_notification=True,
                                    default_partner_ids=[self.partner_id.id], default_body=mail_body)
            subtype_id = self.env['mail.message.subtype'].sudo().search([('default','=',True)], limit=1)
            if subtype_id:
                self = self.with_context(default_subtype_id=subtype_id.id)
        return self.env['mail.mail'].create(mail_values).send()
