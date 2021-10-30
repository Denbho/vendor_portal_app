# -*- coding: utf-8 -*-

from odoo import models, fields, api
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    def send_cron_edts_for_approval_dept_head_email(self, records):
        template_id = self.env.ref('edts.email_template_cron_edts_for_approval_dept_head').id
        view_id = self.env.ref('edts.view_move_form_inherit').id

        context = {
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            'view_id': view_id,
            'records': records
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)

    def send_cron_edts_for_validation_acctg_email(self, records):
        template_id = self.env.ref('edts.email_template_cron_edts_for_validation_acctg').id
        view_id = self.env.ref('edts.view_move_form_inherit').id

        context = {
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            'view_id': view_id,
            'records': records
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)

    def send_cron_edts_for_processing_finance_email(self, records):
        template_id = self.env.ref('edts.email_template_cron_edts_for_processing_finance').id
        view_id = self.env.ref('edts.view_move_form_inherit').id

        context = {
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            'view_id': view_id,
            'records': records
        }
        template = self.env['mail.template'].browse(template_id).with_context(context)
        template.send_mail(self.id, force_send=True)


class AccountMoveCron(models.Model):
    _inherit = 'account.move'

    def _cron_edts_sap_process(self):
        return True

    def _cron_edts_pending_for_approval_notification(self):
        _logger.info('EDTS Pending For Approval Notification is running')

        head_pending_records = self.env['account.move'].sudo().search([('status', 'in', ['waiting_for_head'])])
        acctg_pending_records = self.env['account.move'].sudo().search([('status', 'in', ['waiting_for_accounting'])])
        # finance_pending_records = self.env['account.move'].sudo().search([('status', 'in', ['processing_finance'])])

        heads = []
        acctgs = []
        # finances = []

        for record in head_pending_records:
            if record.approver and record.approver not in heads:
                heads.append(record.approver)

        for record in acctg_pending_records:
            if record.processor and record.processor not in acctgs:
                acctgs.append(record.processor)

        # Waiting for finance person record from SAP
        # for record in finance_pending_records:
        #     if record.processor and record.processor not in finances:
        #         finances.append(record.processor)

        for approver in heads:
            approver_records = self.env['account.move'].sudo().search([('status', 'in', ['waiting_for_head']), ('approver', '=', approver.id)], order='id desc')
            approver.send_cron_edts_for_approval_dept_head_email(approver_records)

        for processor in acctgs:
            processor_records = self.env['account.move'].sudo().search([('status', 'in', ['waiting_for_accounting']), ('processor', '=', processor.id)], order='id desc')
            processor.send_cron_edts_for_validation_acctg_email(processor_records)

        # Waiting for finance person record from SAP
        # for finance in finances:
        #     finance_records = self.env['account.move'].sudo().search([('status', 'in', ['processing_finance']), ('processor', '=', finance.id)], order='id desc')
        #     finance.send_cron_edts_for_processing_finance_email(finance_records)

        _logger.info('EDTS Pending For Approval Notification end')

    def cron_email_and_status_update_for_recurring_transactions(self):
        _logger.info('Email and Status Update for Recurring Transactions is running')

        recurring_transactions = self.env['account.move'].sudo().search([('status', 'in', ['ongoing', 'processing_finance', 'partial_payment_released', 'fully_paid']), ('edts_subtype', 'in', ['agency_contracts_accruals', 'agency_contracts_monthly', 'recurring_transactions_accruals', 'recurring_transactions_monthly']), ('parent_recurring_id', '=', False)])

        for transaction in recurring_transactions:
            present_date = datetime.now().date()

            if present_date > transaction.valid_to:
                transaction.send_completed_notification_email()
                transaction.set_completed_status()

            if transaction.is_in_valid_renewal_date:
                transaction.send_renewal_notification_email()

        _logger.info('Email and Status Update for Recurring Transactions end')

    def cron_automatic_creation_of_recurring_transactions(self):
        _logger.info('Automatic Creation of Recurring Transactions is running')

        recurring_transactions = self.env['account.move'].sudo().search([('status', 'in', ['ongoing', 'completed']), ('edts_subtype', 'in', ['agency_contracts_accruals', 'recurring_transactions_accruals']), ('parent_recurring_id', '=', False)])

        for transaction in recurring_transactions:
            present_date = datetime.now().date()
            allowed_months = transaction.get_allowed_months()
            allowed_years = transaction.get_allowed_years()

            if present_date.month in allowed_months and present_date.year in allowed_years and present_date.day >= transaction.run_day and (transaction.last_run_date is False or (transaction.last_run_date.month != present_date.month and transaction.last_run_date < transaction.valid_to)) and transaction.to_be_run_next_month() is False:
                new_valid_from = transaction.get_new_valid_from()
                new_valid_to = transaction.get_new_valid_to()
                new_amount = transaction.get_prorated_amount()

                vals = {
                    'is_recurring_invoice': True,
                    'parent_recurring_id': transaction.id,
                    'edts_subtype': transaction.edts_subtype,
                    'company_id': transaction.company_id.id,
                    'company_code': transaction.company_code,
                    'journal_id': transaction.journal_id.id,
                    'amount': new_amount,
                    'approved_amount': transaction.approved_amount,
                    'billed_amount': transaction.billed_amount,
                    'internal_order': transaction.internal_order,
                    'account_number': transaction.account_number,
                    'employee_code': transaction.employee_code,
                    'employee_id': transaction.employee_id.id,
                    'universal_vendor_code': transaction.universal_vendor_code,
                    'vendor_code_113': transaction.vendor_code_113,
                    'vendor_code_303': transaction.vendor_code_303,
                    'vendor_id': transaction.vendor_id.id,
                    'department': transaction.department,
                    'cost_center': transaction.cost_center,
                    'valid_from': new_valid_from,
                    'valid_to': new_valid_to,
                    'run_day': transaction.run_day,
                }

                child_transaction = self.create(vals)

                transaction.create_default_lines_for_next_record(child_transaction.id)
                transaction.child_recurring_ids = [(4, child_transaction.id)]
                if transaction.extension_reference_ids:
                    transaction.extension_reference_ids[0].extension_child_recurring_ids = [(4, child_transaction.id)]
                transaction.last_run_date = present_date
        _logger.info('Automatic Creation of Recurring Transactions end')

    def get_new_valid_from(self):
        latest_child_recurring_transaction = self.child_recurring_ids and self.child_recurring_ids[0]

        if not latest_child_recurring_transaction:
            new_valid_from = self.valid_from
        else:
            new_valid_from = latest_child_recurring_transaction.valid_to + relativedelta(days=1)

        return new_valid_from

    def get_new_valid_to(self):
        if self.is_valid_to_condition():
            new_valid_to = self.valid_to
        else:
            new_valid_to = datetime.now().date()

        return new_valid_to

    def get_prorated_amount(self):
        present_date = datetime.now().date()
        new_valid_from_date = self.get_new_valid_from()
        new_valid_to_date = self.get_new_valid_to()
        latest_child_recurring_transaction = self.child_recurring_ids and self.child_recurring_ids[0]

        max_days_in_a_month = monthrange(present_date.year, present_date.month)[1]
        max_days_in_valid_from_month = monthrange(new_valid_from_date.year, new_valid_from_date.month)[1]
        max_days_in_valid_to_month = monthrange(new_valid_to_date.year, new_valid_to_date.month)[1]

        if present_date.month == self.valid_from.month:
            prorated_amount = self.amount * ((present_date.day - self.valid_from.day)/max_days_in_a_month)
        elif self.is_hanging_transaction():
            dividend = 1 if new_valid_to_date.day == new_valid_from_date.day else new_valid_to_date.day - new_valid_from_date.day
            prorated_amount = self.amount * (dividend/max_days_in_valid_to_month)
        else:
            dividend = (max_days_in_valid_from_month - new_valid_from_date.day) if not latest_child_recurring_transaction else (max_days_in_valid_from_month - (new_valid_from_date.day - 1))
            valid_from_prorated_amount = self.amount * (dividend/max_days_in_valid_from_month)
            valid_to_prorated_amount = self.amount * (new_valid_to_date.day / max_days_in_valid_to_month)

            prorated_amount = valid_from_prorated_amount + valid_to_prorated_amount

        return prorated_amount

    def get_allowed_years(self):
        allowed_years = []
        end_date = self.valid_to
        initial_date = self.valid_from

        if end_date and initial_date:
            year_difference = end_date.year - initial_date.year

            if self.is_valid_to_day_greater_than_or_equal_to_run_day() and (end_date + relativedelta(months=1)).year != end_date.year:
                year_difference += 1

            for r in range(year_difference + 1):
                allowed_years.append((initial_date + relativedelta(years=r)).year)

        return allowed_years

    def get_allowed_months(self):
        allowed_months = []
        end_date = self.valid_to
        initial_date = self.valid_from

        if end_date and initial_date:
            month_difference = ((end_date.year - initial_date.year) * 12) + (end_date.month - initial_date.month)

            if self.is_valid_to_day_greater_than_or_equal_to_run_day():
                month_difference += 1

            for r in range(month_difference + 1):
                allowed_months.append((initial_date + relativedelta(months=r)).month)

        return allowed_months

    def is_valid_to_day_greater_than_or_equal_to_run_day(self):
        condition = False
        if self.valid_to.day >= self.run_day:
            condition = True

        return condition

    def is_valid_to_condition(self):
        present_date = datetime.now()
        latest_child_recurring_transaction = self.child_recurring_ids and self.child_recurring_ids[0]

        if self.is_valid_to_day_greater_than_or_equal_to_run_day() is False and self.valid_to.month == present_date.month:
            valid_to_condition = True
        elif self.is_valid_to_day_greater_than_or_equal_to_run_day() and latest_child_recurring_transaction and latest_child_recurring_transaction.valid_to.month == self.valid_to.month and latest_child_recurring_transaction.valid_to.day != self.valid_to.day:
            valid_to_condition = True
        else:
            valid_to_condition = False

        return valid_to_condition

    def is_hanging_transaction(self):
        is_hanging_record = False

        if self.is_valid_to_condition() and self.is_valid_to_day_greater_than_or_equal_to_run_day():
            is_hanging_record = True

        return is_hanging_record

    def to_be_run_next_month(self):
        to_be_run_next_month = False
        present_date = datetime.now()
        if self.is_valid_to_day_greater_than_or_equal_to_run_day() and present_date.month == self.valid_from.month:
            to_be_run_next_month = True
        return to_be_run_next_month
