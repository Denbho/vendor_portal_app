# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritedResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_css(self):
        for rec in self:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level1') or  self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level2'):
                rec.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                rec.x_css = False

    x_css = fields.Html(
        string='CSS',
        sanitize=False,
        compute='_compute_css',
        store=False,
    )

    def unlink(self):
        if self.accredited:
            raise ValidationError(_("You cannot delete an accredited vendors! Please contact the administrator."))
        return super(InheritedResPartner, self).unlink()


class InheritedPartnerEvaluation(models.Model):
    _inherit = "partner.evaluation"

    def _compute_css(self):
        for rec in self:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level1') or  self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level2'):
                rec.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                rec.x_css = False

    x_css = fields.Html(
        string='CSS',
        sanitize=False,
        compute='_compute_css',
        store=False)

    def submit_request(self):
        res = super(InheritedPartnerEvaluation, self).submit_request()
        if res:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level5') and \
                    (not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or
                     not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7')):
                raise ValidationError(_("You are not allowed to submit this record. Please contact the administrator."))
        return res

    def confirm_request(self):
        res = super(InheritedPartnerEvaluation, self).confirm_request()
        if res:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level5') and \
                    (not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or
                     not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7')):
                raise ValidationError(_("You are not allowed to submit this record. Please contact the administrator."))
        return res

    def _compute_evaluator_count(self):
        for rec in self:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or \
                    self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7'):
                self.evaluator_count = len(rec.evaluator_line)
            else:
                self.evaluator_count = len(rec.evaluator_line.filtered(lambda r: r.evaluator_id.id == self.env.user.id))

    def action_view_evaluator(self):
        self.ensure_one()
        values = {
            'name': _('Evaluator'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.evaluator',
            'target': 'current',
            'context': {
                'default_partner_evaluation_id': self.id,
                'default_type': 'technical',
            },
        }
        if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or \
                self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7'):
            values['domain'] = [('partner_evaluation_id', '=', self.id)]
        else:
            values['domain'] = [('partner_evaluation_id', '=', self.id), ('evaluator_id', '=', self.env.user.id)]
        return values


class InheritPartnerRegularEvaluation(models.Model):
    _inherit = "partner.regular.evaluation"

    def submit_request(self):
        res = super(InheritPartnerRegularEvaluation, self).submit_request()
        if res:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level5') and \
                    (not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or
                     not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7')):
                raise ValidationError(_("You are not allowed to submit this record. Please contact the administrator."))
        return res

    def confirm_request(self):
        res = super(InheritPartnerRegularEvaluation, self).confirm_request()
        if res:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level5') and \
                    (not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or
                     not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7')):
                raise ValidationError(_("You are not allowed to submit this record. Please contact the administrator."))
        return res

    def approve_request(self):
        res = super(InheritPartnerRegularEvaluation, self).approve_request()
        if res:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level5') and \
                    (not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or
                     not self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7')):
                raise ValidationError(_("You are not allowed to submit this record. Please contact the administrator."))
        return res

    def _compute_evaluator_count(self):
        for rec in self:
            if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or \
                    self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7'):
                self.evaluator_count = len(rec.evaluator_line)
            else:
                self.evaluator_count = len(rec.evaluator_line.filtered(lambda r: r.evaluator_id.id == self.env.user.id))

    def action_view_evaluator(self):
        self.ensure_one()
        values = {
            'name': _('Evaluator'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.regular.evaluator',
            'target': 'current',
            'context': {
                'default_partner_evaluation_id': self.id,
                'default_type': 'technical',
            },
        }
        if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or \
                self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7'):
            values['domain'] = [('partner_evaluation_id', '=', self.id)]
        else:
            values['domain'] = [('partner_evaluation_id', '=', self.id), ('evaluator_id', '=', self.env.user.id)]
        return values
