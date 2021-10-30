from odoo import fields, models, api
import http
import json
import logging

_logger = logging.getLogger("_name_")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def tag_po_acceptance_status(self, acceptance_status, declined_note):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        payload = json.dumps([])
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type,
                   'Mandt': str(self.company_id.sap_client_id),
                   'Ebeln': str(self.name),
                   'Status': acceptance_status == 'accepted' and '1' or '0',
                   'Remarks': declined_note}
        prefix = api_key.api_prefix
        conn = http.client.HTTPSConnection(api_key.api_url)
        conn.request("POST", f"{prefix}VendorAcceptanceTag", payload, headers)
        res = conn.getresponse()
        data = res.read()
        _logger.info(f"\n\nTriggered: {data.decode('utf-8')}\n\n")
        return True

    def write(self, vals):
        super(PurchaseOrder, self).write(vals)
        if 'acceptance_status' in vals and vals.get('acceptance_status'):
            self.tag_po_acceptance_status(vals.get('acceptance_status'), 'declined_note' in vals and vals.get('declined_note') or 'Accepted')
