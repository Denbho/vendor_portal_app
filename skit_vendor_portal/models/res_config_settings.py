from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_nda = fields.Boolean('Enable NON-DISCLOSURE AGREEMENT (NDA)')
    nda_title = fields.Char('Title')
    nda_body = fields.Html('Body')
    enable_privacy_policy = fields.Boolean('Enable Privacy Policy')
    privacy_policy_title = fields.Char('Title')
    privacy_policy_body = fields.Html('Body')
    enable_terms_and_condition = fields.Boolean('Enable Terms and Condition')
    terms_and_condition_title = fields.Char('Title')
    terms_and_condition_body = fields.Html('Body')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['enable_nda'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.enable_nda')
        res['nda_title'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.nda_title')
        res['nda_body'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.nda_body')
        res['enable_privacy_policy'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.enable_privacy_policy')
        res['privacy_policy_title'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.privacy_policy_title')
        res['privacy_policy_body'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.privacy_policy_body')
        res['enable_terms_and_condition'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.enable_terms_and_condition')
        res['terms_and_condition_title'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.terms_and_condition_title')
        res['terms_and_condition_body'] = self.env['ir.config_parameter'].sudo().get_param('skit_vendor_portal.terms_and_condition_body')
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('skit_vendor_portal.enable_nda', self.enable_nda)
        param.set_param('skit_vendor_portal.nda_title', self.nda_title)
        param.set_param('skit_vendor_portal.nda_body', self.nda_body)
        param.set_param('skit_vendor_portal.enable_privacy_policy', self.enable_privacy_policy)
        param.set_param('skit_vendor_portal.privacy_policy_title', self.privacy_policy_title)
        param.set_param('skit_vendor_portal.privacy_policy_body', self.privacy_policy_body)
        param.set_param('skit_vendor_portal.enable_terms_and_condition', self.enable_terms_and_condition)
        param.set_param('skit_vendor_portal.terms_and_condition_title', self.terms_and_condition_title)
        param.set_param('skit_vendor_portal.terms_and_condition_body', self.terms_and_condition_body)
