from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class PropertyAdminSaleInherited(models.Model):
    _inherit = 'property.admin.sale'

    loan_sub_stage_id = fields.Many2one('property.sale.sub.status', string="Loan Sub-Status", track_visibility="always")
    check_loan_status = fields.Boolean(string="Check Loan Status", compute='compute_check_loans_status')

    def write(self, values):
        res = super(PropertyAdminSaleInherited, self).write(values)
        if res:
            if (self.env.user.has_group('property_admin_monitoring.group_property_user') or
                self.env.user.has_group('admin_system_user_access.group_admin_account_officer_staff') or
                self.env.user.has_group('admin_system_user_access.group_admin_account_officer_leader')) and \
                    self.account_officer_user_id.id != self.env.user.id:
                if (not self.env.user.has_group('property_admin_monitoring.group_property_supervisor') or
                        not self.env.user.has_group('property_admin_monitoring.group_property_supervisor')):
                    if (not self.env.user.has_group('base.group_system') or
                            not self.env.user.has_group('base.group_no_one')):
                        raise ValidationError(_("You are not allowed to write for this record. Please check the assigned account officer."))

        return res

    @api.depends('stage_id')
    def compute_check_loans_status(self):
        for record in self:
            if record.stage_id:
                if record.stage_id.name == 'Loan Released' or record.stage_id.name == 'Loan Releasing':
                    record.check_loan_status = True
                else:
                    record.check_loan_status = False


class PropertyDocumentSubmissionLine(models.Model):
    _inherit = 'property.document.submission.line'

    def write(self, values):
        res = super(PropertyDocumentSubmissionLine, self).write(values)
        if res:
            if (self.env.user.has_group('admin_system_user_access.group_admin_account_officer_leader') or
                self.env.user.has_group('property_admin_monitoring.group_property_supervisor')) and \
                    self.property_sale_id.account_officer_user_id.id != self.env.user.id:
                raise ValidationError(_("You are not allowed to write for this record. Please check the assigned account officer."))
        return res


class PropertyDetail(models.Model):
    _inherit = "property.detail"

    def write(self, values):
        res = super(PropertyDetail, self).write(values)
        if res:
            if 'active' in values:
                raise ValidationError(_("You are not allowed to archive/unarchive for this record."))
        return res


class PropertySubdivisionPhase(models.Model):
    _inherit = "property.subdivision.phase"

    def write(self, values):
        res = super(PropertySubdivisionPhase, self).write(values)
        if res:
            if 'active' in values:
                raise ValidationError(_("You are not allowed to archive/unarchive for this record."))
        return res