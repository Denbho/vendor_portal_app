# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EdtsInfo(models.Model):
    _inherit = 'edts.info'

    def reject_edts(self):
        can_reject = True
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level2'):
                if not record.parent_recurring_id and record.edts_subtype == 'agency_contracts_accruals':
                    can_reject = True
                else:
                    can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                if record.edts_subtype in ('rawland_acquisition', 'techserv_liaison', 'setup', 'return',
                                           'agency_contracts_monthly', 'recurring_transactions_monthly') or \
                        record.parent_recurring_id and record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals'):
                    can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                if record.edts_subtype in ('setup', 'return'):
                    can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                if record.edts_subtype in ('invoice_w_po', 'advance_payment', 'techserv_liaison'):
                    can_reject = False
                else:
                    can_reject = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                if record.edts_subtype != 'stl':
                    can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                can_reject = True
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po'):
                    can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                can_reject = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                if record.edts_subtype == 'invoice_wo_po':
                    can_reject = True
                else:
                    can_reject = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_reject = True
            else:
                can_reject = False
        if can_reject:
            view_id = self.env.ref('edts.rejected_wizard_form').id
            return {
                'name': 'Reject',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'edts.reason.wizard',
                'view_id': view_id,
                'target': 'new',
                'context': {
                    'default_account_move_id': self.id
                }
            }
        else:
            raise ValidationError(_("You are not allowed to reject this request. Please contact the administrator"))

    def return_edts(self):
        can_return = True
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level2'):
                if not record.parent_recurring_id and record.edts_subtype == 'agency_contracts_accruals':
                    can_return = True
                else:
                    can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                if record.edts_subtype in ('rawland_acquisition', 'techserv_liaison', 'setup', 'return',
                                           'agency_contracts_monthly', 'recurring_transactions_monthly') or \
                        record.parent_recurring_id and record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals'):
                    can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                if record.edts_subtype in ('setup', 'return'):
                    can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                can_return = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                if record.edts_subtype == 'stl':
                    can_return = True
                else:
                    can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                can_return = True
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po'):
                    can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                can_return = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                if record.edts_subtype == 'invoice_wo_po':
                    can_return = True
                else:
                    can_return = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_return = True
            else:
                can_return = False
        if can_return:
            view_id = self.env.ref('edts.returned_wizard_form').id
            return {
                'name': 'Return',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'edts.reason.wizard',
                'view_id': view_id,
                'target': 'new',
                'context': {
                    'default_account_move_id': self.id
                }
            }
        else:
            raise ValidationError(_("You are not allowed to reject this request. Please contact the administrator"))

    def recall_edts(self):
        can_recall = True
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level2'):
                if record.edts_subtype in ('invoice_w_po', 'setup', 'return', 'agency_contracts_monthly', 'recurring_transactions_monthly') or \
                        record.parent_recurring_id and record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals'):
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                if record.edts_subtype in ('rawland_acquisition', 'techserv_liaison', 'setup', 'return', 'agency_contracts_monthly', 'recurring_transactions_monthly') or \
                        record.parent_recurring_id and record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals'):
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                if record.edts_subtype in ('setup', 'return'):
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                if record.edts_subtype in ('invoice_w_po', 'advance_payment', 'techserv_liaison'):
                    can_recall = False
                else:
                    can_recall = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                if record.edts_subtype in ('invoice_w_po', 'rawland_acquisition', 'stl', 'techserv_liaison',
                                           'agency_contracts_monthly', 'recurring_transactions_monthly',
                                           'agency_contracts_accruals', 'recurring_transactions_accruals'):
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.edts_subtype in ('invoice_wo_po', 'reimbursement', 'cash_advance', 'stl', 'setup', 'return'):
                    can_recall = True
                else:
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                if record.edts_subtype in ('return', 'agency_contracts_monthly', 'recurring_transactions_accruals',
                                           'recurring_transactions_monthly'):
                    can_recall = False
                else:
                    can_recall = True
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po'):
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                if record.edts_subtype in ('invoice_w_po', 'techserv_liaison', 'setup', 'return') or \
                        record.parent_recurring_id and record.edts_subtype == 'agency_contracts_accruals':
                    can_recall = False
                else:
                    can_recall = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                if record.edts_subtype in ('invoice_wo_po', 'reimbursement', 'cash_advance', 'stl'):
                    can_recall = True
                else:
                    can_recall = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_recall = True
            else:
                can_recall = False
            if not can_recall:
                raise ValidationError(_("You are not allowed to recall this request.\n"
                                        "Please contact the administrator"))
        return super(EdtsInfo, self).recall_edts()

    def submit_edts(self):
        submit_edts = False
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level2'):
                submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                if record.edts_subtype in ('rawland_acquisition', 'techserv_liaison', 'setup' ,'return', 'agency_contracts_monthly', 'recurring_transactions_monthly') or\
                        record.parent_recurring_id and record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals') :
                    submit_edts = False
                else:
                    submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                if record.edts_subtype in ('reimbursement', 'cash_advance', 'stl'):
                    submit_edts = True
                else:
                    submit_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                if record.edts_subtype in ('invoice_w_po', 'advance_payment', 'techserv_liaison'):
                    submit_edts = False
                else:
                    submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                if record.edts_subtype in ('invoice_w_po', 'rawland_acquisition', 'stl', 'techserv_liaison'):
                    submit_edts = False
                else:
                    submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.edts_subtype in ('invoice_wo_po', 'reimbursement', 'cash_advance', 'stl', 'setup', 'return'):
                    submit_edts = True
                else:
                    submit_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po', 'stl', 'techserv_liaison', 'setup'):
                    submit_edts = False
                else:
                    submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po', 'setup', 'return'):
                    submit_edts = False
                else:
                    submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                if record.edts_subtype in ('invoice_w_po', 'techserv_liaison', 'setup', 'return') or \
                        record.parent_recurring_id and record.edts_subtype == 'agency_contracts_accruals':
                    submit_edts = False
                else:
                    submit_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                if record.edts_subtype in ('invoice_wo_po', 'reimbursement', 'cash_advance', 'stl'):
                    submit_edts = True
                else:
                    submit_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                submit_edts = True
            if not submit_edts:
                raise ValidationError(_("You are not allowed to submit the EDTS request. Please contact the administrator"))
            return super(EdtsInfo, self).submit_edts()

    def approve_edts(self):
        approve_edts = False
        for record in self:
            if (self.env.user.has_group('edts_user_access.group_edts_level1') or
                self.env.user.has_group('edts_user_access.group_edts_level2')) and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                approve_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                if not record.parent_recurring_id and \
                        record.edts_subtype == 'recurring_transactions_accruals':
                    approve_edts = False

                else:
                    approve_edts = True
            elif (self.env.user.has_group('edts_user_access.group_edts_level4') or
                  self.env.user.has_group('edts_user_access.group_edts_level5') or
                  self.env.user.has_group('edts_user_access.group_edts_level6') or
                  self.env.user.has_group('edts_user_access.group_edts_level7')) and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                approve_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po') and \
                        (not record.parent_recurring_id and record.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    approve_edts = False
                else:
                    approve_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                approve_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                if record.edts_subtype == 'invoice_wo_po':
                    approve_edts = True
                else:
                    approve_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                approve_edts = True
            if approve_edts:
                view_id = self.env.ref('edts.signature_wizard_form').id
                return {
                    'name': 'Approve EDTS',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'edts.signature.wizard',
                    'view_id': view_id,
                    'target': 'new',
                    'context': {
                        'default_account_move_id': self.id,
                        'default_action': 'approve'
                    }
                }
            else:
                raise ValidationError(
                    _("You are not allowed to approved the EDTS request. Please contact the administrator"))

    def validate_edts(self):
        validate_edts = False
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                if record.parent_recurring_id and record.edts_subtype in \
                        ('agency_contracts_accruals', 'recurring_transactions_accruals', 'recurring_transactions_monthly'):
                    validate_edts = True
                else:
                    validate_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                validate_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                if record.edts_subtype == 'stl':
                    validate_edts = True
                else:
                    validate_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                validate_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                if not record.parent_recurring_id and \
                        record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals'):
                    validate_edts = False
                else:
                    validate_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype in ('advance_payment', 'rawland_acquisition',
                                           'reimbursement', 'cash_advance', 'stl', 'techserv_liaison'):
                    validate_edts = True
                else:
                    validate_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                validate_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                not self.env.user.has_group('edts_user_access.group_edts_level11'):
                if record.edts_subtype == 'invoice_wo_po':
                    validate_edts = True
                else:
                    validate_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                validate_edts = True

            if validate_edts:
                view_id = self.env.ref('edts.signature_wizard_form').id
                return {
                    'name': 'Validate EDTS',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'edts.signature.wizard',
                    'view_id': view_id,
                    'target': 'new',
                    'context': {
                        'default_account_move_id': self.id,
                        'default_action': 'validate'
                    }
                }
            else:
                raise ValidationError(_("You are not allowed to Validate the EDTS request. \n"
                                        "Please contact the administrator"))

    def process_finance(self):
        if not self.env.user.has_group('edts_user_access.group_edts_level11'):
            raise ValidationError(_("You are not allowed to process the finance of this request. \n"
                                        "Please contact the administrator"))
        return super(EdtsInfo, self).process_finance()

    def countered_edts(self):
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level2'):
                countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                if record.edts_subtype in ('invoice_wo_po', 'invoice_w_po', 'agency_contracts_monthly',
                                           'recurring_transactions_monthly') or \
                        (record.parent_recurring_id and record.edts_subtype in ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    countered_edts = True
                else:
                    countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                countered_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                if record.edts_subtype == 'stl':
                    countered_edts = True
                else:
                    countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                if record.edts_subtype == 'return' or \
                        (not record.parent_recurring_id and record.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    countered_edts = False
                else:
                    countered_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                if record.edts_subtype == 'invoice_wo_po':
                    countered_edts = False
                else:
                    countered_edts = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                countered_edts = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                countered_edts = True
            else:
                countered_edts = False

            if not countered_edts:
                raise ValidationError(_("You are not allowed to Countered the EDTS request. \n"
                                        " Please contact the administrator."))
            return super(EdtsInfo, self).countered_edts()

    def get_all_payments(self):
        payment_tree = self.env.ref('edts.payment_reference_tree')
        payment_form = self.env.ref('edts.payment_reference_form')
        create_button = True
        edit_button = True
        view_payment = True
        if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                not self.env.user.has_group('edts_user_access.group_edts_level2'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
                view_payment = False
        elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                not self.env.user.has_group('edts_user_access.group_edts_level3'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                not self.env.user.has_group('edts_user_access.group_edts_level4'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                not self.env.user.has_group('edts_user_access.group_edts_level5'):
            if self.edts_subtype != 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                not self.env.user.has_group('edts_user_access.group_edts_level6'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                not self.env.user.has_group('edts_user_access.group_edts_level7'):
            if self.edts_subtype != 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                not self.env.user.has_group('edts_user_access.group_edts_level8'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                not self.env.user.has_group('edts_user_access.group_edts_level9'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                not self.env.user.has_group('edts_user_access.group_edts_level10'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = False
                edit_button = False
        elif self.env.user.has_group('edts_user_access.group_edts_level10'):
            if self.edts_subtype == 'invoice_wo_po':
                create_button = True
                edit_button = True
        if self.status in ['fully_paid']:
            create_button = False
            edit_button = False
        if view_payment:
            return {
                'name': 'Payments',
                'type': 'ir.actions.act_window',
                'domain': [('account_move_id', '=', self.id)],
                'res_model': 'edts.payment.reference.line',
                'view_mode': 'tree,form',
                'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
                'context': {
                    'default_account_move_id': self.id,
                    'create': create_button,
                    'edit': edit_button,
                }
            }
        else:
            raise ValidationError(_("You are not allowed to view the payments. Please contact the administrator."))

    def get_need_released_payments(self):
        can_release = True
        for record in self:
            if (self.env.user.has_group('edts_user_access.group_edts_level5') or
                    self.env.user.has_group('edts_user_access.group_edts_level6')) and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.edts_subtype == 'return' or (not record.parent_recurring_id and
                                                       record.edts_subtype in ('agency_contracts_accruals',
                                                                               'recurring_transactions_accruals')):
                    can_release = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                can_release = False
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype == 'return' or (not record.parent_recurring_id and
                                                       record.edts_subtype in ('agency_contracts_accruals',
                                                                               'recurring_transactions_accruals')):
                    can_release = False
            elif (self.env.user.has_group('edts_user_access.group_edts_level9') or
                    self.env.user.has_group('edts_user_access.group_edts_level10'))  and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_release = False

            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_release = True
            else:
                can_release = False
        if can_release:
            payment_tree = self.env.ref('edts.payment_reference_tree')
            payment_form = self.env.ref('edts.payment_reference_to_release_form')
            return {
                'name': 'To Release',
                'type': 'ir.actions.act_window',
                'domain': [('account_move_id', '=', self.id), ('released', '=', False), ('is_payment_ready_for_releasing', '=', True)],
                'res_model': 'edts.payment.reference.line',
                'view_mode': 'tree,form',
                'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
                'context': {
                    'create': False,
                    'edit': False,
                }
            }
        else:
            raise ValidationError(_("You are not allowed to release payments for this request. \n"
                                    "Please contact the administrator."))

    def get_need_encashed_payments(self):
        can_encash = True
        for record in self:
            if (self.env.user.has_group('edts_user_access.group_edts_level5') or
                    self.env.user.has_group('edts_user_access.group_edts_level6')) and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.edts_subtype == 'return' or (not record.parent_recurring_id and
                                                       record.edts_subtype in ('agency_contracts_accruals',
                                                                               'recurring_transactions_accruals')):
                    can_encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                can_encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype == 'return' or (not record.parent_recurring_id and
                                                       record.edts_subtype in ('agency_contracts_accruals',
                                                                               'recurring_transactions_accruals')):
                    can_encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_encash = False

            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_encash = True
            else:
                can_encash = False
        if can_encash:
            payment_tree = self.env.ref('edts.payment_reference_tree')
            payment_form = self.env.ref('edts.payment_reference_to_encash_form')

            return {
                'name': 'To Encash',
                'type': 'ir.actions.act_window',
                'domain': [('account_move_id', '=', self.id), ('released', '=', True), ('encashed', '=', False), ('mode', 'in', ['check', 'check_writer'])],
                'res_model': 'edts.payment.reference.line',
                'view_mode': 'tree,form',
                'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
                'context': {
                    'create': False,
                    'edit': False
                }
            }
        else:
            raise ValidationError(_("You are not allowed to Encash for this request. \n"
                                    "Please contact the administrator."))

    def get_need_or_received_payments(self):
        can_receive_or = True
        for record in self:
            if (self.env.user.has_group('edts_user_access.group_edts_level5') or
                    self.env.user.has_group('edts_user_access.group_edts_level6')) and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.edts_subtype == 'return' or (not record.parent_recurring_id and
                                                       record.edts_subtype in ('agency_contracts_accruals',
                                                                               'recurring_transactions_accruals')):
                    can_receive_or = False
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                can_receive_or = False
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.edts_subtype == 'return' or (not record.parent_recurring_id and
                                                       record.edts_subtype in ('agency_contracts_accruals',
                                                                               'recurring_transactions_accruals')):
                    can_receive_or = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_receive_or = False

            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                can_receive_or = True
            else:
                can_receive_or = False
        if can_receive_or:
            payment_tree = self.env.ref('edts.payment_reference_tree')
            payment_form = self.env.ref('edts.payment_reference_to_receive_or_form')

            return {
                'name': 'To Receive OR',
                'type': 'ir.actions.act_window',
                'domain': [('account_move_id', '=', self.id), ('released', '=', True), ('or_received', '=', False), ('is_or_required', '=', True)],
                'res_model': 'edts.payment.reference.line',
                'view_mode': 'tree,form',
                'views': [(payment_tree.id, 'tree'), (payment_form.id, 'form')],
                'context': {
                    'create': False,
                }
            }
        else:
            raise ValidationError(_("You are not allowed to receive an OR for this request. \n"
                                    "Please contact the administrator."))

    def get_all_liquidations(self):
        create_button = True
        edit_button = True
        view_liquidation = True
        for record in self:
            if self.env.user.has_group('edts_user_access.group_edts_level1') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level2'):
                view_liquidation = True
                if record.edts_subtype == 'cash_advance':
                    create_button = False
                    edit_button = False
            elif self.env.user.has_group('edts_user_access.group_edts_level2') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level3'):
                view_liquidation = True
                if record.edts_subtype == 'cash_advance':
                    create_button = False
                    edit_button = False
                if record.edts_subtype in ('stl', 'techserv_liaison'):
                    create_button = False
                    edit_button = True
            elif self.env.user.has_group('edts_user_access.group_edts_level3') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level4'):
                view_liquidation = True
                if record.edts_subtype in ('cash_advance', 'stl', 'techserv_liaison'):
                    create_button = False
                    edit_button = False
            elif (self.env.user.has_group('edts_user_access.group_edts_level4') or
                    self.env.user.has_group('edts_user_access.group_edts_level5') or
                    self.env.user.has_group('edts_user_access.group_edts_level6') or
                    self.env.user.has_group('edts_user_access.group_edts_level7') or
                    self.env.user.has_group('edts_user_access.group_edts_level8')) and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                view_liquidation = True
                if record.edts_subtype in ('cash_advance', 'stl', 'techserv_liaison'):
                    create_button = False
                    edit_button = True
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                view_liquidation = True
                if record.edts_subtype in ('cash_advance', 'stl', 'techserv_liaison'):
                    create_button = True
                    edit_button = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level11'):
                view_liquidation = True
                if record.edts_subtype in ('cash_advance', 'stl', 'techserv_liaison'):
                    create_button = False
                    edit_button = False
            elif self.env.user.has_group('edts_user_access.group_edts_level11'):
                view_liquidation = True
                if record.edts_subtype in ('cash_advance', 'stl', 'techserv_liaison'):
                    create_button = True
                    edit_button = True
            else:
                view_liquidation = False
                create_button = False
                edit_button = False
        if view_liquidation:
            liquidation_tree = self.env.ref('edts.liquidation_reference_tree')
            liquidation_form = self.env.ref('edts.liquidation_reference_form')
            liquidation_search = self.env.ref('edts.edts_liquidation_reference_search_view')
            if create_button:
                if len(self.liquidation_reference_ids) > 1:
                    create_button = False
            return {
                'name': 'Liquidations',
                'type': 'ir.actions.act_window',
                'domain': [('account_move_id', '=', self.id)],
                'res_model': 'edts.liquidation.reference',
                'view_mode': 'tree,form',
                'search_view_id': [liquidation_search.id, 'search'],
                'views': [(liquidation_tree.id, 'tree'), (liquidation_form.id, 'form')],
                'context': {
                    'default_account_move_id': self.id,
                    'default_edts_subtype': self.edts_subtype,
                    'default_company_id': self.edts_company_id.id,
                    'default_journal_id': self.journal_id.id,
                    'default_request_date': self.request_date,
                    'default_currency_id': self.currency_id.id,
                    'default_amount': self.amount,
                    'default_requestor': self.create_uid.id,
                    'create': create_button,
                    'edit': edit_button
                }
            }
        else:
            raise ValidationError(_("You are not allowed to view the liquidation. Please contact the administrator"))


class PaymentReferenceLine(models.Model):
    _inherit = 'edts.payment.reference.line'

    def encash_payment(self):
        for record in self:
            if not self.env.user.has_group('edts_user_access.group_edts_level4'):
                encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                if record.account_move_id.edts_subtype == 'return' or \
                        (not record.account_move_id.parent_recurring_id and record.account_move_id.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    encash = False
                else:
                    encash = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.account_move_id.edts_subtype == 'return' or \
                        (not record.account_move_id.parent_recurring_id and record.account_move_id.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    encash = False
                else:
                    encash = True
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.account_move_id.edts_subtype == 'techserv_liaison':
                    encash = True
                else:
                    encash = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                if record.account_move_id.edts_subtype == 'return' or \
                        (not record.account_move_id.parent_recurring_id and record.account_move_id.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    encash = False
                else:
                    encash = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10'):
                encash = True
            else:
                encash = False

            if not encash:
                raise ValidationError(_("You are not allowed to encash the payment request. Please contact the administrator"))
        return super(PaymentReferenceLine, self).encash_payment()

    def or_received_payment(self):
        for record in self:
            if not self.env.user.has_group('edts_user_access.group_edts_level4'):
                received_payment = False
            elif self.env.user.has_group('edts_user_access.group_edts_level4') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level5'):
                if record.account_move_id.edts_subtype == 'return' or \
                        (not record.account_move_id.parent_recurring_id and record.account_move_id.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    received_payment = False
                else:
                    received_payment = True
            elif self.env.user.has_group('edts_user_access.group_edts_level5') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level6'):
                received_payment = False
            elif self.env.user.has_group('edts_user_access.group_edts_level6') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level7'):
                if record.account_move_id.edts_subtype == 'return' or \
                        (not record.account_move_id.parent_recurring_id and record.account_move_id.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    received_payment = False
                else:
                    received_payment = True
            elif self.env.user.has_group('edts_user_access.group_edts_level7') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level8'):
                received_payment = False
            elif self.env.user.has_group('edts_user_access.group_edts_level8') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level9'):
                if record.account_move_id.edts_subtype == 'techserv_liaison':
                    received_payment = True
                else:
                    received_payment = False
            elif self.env.user.has_group('edts_user_access.group_edts_level9') and \
                    not self.env.user.has_group('edts_user_access.group_edts_level10'):
                if record.account_move_id.edts_subtype == 'return' or \
                        (not record.account_move_id.parent_recurring_id and record.account_move_id.edts_subtype in
                         ('agency_contracts_accruals', 'recurring_transactions_accruals')):
                    received_payment = False
                else:
                    received_payment = True
            elif self.env.user.has_group('edts_user_access.group_edts_level10'):
                received_payment = True
            else:
                received_payment = False

            if not received_payment:
                raise ValidationError(_("You are not allowed to received the payment request. Please contact the administrator"))
        return super(PaymentReferenceLine, self).or_received_payment()


class LiquidationReference(models.Model):
    _inherit = 'edts.liquidation.reference'

    @api.constrains('account_move_id')
    def check_account_move_duplicate(self):
        for record in self:
            exist = record.search([('id', '!=', record.id), ('account_move_id', '=', record.account_move_id.id)])
            if exist:
                raise ValidationError(_("EDTS No. already exists in the records. Please check the records properly."))