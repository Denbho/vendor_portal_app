# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import http
import json
import logging

_logger = logging.getLogger("_name_")


class AdminSelectTypeOfEvaluation(models.TransientModel):
    _inherit = 'admin.select.type.of.evaluation'

    @api.model
    def view_init(self, fields):
        res = super(AdminSelectTypeOfEvaluation, self).view_init(fields)
        evaluation = self.env['partner.evaluation'].sudo().browse(self._context.get('active_id'))
        for line in evaluation.evaluator_line:
            for ln in line.evaluation_line:
                if not ln.display_type and ln.score == 0:
                    raise ValidationError(_("Evaluators must complete evaluating per criteria."))
        return res

    def create_sap_vendor(self, partner):
        company = self.env['res.company'].sudo().search([('code', '=', self.company_code)])
        if not company[:1]:
            raise ValidationError(_(f"Record found related to company code {self.company_code}"))
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        prefix = api_key.api_prefix
        conn = http.client.HTTPSConnection(api_key.api_url)
        street = partner.street
        if partner.street2:
            street = f"{street}, {partner.street2}"
        if not partner.vat or not partner.email:
            raise ValidationError(_("Vendor Email and TIN is required when creating a vendor in SAP."))
        if not partner.zip:
            raise ValidationError(_("Please define the vendor Zip Code address"))
        if not partner.phone and not partner.mobile:
            raise ValidationError(_("Please define vendor's Mobile or Landline number."))
        payload = json.dumps([
                                {
                                    "AccountGroup": str(self.vendor_account_group_id.code),
                                    "City": partner.city_id and str(partner.city_id.name) or "N/A",
                                    "HouseNumber": street and str(street) or "N/A",
                                    "PostalCode": partner.zip and str(partner.zip) or "N/A",
                                    "Street": street or "N/A",
                                    "CompanyCode": str(self.company_code),
                                    "Email": str(partner.email),
                                    "LiableToWH": self.is_subject_to_wh_tax and "X" or "",
                                    "Mobile": partner.mobile and str(partner.mobile) or "0",
                                    "Name": str(partner.name),
                                    "TelNo": partner.phone and str(partner.phone) or "0",
                                    "Tin": str(partner.vat),
                                    "Title": partner.title and str(partner.title) or "Company",
                                    "VatStat": str(self.vat_type),
                                    "WhTaxCode": self.wh_tax_code_id and str(self.wh_tax_code_id.code) or "N/A",
                                    "SapClientId": str(company.sap_client_id)
                                }
                            ])
        conn.request("POST", f"{prefix}VendorCreation", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        # raise ValidationError(_(f"{json_data}"))
        # _logger.info(f"\n\nData: {payload}\nJSON: {json_data}\n\n")
        if json_data.get('Status') == 'E':
            raise ValidationError(_(f"{json_data.get('MessageLog')}"))
        elif json_data.get('Status') == 'S':
            value = {'universal_vendor_code': json_data.get('UniversalVendor')}
            if company.sap_client_id == 113:
                value['vendor_code_113'] = json_data.get('VendorNumber')
            else:
                value['vendor_code_303'] = json_data.get('VendorNumber')
            partner.sudo().write(value)
        else:
            raise ValidationError(_(f"Connection Problem.\n{json_data}"))

    def approve(self):
        partner = self.env['partner.evaluation'].sudo().browse(self._context.get('active_id')).partner_id
        if not partner.universal_vendor_code:
            self.create_sap_vendor(partner)
        super(AdminSelectTypeOfEvaluation, self).approve()
