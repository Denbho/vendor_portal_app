# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_privacy_policy = fields.Boolean('Enable Privacy Policy',
                                           readonly=False,
                                           related='website_id.enable_privacy_policy')
    privacy_policy_title = fields.Char('Title',
                                       readonly=False,
                                       related='website_id.privacy_policy_title')
    privacy_policy_body = fields.Html('Body',
                                      readonly=False,
                                      related='website_id.privacy_policy_body')
    privacy_policy_info = fields.Text(string="Privacy Policy Info",
                                      readonly=False,
                                      related='website_id.privacy_policy_info')
    body_bg_color = fields.Char(related='website_id.body_bg_color',
                                readonly=False)
    body_bg_image = fields.Binary(string="Login Background",
                                  related='website_id.body_bg_image',
                                  readonly=False)
    login_panel_bg_color = fields.Char(related='website_id.login_panel_bg_color',
                                       readonly=False)
    terms_and_condition_title = fields.Char('Title',
                                       readonly=False,
                                       related='website_id.terms_and_condition_title')
    terms_and_condition_body = fields.Html('Body',
                                      readonly=False,
                                      related='website_id.terms_and_condition_body')

