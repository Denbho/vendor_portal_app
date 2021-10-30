from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError


class InheritedPropertySaleCreditCommitteeApproval(models.Model):
    _inherit = 'property.sale.credit.committee.approval'

    def request_approve(self):
        if self.env.user.has_group('admin_user_access.group_admin_account_officer_staff') or \
                self.env.user.has_group('admin_user_access.group_admin_account_officer_leader') or \
                self.env.user.has_group('property_admin_monitoring.group_property_supervisor') or \
                self.env.user.has_group('admin_user_access.property_credit_officer_level2') or \
                self.env.user.has_group('admin_user_access.property_credit_officer_level3'):
            raise ValidationError(_("You are not allowed to do this request. Please contact the administrator."))
        res = super(InheritedPropertySaleCreditCommitteeApproval, self).request_approve()
        return res

    def unlink(self):
        if self.state == 'approved':
            raise ValidationError(_("You cannot delete an approved records! Please contact the administrator."))
        return super(InheritedPropertySaleCreditCommitteeApproval, self).unlink()

    @api.model
    def create(self, values):
        res = super(InheritedPropertySaleCreditCommitteeApproval, self).create(values)
        if res:
            if self.env.user.has_group('property_admin_monitoring.group_property_supervisor') and res.property_sale_id.account_officer_user_id.id != self.env.user.id:
                raise ValidationError(_("You are not allowed to create for this record. Please check the assigned account officer."))

        return res

    def write(self, values):
        res = super(InheritedPropertySaleCreditCommitteeApproval, self).write(values)
        if res:
            if self.env.user.has_group('property_admin_monitoring.group_property_supervisor') and self.property_sale_id.account_officer_user_id.id != self.env.user.id:
                raise ValidationError(_("You are not allowed to write for this record. Please check the assigned account officer."))
        return res



