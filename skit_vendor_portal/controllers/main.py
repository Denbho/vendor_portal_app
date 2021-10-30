# -*- coding: utf-8 -*-
import base64
import json
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
import io
import os
import mimetypes
from ast import literal_eval
from werkzeug.utils import redirect
from datetime import date


class VendorPortal(Website):

    @http.route('/vendor_portal/registration', type="http",
                auth="public", website=True)
    def vendor_registration(self, **kw):
        """ Render Vendor Registration Form """
        industry = request.env['res.partner.industry'].sudo().search([])
        country = request.env['res.country'].sudo().search([])
        ph_country_id = request.env['res.country'].sudo().search([('code', '=', 'PH')], limit=1).id
        states = request.env['res.country.state'].sudo().search([('country_id', '=', int(ph_country_id))])
        barangay = []
        province = []
        cities = []
        product_classifications = request.env['product.classification'].sudo().search([])
        nda_title = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.nda_title')
        nda_body = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.nda_body')
        privacy_policy_title = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.privacy_policy_title')
        privacy_policy_body = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.privacy_policy_body')
        terms_and_condition_title = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.terms_and_condition_title')
        terms_and_condition_body = request.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.terms_and_condition_body')

        values = ({'countries': country,
                   'barangaies': barangay,
                   'states': states,
                   'province': province,
                   'cities': cities,
                   'product_classifications': product_classifications,
                   'industries': industry,
                   'nda_title': nda_title,
                   'nda_body': nda_body,
                   'privacy_policy_title': privacy_policy_title,
                   'privacy_policy_body': privacy_policy_body,
                   'terms_and_condition_title':terms_and_condition_title,
                   'terms_and_condition_body': terms_and_condition_body,
                   })
        return request.render("skit_vendor_portal.vendor_registration_form",
                              values)
        
    @http.route(['/onchange/head_office_address'], type='json', auth="public",
                methods=['POST'], website=True)
    def onChangeHeadAddressField(self, **kw):
        values = {}
        if kw.get('country_id'):
            states = request.env['res.country.state'].sudo().search([('country_id', '=', int(kw.get('country_id')))])
            values['id'] = 'state_id'
            values['name'] = 'state_id'
            values['placeholder'] = 'Region'
            values['class_name'] = 'form-control vinput'
            values['datas'] = states
            values['active_id'] = 0
            values['first_option'] = 'Region..'
        if kw.get('state_id'):
            province = request.env['res.country.province'].sudo().search([('state_id', '=', int(kw.get('state_id')))])
            values['id'] = 'province_id'
            values['name'] = 'province_id'
            values['placeholder'] = 'Province'
            values['class_name'] = 'form-control vinput'
            values['datas'] = province
            values['active_id'] = 0
            values['first_option'] = 'Province..'
        if kw.get('province_id'):
            cities = request.env['res.country.city'].sudo().search([('province_id', '=', int(kw.get('province_id')))])
            values['id'] = 'city_id'
            values['name'] = 'city_id'
            values['placeholder'] = 'City'
            values['class_name'] = 'form-control vinput'
            values['datas'] = cities
            values['active_id'] = 0
            values['first_option'] = 'City..'
        if kw.get('city_id'):
            barangay = request.env['res.barangay'].sudo().search([('city_id', '=', int(kw.get('city_id')))])
            values['id'] = 'barangay_id'
            values['name'] = 'barangay_id'
            values['placeholder'] = 'Barangay'
            values['class_name'] = 'form-control vinput'
            values['datas'] = barangay
            values['active_id'] = 0
            values['first_option'] = 'Barangay..'
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.address_field_template",
                                                         values)

    @http.route(['/onchange/address'], type='json', auth="public",
                methods=['POST'], website=True)
    def onChangeAddressField(self, **kw):
        values = {}
        if kw.get('country_id'):
            states = request.env['res.country.state'].sudo().search([('country_id', '=', int(kw.get('country_id')))])
            values['id'] = 'sstate_id'
            values['name'] = kw.get('name')
            values['placeholder'] = 'Region'
            values['class_name'] = 'form-control sstate_id mt-2'
            values['datas'] = states
            values['active_id'] = 0
            values['first_option'] = ''
        if kw.get('state_id'):
            province = request.env['res.country.province'].sudo().search([('state_id', '=', int(kw.get('state_id')))])
            values['id'] = 'sprovince_id'
            values['name'] = kw.get('name')
            values['placeholder'] = 'Province'
            values['class_name'] = 'form-control sprovince_id mt-2'
            values['datas'] = province
            values['active_id'] = 0
            values['first_option'] = ''
        if kw.get('province_id'):
            cities = request.env['res.country.city'].sudo().search([('province_id', '=', int(kw.get('province_id')))])
            values['id'] = 'scity_id'
            values['name'] = kw.get('name')
            values['placeholder'] = 'City'
            values['class_name'] = 'form-control scity_id mt-2'
            values['datas'] = cities
            values['active_id'] = 0
        if kw.get('city_id'):
            barangay = request.env['res.barangay'].sudo().search([('city_id', '=', int(kw.get('city_id')))])
            values['id'] = 'sbarangay_id'
            values['name'] = kw.get('name')
            values['placeholder'] = 'Barangay'
            values['class_name'] = 'form-control sbarangay_id mt-2'
            values['datas'] = barangay
            values['active_id'] = 0
            values['first_option'] = ''
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.address_field_template",
                                                         values)
        
    @http.route(['/site_address/creation'], type='json', auth="public",
                methods=['POST'], website=True)
    def site_office_creation(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        country = request.env['res.country'].sudo().search([])
        barangay = []
        province = []
        cities = []
        states = []
        country_id = 0
        if kw.get('country_id'):
            country_id = int(kw.get('country_id'))
        else:
            country_id = request.env['res.country'].sudo().search([('code', '=', 'PH')], limit=1).id
        states = request.env['res.country.state'].sudo().search([('country_id', '=', int(country_id))])
        state_id = 0
        if kw.get('state_id'):
            state_id = int(kw.get('state_id'))
            province = request.env['res.country.province'].sudo().search([('state_id', '=', int(state_id))])
        provice_id = 0
        if kw.get('province_id'):
            provice_id = int(kw.get('province_id'))
            cities = request.env['res.country.city'].sudo().search([('province_id', '=', int(provice_id))])
        city_id = 0
        if kw.get('city_id'):
            city_id = int(kw.get('city_id'))
            barangay = request.env['res.barangay'].sudo().search([('city_id', '=', int(city_id))])
        barangay_id = 0
        if kw.get('barangay_id'):
            barangay_id = int(kw.get('barangay_id'))
        values = ({'countries': country,
                   'barangaies': barangay,
                   'states': states,
                   'province': province,
                   'cities': cities,
                   'name': kw.get('s_name') or '',
                   'street': kw.get('street') or '',
                   'street2': kw.get('street2') or '',
                   'barangay_id': barangay_id or 0,
                   'city_id': city_id or 0,
                   'province_id': provice_id or 0,
                   'state_id': state_id or 0,
                   'zip_code': kw.get('zip_code') or '',
                   'country_id': country_id or 0,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.site_address_creation_popup",
                                                         values)

    @http.route(['/new/row/siteaddress'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_row_siteaddress(self, **kw):
        """ Render the new site address row template """
        datas = kw.get('datas')
        country_name = ''
        country_id = 0
        if datas.get('site_country_id'):
            country = request.env['res.country'].sudo().search(
                            [('id', '=', datas['site_country_id'])])
            country_id = country.id
            country_name = country.name
        state_id = 0
        state_name = ''
        if datas.get('site_state_id'):
            states = request.env['res.country.state'].sudo().search(
                                [('id', '=', datas['site_state_id'])])
            state_id = states.id
            state_name = states.name
        province_id = 0
        province_name = ''
        if datas.get('site_province_id'):
            province = request.env['res.country.province'].sudo().search(
                                [('id', '=', datas['site_province_id'])])
            province_id = province.id
            province_name = province.name
        city_id = 0
        city_name = ''
        if datas.get('site_city_id'):
            cities = request.env['res.country.city'].sudo().search(
                                [('id', '=', datas['site_city_id'])])
            city_id = cities.id
            city_name = cities.name
        barangay_id = 0
        barangay_name = ''
        if datas.get('site_barangay_id'):
            barangay = request.env['res.barangay'].sudo().search(
                                [('id', '=', datas['site_barangay_id'])])
            barangay_id = barangay.id
            barangay_name = barangay.name
        values = {
                  'name': datas.get('office_name'),
                  'street': datas.get('street'),
                  'street2': datas.get('street2'),
                  'barangay_id': barangay_id,
                  'barangay_name': barangay_name,
                  'city_id': city_id,
                  'city_name': city_name,
                  'province_id': province_id,
                  'province_name': province_name,
                  'state_id': state_id,
                  'state_name': state_name,
                  'zip_code': datas.get('zip_code'),
                  'country_id': country_id,
                  'country_name': country_name,
                  'count': datas.get('count')}
        return request.env['ir.ui.view'].render_template(
            "skit_vendor_portal.new_site_address_option_row", values)

    @http.route(['/contact_person/creation'], type='json', auth="public",
                methods=['POST'], website=True)
    def contact_person_creation(self, **kw):
        """ Display Contact Person creation form.
        @return popup.
        """
        values = {
                  'name': kw.get('c_name'),
                  'cdepartment': kw.get('c_department'),
                  'cposition': kw.get('c_position'),
                  'cphone': kw.get('c_phone'),
                  'cmobile': kw.get('c_mobile'),
                  'cemail': kw.get('c_email'),
                  }
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.vendor_contact_person_popup",
                                                         values)

    @http.route(['/new/row/contactperson'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_row_contactperson(self, **kw):
        """ Render the new contact row template """
        values = {
                  'name': kw.get('c_name'),
                  'department': kw.get('c_department'),
                  'position': kw.get('c_position'),
                  'phone': kw.get('c_phone'),
                  'mobile': kw.get('c_mobile'),
                  'email': kw.get('c_email'),
                  'count': kw.get('count')}
        return request.env['ir.ui.view'].render_template(
            "skit_vendor_portal.new_contactperson_option_row", values)

    @http.route(['/affiliated_contact/creation'], type='json', auth="public",
                methods=['POST'], website=True)
    def affiliated_contact_creation(self, **kw):
        """ Display Affiliated Contact creation form.
        @return popup.
        """
        values = {'name': kw.get('name'),
                  'relationship': kw.get('relationship'),
                  'email': kw.get('email'),
                  }

        return request.env['ir.ui.view'].render_template("skit_vendor_portal.vendor_affiliated_contact_popup",
                                                         values)

    @http.route(['/new/row/affiliated'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_row_affiliated(self, **kw):
        """ Render the new affiliated row template """
        values = {
                  'name': kw.get('aff_name'),
                  'email': kw.get('aff_email'),
                  'relationship': kw.get('aff_relationship'),
                  'count': kw.get('count')}
        return request.env['ir.ui.view'].render_template(
            "skit_vendor_portal.new_affiliated_option_row", values)

    @http.route(['/product_service/creation'], type='json', auth="public",
                methods=['POST'], website=True)
    def product_service_creation(self, **kw):
        """ Display product service creation form.
        @return popup.
        """
        product_classifications = request.env['product.classification'].sudo().search([])
        product_uom = request.env['uom.uom'].sudo().search([])
        category_id = 0
        if kw.get('category_id'):
            category_id = int(kw.get('category_id'))
        uom_id = 0
        if kw.get('uom_id'):
            uom_id = int(kw.get('uom_id'))
        file_attached = False
        file_attachments = []
        attachments = request.env['ir.attachment'].sudo().search([
                            ('id', 'in', literal_eval(kw.get('att_ids'))),
                            ('res_model', '=', 'product.service.offered')])
        if attachments:
            file_attached = True
            for attachment in attachments:
                file_attachments.append({'pfile_content': attachment.datas,
                                         'pfile_name': attachment.name,
                                         'type': attachment.type,
                                         'id': attachment.id})
        values = ({
                    'product_service': kw.get('p_name'),
                    'name': kw.get('p_desc'),
                    'product_classification_id': category_id,
                    'price': kw.get('p_price'),
                    'uom_id': uom_id,
                    'file_attached': file_attached,
                    'file_attachments': file_attachments,
                    'img_attached': kw.get('img_attached'),
                    'img_src': kw.get('image_1920'),
                    'product_classifications': product_classifications,
                    'product_uom': product_uom,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.product_service_offered_popup", values)

    @http.route(['/attachment/download'], type='http', auth='public')
    def download_attachment(self, attachment_id):
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "mimetype", "res_model", "res_id", "type", "url"]
        )
        if attachment:
            attachment = attachment[0]
        else:
            return redirect('/my/home')

        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            # we follow what is done in ir_http's binary_content for the extension management
            extension = os.path.splitext(attachment["name"] or '')[1]
            extension = extension if extension else mimetypes.guess_extension(attachment["mimetype"] or '')
            filename = attachment['name']
            filename = filename if os.path.splitext(filename)[1] else filename + extension
            return http.send_file(data, filename=filename, as_attachment=True)
        else:
            return request.not_found()

    @http.route(['/show_product/attachment'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_product_attachment(self, **kw):
        """ Display product service creation form.
        @return popup.
        """
        attachment = False
        if (kw.get('attachment_id')):
            attachment = request.env['ir.attachment'].sudo().browse(literal_eval(kw.get('attachment_id')))
        values = ({
                   'src': kw.get('src'),
                   'attachment': attachment
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.show_attached_files", values)

    @http.route(['/show/product_attach/popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_multi_product_attchment_popup(self, **kw):
        """ Show multi attachment.
        @return popup.
        """
        attachments = request.env['ir.attachment'].sudo().search([
                        ('id', 'in', literal_eval(kw.get('attach_ids'))),
                        ('res_model', '=', 'product.service.offered')])
        values = {'attachments': attachments}
        return request.env['ir.ui.view'].render_template("skit_website_my_po.show_dl_attachments_template", values)

    @http.route(['/view/product_photo'], type='json', auth="public",
                methods=['POST'], website=True)
    def view_product_photo(self, **kw):
        """ View product photo form.
        @return popup.
        """
        pro_service = False
        if kw.get('ps_id'):
            pro_service = request.env['product.service.offered'].sudo().search(
                                [('id', '=', int(kw.get('ps_id')))])
        values = ({
                    'img_attached': kw.get('img_attached'),
                    'img_src': kw.get('image_1920'),
                    'pro_service': pro_service,
                    'website': request.website,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.product_photo_view_popup", 
                                                         values)

    @http.route(['/new/row/product'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_row_product(self, **kw):
        """ Render the new product row template """
        # Create Attachment
        product_files = kw.get('product_files')
        attachment = False
        if product_files and kw.get('file_attached'):
            attachment = self.product_create_attachment(product_files)

        # Get Category from Imported data
        categ_id = 0
        if (kw.get('product_classification_id')):
            categ_name = str(kw.get('category_name'))
            prod_categ_id = request.env['product.classification'].sudo().search(
                            [('name', '=', categ_name)], limit=1)
            if prod_categ_id:
                categ_id = prod_categ_id.id
        elif kw.get('category_id'):
            categ_id = kw.get('category_id')
        # Get UOM from Imported data
        uom_id = 0
        if (kw.get('product_uom_id')):
            uom_name = str(kw.get('uom_name'))
            prod_uom_id = request.env['uom.uom'].sudo().search(
                            [('name', '=', uom_name)], limit=1)
            if prod_uom_id:
                uom_id = prod_uom_id.id
        elif kw.get('uom_id'):
            uom_id = kw.get('uom_id')
        prod_price = 0
        if kw.get('p_price'):
            prod_price = kw.get('p_price')
        values = {
                    'product_service': kw.get('p_name'),
                    'name': kw.get('p_desc'),
                    'price': float(prod_price),
                    'category_id': categ_id,
                    'category_name': kw.get('category_name'),
                    'uom_id': uom_id,
                    'uom_name': kw.get('uom_name'),
                    'file_attached': kw.get('file_attached'),
                    'img_attached': kw.get('img_attached'),
                    'img_src': kw.get('image_1920'),
                    'count': kw.get('count'),
                    'attachments': attachment if attachment else [0],
                    'is_edit_profile': kw.get('is_edit_profile') or False
                    }
        if(kw.get('is_edit_profile')):
            pro_service = request.env['product.service.offered'].sudo().create({
                                    'product_service': kw.get('p_name'),
                                    'name': kw.get('p_desc'),
                                    'product_classification_id': categ_id,
                                    'price': float(kw.get('p_price')),
                                    'uom_id': uom_id,
                                    'partner_id': request.env.user.partner_id.id
                                    })
            values['product_service_id'] = pro_service
        return request.env['ir.ui.view'].render_template(
            "skit_vendor_portal.new_product_option_row", values)

    # Create Attachments
    def product_create_attachment(self, file_datas):
        Attachments = request.env['ir.attachment']
        attachment_ids = []
        for file in file_datas:
            file_content = file['file_content']
            file_content = file_content.split(',')[1]
            attachment = Attachments.sudo().create({
                'name': file['file_name'],
                'res_name': file['file_name'],
                'type': 'binary',
                'res_model': 'product.service.offered',
                'datas': file_content
            })
            attachment_ids.append(attachment.id)
        return attachment_ids

    def vendor_catalogue_attachment(self, partner, file_datas):
        """ Create attachment in Vendor"""
        IrAttachment = request.env['ir.attachment'].sudo()
        attachment = False
        for file in file_datas:
            file_content = file['file_content']
            file_content = file_content.split(',')[1]
            attachment = IrAttachment.create({
                    'name': file['file_name'],
                    'res_name': file['file_name'],
                    'datas': file_content,
                    'res_model': 'res.partner',
                    'type': 'binary',
                    'res_id': partner.id
            })
        return attachment

    @http.route(['/vendor_registration/creation'], type='json', auth="public",
                methods=['POST'], website=True)
    def Create_Vendor_Registration(self, **kw):
        """ Create Vendor User Registration.
        @return Redirect to confirmation page.
        """
        if kw.get('vendor_datas'):
            vendor_datas = kw.get('vendor_datas')[0]
            vals = {'name': vendor_datas.get('name'),
                    'login': vendor_datas.get('email'),
                    'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
                    }
            # Create vendor user
            user = request.env['res.users'].sudo().create(vals)
            if user:
                partner = user.partner_id
                country_id = False
                if vendor_datas.get('country_id'):
                    country_id = int(vendor_datas.get('country_id'))
                state_id = False
                if vendor_datas.get('state_id'):
                    state_id = int(vendor_datas.get('state_id'))
                provice_id = False
                if vendor_datas.get('province_id'):
                    provice_id = int(vendor_datas.get('province_id'))
                city_id = False
                if vendor_datas.get('city_id'):
                    city_id = int(vendor_datas.get('city_id'))
                barangay_id = False
                if vendor_datas.get('barangay_id'):
                    barangay_id = int(vendor_datas.get('barangay_id'))
                industry_id = False
                if vendor_datas.get('industry_id'):
                    industry_id = int(vendor_datas.get('industry_id'))
                if vendor_datas.get('catalogue_all_attach'):
                    attach_file = vendor_datas['catalogue_all_attach']
                    # Create Attachment
                    self.vendor_catalogue_attachment(partner, attach_file)
                business_type = vendor_datas.get('business_type')
                if vendor_datas.get('company_type') == 'person':
                    business_type = 'Individual'
                partner_vals = {'company_type': vendor_datas.get('company_type'),
                                'business_type': business_type,
                                'business_name': vendor_datas.get('business_name'),
                                'industry_id': industry_id,
                                'vat': vendor_datas.get('vat'),
                                'phone': vendor_datas.get('phone'),
                                'email': vendor_datas.get('email'),
                                'mobile': vendor_datas.get('mobile'),
                                'website': vendor_datas.get('website'),
                                'country_id': country_id,
                                'state_id': state_id,
                                'province_id': provice_id,
                                'city_id': city_id,
                                'zip': vendor_datas.get('zip'),
                                'barangay_id': barangay_id,
                                'street2': vendor_datas.get('street2'),
                                'street': vendor_datas.get('street'),
                                'comment': vendor_datas.get('comment'),
                                'child_ids': vendor_datas.get('child_ids') or [],
                                'affiliated_contact_ids': vendor_datas.get('affiliated_contact_ids') or [],
                                'product_service_offered_line': vendor_datas.get('product_service_offered_line') or [],
                                'product_classification_ids': vendor_datas.get('product_classification_ids') or [],
                                'has_other_category': vendor_datas.get('has_other_category') or False,
                                'other_categories': vendor_datas.get('other_categories'),
                                'supplier_rank': 1,
                                'agree': vendor_datas.get('agree'),
                                'registration_date': date.today()
                                }
                # update partner values
                partner.sudo().write(partner_vals)
                # Send mail
                partner.sudo().send_portal_vendor_mail(user)
                partner.sudo().notify_vendor_creation(user)
                """ Create Accreditation"""
                request.env['partner.evaluation'].sudo().create({'partner_id': partner.id,
                                                                 'start_date': date.today()})
            return "/vendor/register_confirm"

    @http.route(['/view_profile/new_site_address_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_site_address_popup(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        country = request.env['res.country'].sudo().search([])
        country_id = request.env['res.country'].sudo().search([('code', '=', 'PH')], limit=1).id
        barangay = []
        province = []
        cities = []
        states = request.env['res.country.state'].sudo().search([('country_id', '=', int(country_id))])
        values = ({'countries': country,
                   'barangaies': barangay,
                   'states': states,
                   'province': province,
                   'cities': cities,
                   'barangay_id': 0,
                   'city_id': 0,
                   'province_id': 0,
                   'state_id': 0,
                   'country_id': 0,
                   })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.site_address_creation_popup_view",
                                                         values)

    @http.route('/view_profile/create_site_address', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def create_site_address(self, **kw):
        """ Create Vendor User Registration.
        @return Redirect to confirmation page.
        """
        for field in set(['country_id',
                          'state_id',
                          'title',
                          'nationality_country_id',
                          'religion_id',
                          'employment_status_id',
                          'employment_country_id',
                          'profession_id',
                          'city_id',
                          'barangay_id',
                          'province_id']) & set(kw.keys()):
            try:
                kw[field] = int(kw[field])
            except:
                kw[field] = False
        kw.pop('csrf_token', None)
        kw.pop('model_name', None) 
        kw.pop('website', None)    
        # partner.sudo().write({'child_ids': [(0, 0, kw)]})
        partner = request.env.user.partner_id
        if(kw.get('partner_id')):
            partner_id = kw.get('partner_id')
            kw.pop('partner_id')
            partner_child_id = request.env['res.partner'].sudo().search([('id', '=', int(partner_id))])
            partner_child_id.sudo().write(kw)
        else:
            partner_obj = request.env['res.partner'].sudo()
            partner_child_id = partner_obj.sudo().create(kw)
            partner.sudo().write({'child_ids': [(4, partner_child_id.id)]})
        return json.dumps({
            'id': partner_child_id.id,
            'name': partner_child_id.name,
            'country_id': partner_child_id.country_id.name if partner_child_id.country_id else '',
            'city_id': partner_child_id.city_id.name if partner_child_id.city_id else '',
            'state_id': partner_child_id.state_id.name if partner_child_id.state_id else '',
            'barangay_id': partner_child_id.barangay_id.name if partner_child_id.barangay_id else '',
            'province_id': partner_child_id.province_id.name if partner_child_id.province_id else '',
            'zip': partner_child_id.zip,
            'street': partner_child_id.street,
            'street2': partner_child_id.street2,
            'type': partner_child_id.type,
            'position': partner_child_id.function or '',
            'phone': partner_child_id.phone or '',
            'mobile': partner_child_id.mobile,
            'email': partner_child_id.email,
            'department': partner_child_id.department or '',
            'logged_in_partner_id': partner.id
            })


    @http.route('/view_profile/create_affiliated_contact', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def create_affiliated_contact(self, **kw):
        """ Create Vendor User Registration.
        @return Redirect to confirmation page.
        """

        kw.pop('csrf_token', None)
        kw.pop('model_name', None) 
        kw.pop('website', None)    
        partner = request.env.user.partner_id

        if(kw.get('partner_id')):
            partner_id = kw.get('partner_id')
            kw.pop('partner_id')
            partner_affilation_id = request.env['res.partner.affiliation'].sudo().search([('id', '=', int(partner_id))])
            partner_affilation_id.sudo().write(kw)
        else:

            partner_affilation_obj = request.env['res.partner.affiliation'].sudo()
            partner_affilation_id = partner_affilation_obj.sudo().create(kw)
            partner.sudo().write({'affiliated_contact_ids': [(4, partner_affilation_id.id)]})

        return json.dumps({
            'id': partner_affilation_id.id,
            'name': partner_affilation_id.name,
            'email': partner_affilation_id.email,
            'relationship': partner_affilation_id.relationship,
            'is_affiliated': True
            })

    @http.route('/view_profile/create_product_service', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def create_product_service(self, **kw):
        """ Create Vendor User Registration.
        @return Redirect to confirmation page.
        """
        partner = request.env.user.partner_id

        kw.pop('csrf_token', None)
        kw.pop('model_name', None) 
        kw.pop('website', None) 
        partner = request.env.user.partner_id
        for field in set(['uom_id',
                          'product_classification_id']) & set(kw.keys()):
            try:
                kw[field] = int(kw[field])
            except:
                kw[field] = False

        if(kw.get('partner_id')):
            partner_id = kw.get('partner_id')
            kw.pop('partner_id')
            if kw.get('image_1920[0][0]'):
                profile_image = kw.get('image_1920[0][0]').read()
                kw['image_1920'] = base64.b64encode(profile_image)
                kw.pop('image_1920[0][0]')
                if kw.get('attachment_ids[1][0]'):
                    kw.pop('attachment_ids[1][0]')
            product_service = request.env['product.service.offered'].sudo().search([('id', '=', int(partner_id))])
            product_service.sudo().write(kw)
        else:
            if kw.get('image_1920[0][0]'):
                profile_image = kw.get('image_1920[0][0]').read()
                kw['image_1920'] = base64.b64encode(profile_image)
                kw.pop('image_1920[0][0]')
                if kw.get('attachment_ids[1][0]'):
                    kw.pop('attachment_ids[1][0]')
            product_service_obj = request.env['product.service.offered'].sudo()
            product_service = product_service_obj.sudo().create(kw)
            partner.sudo().write({'product_service_offered_line': [(4, product_service.id)]})

        return json.dumps({
            'id': product_service.id,
            'name': product_service.name,
            'product_category_name': product_service.product_classification_id.name,
            'product_service': product_service.product_service,
            'price': product_service.price,
            'is_product_service': True,

            })

    @http.route(['/view_profile/edit_office_address'], type='json', auth="public",
                methods=['POST'], website=True)
    def edit_view_profile_address(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        partner_id = kw.get('partner_id')
        if(partner_id):
            partner = request.env['res.partner'].sudo().search([('id', '=', int(partner_id))])
        else:
            partner = False
        country = request.env['res.country'].sudo().search([])
        barangay = []
        province = []
        cities = []
        states = []
        ph_country_id = request.env['res.country'].sudo().search([('code', '=', 'PH')], limit=1).id
        states = request.env['res.country.state'].sudo().search([('country_id', '=', int(ph_country_id))])
        if partner.state_id:
            province = request.env['res.country.province'].sudo().search([('state_id', '=', partner.state_id.id)])
        if partner.province_id:
            cities = request.env['res.country.city'].sudo().search([('province_id', '=', partner.province_id.id)])
        if partner.city_id:
            barangay = request.env['res.barangay'].sudo().search([('city_id', '=', partner.city_id.id)])

        values = ({'countries': country,
                   'barangaies': barangay,
                   'states': states,
                   'province': province,
                   'cities': cities,

                   'partner': partner if partner else False,
                   'partner_id': partner.id if partner else False,
                   'name': partner.name if partner else '',
                   'street': partner.street if partner else '',
                   'street2': partner.street2 if partner else '',
                   'barangay_id': partner.barangay_id.id if partner else 0,
                   'city_id': partner.city_id.id if partner else 0,
                   'province_id': partner.province_id.id if partner else 0,
                   'state_id': partner.state_id.id if partner else 0,
                   'zip_code': partner.zip if partner else False,
                   'country_id': partner.country_id.id if partner else 0,

                   'function': partner.function if partner else False,
                   'department': partner.department if partner else False,
                   'phone': partner.phone if partner else False,
                   'mobile': partner.mobile if partner else False,
                   'email': partner.email if partner else False,

                   })
        if(partner.id == request.env.user.partner_id.id):
            return request.env['ir.ui.view'].render_template("skit_vendor_portal.head_office_address_creation_popup",
                                                          values)
        elif(partner.type == 'other'):
                return request.env['ir.ui.view'].render_template("skit_vendor_portal.site_address_creation_popup_view",
                                                         values)

        elif(partner.type == 'contact'):
            return request.env['ir.ui.view'].render_template("skit_vendor_portal.vendor_contact_person_popup_view",
                                                         values)

    @http.route(['/view_profile/update_office_address'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_office_address(self, **kw):
        """ Render the new site address row template """
        partner_id = kw.get('partner_id')
        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        if(kw.get('office_name')):
            kw.pop('office_name')
        if(kw.get('partner_id')):
            kw.pop('partner_id')
        for field in set(['country_id',
                                  'state_id',
                                  'title',
                                  'nationality_country_id',
                                  'religion_id',
                                  'employment_status_id',
                                  'employment_country_id',
                                  'profession_id',
                                  'city_id',
                                  'barangay_id',
                                  'province_id']) & set(kw.keys()):
                    try:
                        kw[field] = int(kw[field])
                    except:
                        kw[field] = False
        partner.sudo().write(kw)
        return True

    @http.route(['/view_profile/delete_partner'], type='json', auth="public",
                methods=['POST'], website=True)
    def delete_partner(self, **kw):
        """ Render the new site address row template """
        partner_id = kw.get('partner_id')
        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        partner.unlink(); 

    @http.route(['/view_profile/delete_affiliated_contact'], type='json', auth="public",
                methods=['POST'], website=True)
    def delete_affiliated_contact(self, **kw):
        """ Render the new site address row template """
        partner_id = kw.get('partner_id')
        partner = request.env['res.partner.affiliation'].sudo().search([('id', '=', partner_id)])
        partner.unlink(); 

    @http.route('/view_profile/update_contact/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def update_phone(self, **kw):
        """ Create Vendor User Registration.
        @return Redirect to confirmation page.
        """
        kw.pop('csrf_token', None)
        kw.pop('model_name', None)
        partner = request.env.user.partner_id
        partner.sudo().write(kw)
        return json.dumps({
            'id': partner.id,
            'email': partner.email,
            'phone': partner.phone,
            'mobile': partner.mobile,
            'website': partner.website,
            'comment': partner.comment
            })

    @http.route(['/view_profile/new_contact_person_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_contact_person_popup(self, **kw):
        """ Display Contact Person creation form.
        @return popup.
        """
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.vendor_contact_person_popup_view",
                                                         {})

    @http.route(['/view_profile/new_affiliated_contact_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_affiliated_contact_popup(self, **kw):
        """ Display Affiliated Contact creation form.
        @return popup.
        """
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.vendor_affiliated_contact_popup_view",
                                                         {})

    @http.route(['/view_profile/edit_affiliated_contact'], type='json', auth="public",
                methods=['POST'], website=True)
    def edit_affiliated_contact(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        affiliated_partner_id = kw.get('partner_id')
        if(affiliated_partner_id):
            partner = request.env['res.partner.affiliation'].sudo().search([('id', '=', int(affiliated_partner_id))])
        else:
            partner = False
        values = ({
               'partner': partner if partner else False,
               'partner_id': partner.id if partner else False,
               'name': partner.name if partner else '',
               'relationship': partner.relationship if partner else False,
               'email': partner.email if partner else False,
            })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.vendor_affiliated_contact_popup_view",
                                                         values)

    @http.route(['/view_profile/update_affiliate_contact'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_affiliate_contact(self, **kw):
        affiliated_partner_id = kw.get('partner_id')
        affiliated_partner = request.env['res.partner.affiliation'].sudo().search([('id', '=', affiliated_partner_id)])
        kw.pop('partner_id')
        affiliated_partner.sudo().write(kw)
        return True

    @http.route(['/view_profile/update_product_other_category'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_product_other_category(self, **kw):
        partner = request.env.user.partner_id
        other_category = kw.get('other_category')
        categ_ids = kw.get('product_classification_ids')
        other_categories = kw.get('other_categories')
        partner.sudo().write({'product_classification_ids': [(6, 0, categ_ids)],
                              'has_other_category': other_category,
                              'other_categories': other_categories
                              })
        return True

    @http.route(['/view_profile/update_comment'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_comment(self, **kw):
        "Update Other Remarks"
        partner = request.env.user.partner_id
        partner.sudo().write(kw)
        return True

    @http.route(['/view_profile/new_product_service_popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def new_product_service_popup(self, **kw):
        """ Display Product creation form.
        @return popup.
        """
        product_classifications = request.env['product.classification'].sudo().search([])
        product_uom = request.env['uom.uom'].sudo().search([])
        partner_id = request.env.user.partner_id.id
        values = {'product_classifications': product_classifications,
                  'product_uom': product_uom,
                  'website': request.website,
                  'partner': False,
                  'uom_id': 0,
                  'product_classification_id': 0,
                  'ps_id': '0',
                  'partner_id': partner_id,
                  'file_attached': False,
                  'file_attachments': []
                  }
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.product_service_offered_popup_view",
                                                         values)

    @http.route(['/delete/pro_service_line'], type='json', auth="public",
                methods=['POST'], website=True)
    def delete_product_service(self, **kw):
        """ Render the new site address row template """
        product_service = int(kw.get('id'))
        product_service = request.env['product.service.offered'].sudo().search(
                                    [('id', '=', product_service)])
        product_service.unlink()

    def keypro_create_attachment(self, file):
        Attachments = request.env['ir.attachment']
        file_content = file['file_content']
        file_content = file_content.split(',')[1]
        attachment = Attachments.sudo().create({
            'name': file['file_name'],
            'res_name': file['file_name'],
            'type': 'binary',
            'res_model': 'product.service.offered',
            'datas': file_content
        })
        return attachment

    @http.route(['/save/pro_service'], type='json', auth="public",
                methods=['POST'], website=True)
    def save_pro_service(self, **kw):
        """ Save the Key Product Service.
            @return True.
        """
        pro_service = request.env['product.service.offered'].sudo().browse(int(kw.get('pro_id')))
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', pro_service.id),
                            ('res_model', '=', 'product.service.offered')])
        datas = kw.get('datas')
        if(int(kw.get('pro_id')) > 0):
            pro_service.write(datas)
        else:
            datas['partner_id'] = int(kw.get('partner_id'))
            pro_service = request.env['product.service.offered'].sudo().create(datas)
        """ Attachment """
        if kw.get('image_1920') and kw.get('img_attached'):
            pro_service.write({'image_1920': kw.get('image_1920')})
        file_att_ids = []
        file_details = kw.get('pro_files')
        if(file_details and file_details[0].get('file_content')):
            for file in file_details:
                file_att_id = int(file['att_id'])
                if(file_att_id > 0):
                    file_att_ids.append(file_att_id)
                else:
                    attachment = self.keypro_create_attachment(file)
                    attachment.write({'res_id': pro_service.id})
        else:
            if kw.get('file_attch'):
                attachment = request.env['ir.attachment'].sudo().search([
                                ('res_id', '=', pro_service.id)])
                if attachment:
                    attachment.unlink()
        remove_att_ids = list(set(attachments.ids) - set(file_att_ids)) 
        if len(remove_att_ids) > 0:
            attachment = request.env['ir.attachment'].sudo().search([
                                ('id', 'in', remove_att_ids)])
            if attachment:
                attachment.unlink()
        values = {}
        values['pro_service_line'] = pro_service
        values['partner_id'] = int(kw.get('partner_id'))
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.new_product_service_line", values)

    @http.route(['/view_profile/edit_product_service'], type='json', auth="public",
                methods=['POST'], website=True)
    def edit_product_service(self, **kw):
        """ Display Site office address form.
        @return popup.
        """
        product_service_id = kw.get('ps_id')
        if(product_service_id):
            partner = request.env['product.service.offered'].sudo().search([('id', '=', int(product_service_id))])
        else:
            partner = False
        product_classifications = request.env['product.classification'].sudo().search([])
        product_uom = request.env['uom.uom'].sudo().search([])
        uom_id = 0
        if partner.uom_id:
            uom_id = partner.uom_id.id
        product_classification_id = 0
        if partner.product_classification_id:
            product_classification_id = partner.product_classification_id.id
        file_attached = False
        file_attachments = []
        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_id', '=', int(kw.get('ps_id'))),
                            ('res_model', '=', 'product.service.offered')])
        if attachments:
            file_attached = True
            for attachment in attachments:
                file_attachments.append({'pfile_content': attachment.datas,
                                         'pfile_name': attachment.name,
                                         'type': attachment.type,
                                         'id': attachment.id})
        product_price = False
        if partner.price:
            product_price = ('{:.2f}').format(partner.price)
        values = ({
               'partner': partner if partner else False,
               'partner_id': partner.id if partner else False,
               'website': request.website,
               'name': partner.name if partner else '',
               'product_service': partner.product_service if partner else False,
               'price': product_price,
               'uom_id': uom_id,
               'product_classification_id': product_classification_id,
               'product_classifications': product_classifications,
               'product_uom': product_uom,
               'file_attached': file_attached,
               'file_attachments': file_attachments,
               'ps_id': product_service_id
            })
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.product_service_offered_popup_view",
                                                         values)
 
    @http.route(['/view_profile/update_product_service'], type='json', auth="public",
                methods=['POST'], website=True)
    def update_product_service(self, **kw):
        product_service_id = kw.get('partner_id')
        product_service = request.env['product.service.offered'].sudo().search([('id', '=', product_service_id)])
        kw.pop('partner_id')
        if kw.get('file_details'):
            file_details = kw.get('file_details')
            exist_id = product_service.attachment_ids.ids
            for files in file_details:
                for file in files:
                    attachment = self.create_attachment(file)
                    exist_id.append(attachment.id)

            kw['attachment_ids'] = [(6, 0, exist_id)]
        if 'clear_image' in kw:
            kw['image_1920'] = False
            kw.pop('clear_image')
        elif(kw.get('image_1920')):
            file_content = kw.get('image_1920').split(',')[1]
            kw['image_1920'] = file_content
        product_service.sudo().write(kw)
        return True

    # Render Registration confirm template
    @http.route(['/vendor/register_confirm'],
                type='http', auth="public", website=True)
    def registration_confirm(self, **post):
        """ Confirm Vendor Registration.
        @return render confirmation page."""

        return request.env['ir.ui.view'].render_template(
                "skit_vendor_portal.vreg_confirm_temp")
        
    @http.route(['/show/product/attach/popup'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_product_multi_attchment_popup(self, **kw):
        """ Show multi attachment.
        @return popup.
        """
        attachments = request.env['ir.attachment'].sudo().search([
                        ('res_id', '=', kw.get('ps_id')),
                        ('res_model', '=', 'product.service.offered')])
        values = {'attachments': attachments}
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.show_product_attachments_template", values)
    
    @http.route(['/show/product_document'], type='json', auth="public",
                methods=['POST'], website=True)
    def show_product_documents(self, **kw):
        """ Display product document.
        @return popup.
        """
        attachment = request.env['ir.attachment'].sudo().browse(int(kw.get('att_id')))
        values = {'attachment': attachment}
        return request.env['ir.ui.view'].render_template("skit_vendor_portal.show_product_attached_files", values)
