from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class InheritPurchaseBidVendor(models.Model):
    _inherit = "purchase.bid.vendor"

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
            'name': _('Evaluation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'vendor.evaluator',
            'target': 'current',
            'context': {
                'default_vendor_bid_id': self.id,
                'default_type': 'technical',
            },
        }
        if self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level6') or \
                self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level7'):
            values['domain'] = [('vendor_bid_id', '=', self.id)]
        else:
            values['domain'] = [('vendor_bid_id', '=', self.id), ('evaluator_id', '=', self.env.user.id)]
        return values


class AdminSelectTypeOfEvaluation(models.TransientModel):
    _inherit = 'admin.select.type.of.evaluation'
    _description = 'Select Type of Evaluation'

    def approve(self):
        partner_update = {}
        for line in self.partner_evaluation_id.evaluator_line:
            for ln in line.evaluation_line:
                if not ln.display_type and ln.score == 0:
                    raise Warning("Evaluators must complete evaluating per criteria.")
        if self.type_of_evaluation:
            eval_months = 1
            if self.type_of_evaluation == 'quarterly':
                eval_months = 3
            elif self.type_of_evaluation == 'semi_annual':
                eval_months = 6
            elif self.type_of_evaluation == 'annual':
                eval_months = 12
            start_date = self.partner_evaluation_id.start_date or date.today()
            next_evaluation_date = start_date + relativedelta(months=eval_months)
            self.partner_evaluation_id.type_of_evaluation = self.type_of_evaluation
            partner_update.update({
                'type_of_evaluation': self.type_of_evaluation,
                'next_evaluation_date': next_evaluation_date,
            })
            # Create schedule activity
            if self.evaluation_responsible_ids:
                partner_model = self.env['ir.model'].sudo().search([('model','=','res.partner')])
                if partner_model[:1]:
                    new_sched_activity = self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,     #To Do
                        'res_model_id': partner_model.id,
                        'res_id': self.partner_evaluation_id.partner_id,
                        'summary': 'For Regular Evaluation',
                        'user_id': self.evaluation_responsible_ids.ids[0],
                        'note': '<b>Regular Evaluation.</b>',
                        'date_deadline': next_evaluation_date,
                    })
                    new_sched_activity.action_close_dialog()
        partner_update.update({
            'vat_type': self.vat_type,
            'is_subject_to_wh_tax': self.is_subject_to_wh_tax,
            'purchase_org_id': self.purchase_org_id.id,
            'vendor_account_group_id': self.vendor_account_group_id.id,
            'property_supplier_payment_term_id': self.property_supplier_payment_term_id.id,
            'evaluation_responsible_ids': [[6, False, [l for l in self.evaluation_responsible_ids.ids]]],
            'accreditation_id': self.partner_evaluation_id.id,
        })
        if self.wh_tax_code_id:
            partner_update['wh_tax_code_id'] = self.wh_tax_code_id and self.wh_tax_code_id.id or False
        self.partner_evaluation_id.partner_id.write(partner_update)
        self.partner_evaluation_id.approve_request()
        return {'type': 'ir.actions.act_window_close'}


class AdminSalesInvoice(models.Model):
    _inherit = 'admin.sales.invoice'

    def _compute_css(self):
        for rec in self:
            rec.x_css = False

    x_css = fields.Html(
        string='CSS',
        sanitize=False,
        compute='_compute_css',
        store=False,
    )
    check_create = fields.Boolean(string="Check Create")

    document_status = fields.Selection([
        ('Original Documents Received', 'Original Documents Received'),
        ('Original Documents Review', 'Original Documents Review'),
        ('Awaiting Original Documents', 'Awaiting Original Documents'),
        ('Returned to Vendor', 'Returned to Vendor')
    ], string="Document Status", track_visibility="always")

    def write(self, values):
        if self.admin_si_type == 'no_po' and self.env.user.has_group('admin_vendor_portal_access.group_vendor_portal_level2b'):
            if 'document_status' in values or 'countered' in values or \
                    'countered_date' in values or 'countering_notes' in values or \
                    'po_delivery_ids' in values or 'countered_by' in values or 'attention_to' in values or \
                    'account_move_id' in values or 'company_id' in values or 'company_code' in values:
                pass
            elif (values.get('company_id') or self.company_id) or (values.get('company_code') or self.company_code):
                pass
            else:
                raise ValidationError(_("You are not allowed to modify a Non-PO related SI. \n"
                                        "Please contact the administrator."))

        return super(AdminSalesInvoice, self).write(values)
