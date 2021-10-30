# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home
import base64


class CustomerPortalDocument(Home):

#     @http.route('/document_page', type='http', website=True,
#                 sitemap=False)
#     def document_page(self, **kw):
#         attachment = request.env['ir.attachment'].sudo().search([('id', '=', 951)])
#         downloadable_docs = self._get_document_downloadable_list_portal()
#         required_docs = self._get_document_required_list_portal()
#         values = {'downloadable_docs': downloadable_docs,
#                   'attachment': attachment,
#                   'required_docs': required_docs
#                   }
#         return request.render('skit_customer_portal.document_template', values)

    @http.route('/send_message/popup', type='json',
                methods=['POST'], website=True)
    def show_send_message_popup(self, **kw):
        values = {}
        return request.env['ir.ui.view'].render_template(
            'skit_customer_portal.send_message_popup', values)

    @http.route('/required_document/save/action', type='json',
                methods=['POST'], website=True)
    def save_required_document(self, **post):
        for file_details in post.get('file_details'):
            if(file_details):
                required_document = self.create_required_doc(file_details)
                document_submission_line = self.create_doc_submission_line(required_document.id)
            return document_submission_line

    def create_required_doc(self, file):
        property_required_document = request.env['property.sale.required.document']
        file_content = file['file_content']
        file_content = file_content.split(',')[1]
        required_document = property_required_document.sudo().create({
            'active': True,
            'name': file['file_name'],
            'preview_file': file_content
        })
        # attachment_id = request.env['ir.attachment'].sudo().search([], order='id desc', limit=1)
        # required_document.message_post(attachment_ids=[attachment_id.id], body="test")
        return required_document

    def create_doc_submission_line(self, document_id):
        property_document_submission_line = request.env['property.document.submission.line']
        values = {
            'document_id': document_id
        }
        document_submission_line = property_document_submission_line.sudo().create(values)
        return document_submission_line

    @http.route('/create_downloadable_doc', type='json',
                methods=['POST'], website=True)
    def downloadable_doc(self, **post):
        for file_details in post.get('file_details'):
            downloadable_doc = self.create_downloadable_doc(file_details)
            document_submission_line = self.create_doc_submission_line(downloadable_doc.id)
            return document_submission_line

    def create_downloadable_doc(self, file):
        property_downloadable_document = request.env['property.sale.downloadable.document']
        file_content = file['file_content']
        file_content = file_content.split(',')[1]
        downloadable_doc = property_downloadable_document.sudo().create({
            'active': True,
            'name': file['file_name'],
            'preview_file': file_content
        })
        return downloadable_doc

#     def _get_document_downloadable_list_portal(self):
#         property_downloadable_doc = request.env['property.sale.downloadable.document']
#         downloadable_docs = property_downloadable_doc.sudo().search([('active', '=', True)])
#         downloadable_doc_list = list()
#         for doc in downloadable_docs:
#             downloadable_doc_list.append({
#                 'id': doc.id,
#                 'name': doc.name,
#                 'description': doc.description,
#                 'sequence': doc.sequence,
#                 'attachment_file': doc.attachment_file
#             })
#         return downloadable_doc_list

    def _get_document_required_list_portal(self):
        property_required_document = request.env['property.sale.required.document']
        required_documents = property_required_document.sudo().search([('active', '=', True)])
        required_document_list = list()
        for doc in required_documents:
            required_document_list.append({
                'id': doc.id,
                'name': doc.name,
                'description': doc.description,
                'sequence': doc.sequence,
                'attachment_file': doc.preview_file,
                'note': doc.note
            })
        return required_document_list

    @http.route('/create_downloadable_doc', type='json',
                methods=['POST'], website=True)
    def download_doc(self, **post):
        for file_details in post.get('file_details'):
            attachment = self.create_downloadable_doc(file_details)
            property_document_submission_line = self.create_doc_submission_line(attachment.id)
            return property_document_submission_line

    @http.route('/customer_profile_page', type='http', website=True,
                sitemap=False)
    def customer_profile_page(self, **kw):
        current_partner = request.env.user.partner_id
        countries = request.env['res.country'].search([])
        states = request.env['res.country.state'].search([])
        value = {'current_partner': current_partner, 'countries': countries, 'states': states}
        return request.render('skit_customer_portal.customer_profile_template', value)

    @http.route('/customer/form/update', type='http', auth="public", website=True)
    def customer_profile_update(self, **post):
        current_partner = request.env.user.partner_id
        if post:
            if post.get('image_1920', False):
                image = post.get('image_1920').read()
                profile_image = base64.b64encode(image)
                post['image_1920'] = profile_image
            if post.get('state_id'):
                state_id = int(post.get('state_id'))
                post['state_id'] = state_id
            else:
                # post.pop('state_id')
                post['state_id'] = None
            if post.get('country_id'):
                country_id = int(post.get('country_id'))
                post['country_id'] = country_id
            else:
                post['country_id'] = None
                # post.pop('country_id')
            current_partner.sudo().write(post)
            value = {'current_partner': current_partner}
            return request.render('skit_customer_portal.customer_update_success_template', value)
