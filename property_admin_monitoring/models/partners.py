# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import http.client
import json
import logging

_logger = logging.getLogger("_name_")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_group = fields.Char(string="Vendor Group")
    broker_level = fields.Char(string="Broker Level")
    property_sale_ids = fields.One2many('property.admin.sale', 'partner_id', string="Properties")
    property_sale_count = fields.Integer(compute="_get_property_sale_count")
    sales_account_number = fields.Char(string="Sale Account Number", track_visibility="always")
    commission_rate = fields.Float(string="Commission Rate", track_visibility="always")
    company_code = fields.Char(string="Company Code", track_visibility="always")
    profession = fields.Char(string="Profession", track_visibility="always")

    sap_religion = fields.Char(string="Religion", help="From SAP DATA", track_visibility="always")
    sap_title = fields.Char(string="SAP Title")
    sap_nationality = fields.Char(string="SAP Nationality")
    sap_employment_status = fields.Char(string="SAP Employment Status")
    sap_employment_country = fields.Char(string="SAP Employment Country")
    sap_city = fields.Char(string="SAP City")
    sap_country = fields.Char(string="SAP Country")
    sap_continent = fields.Char(string="SAP Continent")
    sap_province = fields.Char(String="SAP Province")
    sap_business_entity_identification = fields.Char(string="SAP Business Entity Identification")
    sap_other_field = fields.Text(string="Other SAP Data")

    def _get_property_sale_count(self):
        for r in self:
            r.property_sale_count = r.env['property.admin.sale'].sudo().search_count([('partner_id', '=', r.id)])

    def sap_contact_profile(self, vals):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        conn = http.client.HTTPSConnection(api_key.api_url)
        prefix = api_key.api_prefix
        nationality = 'employment_country_code' in vals and vals.get('employment_country_code') or False
        if not nationality:
            if 'employment_country_id' in vals and vals.get('employment_country_id'):
                country = self.env['res.country'].sudo().browse(vals.get('employment_country_id'))
                nationality = country.code
            elif self.nationality_country_id:
                nationality = self.nationality_country_id.code
        payload = [
                    {
                        "MANDT": str(self.sap_client_id),
                        "KUNNR": str(self.partner_assign_number),
                        "CONTACT_MOB": 'mobile' in vals and str(vals.get('mobile')) or str(self.mobile) or "",
                        "CONTACT_NO": 'phone' in vals and str(vals.get('phone')) or str(self.phone) or "",
                        "EMAIL": 'email' in vals and str(vals.get('email')) or str(self.email) or "",
                        "BIRTH_DATE": 'date_of_birth' in vals and str(vals.get('date_of_birth')) or str(self.date_of_birth) or "",
                        "NATIONALITY": str(nationality),
                        "RELIGION": 'sap_religion' in vals and str(vals.get('sap_religion')) or str(self.sap_religion) or "",
                        "GENDER": 'gender' in vals and str(vals.get('gender')) or str(self.gender) or "",
                        "MARITAL_STATUS": 'marital' in vals and str(vals.get('marital')) or str(self.marital) or "",
                        "EMP_PROF": 'profession' in vals and str(vals.get('profession')) or str(self.profession) or "",
                        "MON_INCOM": 'monthly_income' in vals and vals.get('monthly_income') or self.monthly_income or 0.0,
                        "FB": 'social_facebook' in vals and str(vals.get('social_facebook')) or str(self.social_facebook) or "",
                        "INSTAGRAM": 'social_instagram' in vals and str(vals.get('social_instagram')) or str(self.social_instagram) or "",
                        "LINKEDIN": 'social_linkedin' in vals and str(vals.get('social_linkedin')) or str(self.social_linkedin) or "",
                        "CONTACT_MOB2": 'mobile2' in vals and str(vals.get('mobile2')) or str(self.mobile2) or "",
                        "INCOME_CUR": 'income_currency_code' in vals and str(vals.get('income_currency_code')) or str(self.income_currency_code) or ""
                    }
                ]
        # _logger.info(f"\n\n\nUpdate SAP Contact\n Payload: {payload}\n\n")
        conn.request("POST", f"{prefix}PostCustomerDetails", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        # _logger.info(f"\n\n\nUpdate SAP Contact\n Payload: {str(data.decode('utf-8'))}\n")
        return True

    def write(self, vals):
        if any(['mobile' in vals, 'phone' in vals, 'email' in vals, 'date_of_birth' in vals, 'employment_country_id' in vals,
                'sap_religion' in vals, 'gender' in vals, 'marital' in vals, 'profession' in vals, 'monthly_income' in vals,
                'social_facebook' in vals, 'social_instagram' in vals, 'social_linkedin' in vals, 'mobile2' in vals, 'income_currency_code' in vals]) and self.partner_assign_number and self.sap_client_id:
            self.sap_contact_profile(vals)
        return super(ResPartner, self).write(vals)

    # def update_sap_contact(self):
    #     api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
    #     headers = {'X-AppKey': api_key.api_app_key,
    #                'X-AppId': api_key.api_app_id,
    #                'Content-Type': api_key.api_content_type}
    #     conn = http.client.HTTPSConnection(api_key.api_url)
    #     payload = '[{\"MANDT\": \"%s\", \"VBELN\": \"%s\", \"CODEGRUPPE\": \"%s\", \"CODE\": \"%s\", \"DATETIME\": \"%s\"}]' % (
    #         property_sale.company_id.sap_client_id, property_sale.so_number, r.document_id.group_code,
    #         r.document_id.code, datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
    #     conn.request("POST", "/VistaAdminAPI/rest/DocsOdooMaintenance/CreateDocs", payload, headers)
    #     res = conn.getresponse()
    #     data = res.read()
    #     json_data = json.loads(data.decode("utf-8"))
