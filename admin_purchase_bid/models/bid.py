# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from num2words import num2words
from odoo.exceptions import Warning, ValidationError
import logging

_logger = logging.getLogger("_name_")

_STATES = [
    ('draft', 'Draft'),
    ('waiting_for_verification', 'Waiting for Verification'),
    ('waiting_for_approval', 'Waiting for Approval'),
    ('send_bid_invitation', 'Sending Bid Invitation'),
    ('invitation_sent', 'Bid Invitation Sent'),
    ('pre_bidding', 'Pre-Bidding'),
    ('halted', 'Halted'),
    ('post_bidding', 'Post-Bidding'),
    ('bid_selection', 'Bid Selection'),
    ('waiting_bid_selection_ver', 'Waiting for Bid Selection Verification'),
    ('waiting_bid_selection_con', 'Waiting for Bid Selection Confirmation'),
    ('waiting_bid_selection_app', 'Waiting for Bid Selection Approval'),
    ('done', 'Done'),
    ('cancel', 'Cancelled')
]

_BIDDER_STATES = [
    ('draft', 'Draft'),
    ('waiting_for_acceptance', 'Waiting For Acceptance'),
    ('bidding_in_progress', 'Bidding In-Progress'),
    ('bidding_halt', 'Bidding Halted'),
    ('bidding_cancel', 'Bidding Cancelled'),
    ('done', 'Done'),
    ('decline', 'Declined'),
    ('cancel', 'Canceled'),
    ('no_response', 'No Response'),
]

_ACCEPTANCE = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('did_not_accept', 'Did not accept'),
]

_EVALUATION = [
    ('pending', 'Pending'),
    ('ongoing_review', 'Ongoing review'),
    ('approved', 'Approved'),
]


class PurchaseBid(models.Model):
    _name = "purchase.bid"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Bid"
    _order = 'date_created desc'

    def _compute_vendor_count(self):
        for record in self:
            record.vendor_count = len([line.id for line in record.vendor_line])

    def _compute_event_count(self):
        for record in self:
            record.event_count = len(self.env['event.event'].search([('bid_id','=',record.id)]))

    @api.model
    def default_get(self, default_fields):
        res = super(PurchaseBid, self).default_get(default_fields)
        default_template_data = self.env['vendor.evaluation.template'].search([('template_purpose', '=', 'bid')], limit=1)
        res.update({
            'evaluation_line': [
                (0, 0, line._prepare_evaluation_criteria('technical')) for line in
                default_template_data.technical_evaluation_line
            ],
            'commercial_evaluation_line': [
                (0, 0, line._prepare_evaluation_criteria('commercial')) for line in
                default_template_data.commercial_evaluation_line
            ],
            'assigned_evaluator_line': [
                (0, 0, line._prepare_evaluation_evaluator()) for line in
                default_template_data.assigned_evaluator_line
            ],
            'technical_valuation_weight': default_template_data.technical_valuation_weight,
            'commercial_valuation_weight': default_template_data.commercial_valuation_weight
        })
        return res

    def _compute_check_date_prebid_postbid(self):
        for rec in self:
            rec.check_date_prebid_postbid = True
            current_datetime = datetime.now()
            if rec.state in ['send_bid_invitation', 'invitation_sent']:
                if rec.bid_opening_date and current_datetime >= rec.bid_opening_date:
                    sent_bid_cnt = 0
                    invitation_not_sent = 0
                    for line in rec.vendor_line:
                        if not line.is_kicked and line.invitation == 'sent':
                            sent_bid_cnt += 1
                        if not line.is_kicked and line.state == 'draft':
                            invitation_not_sent += 1
                    if sent_bid_cnt >= 2 and not invitation_not_sent:
                        rec.state = 'pre_bidding'
            if rec.state == 'pre_bidding':
                if rec.bid_closing_date and current_datetime >= rec.bid_closing_date:
                    accepted_cnt = 0
                    for line in rec.vendor_line:
                        if not line.is_kicked and line.acceptance == 'accepted':
                            accepted_cnt += 1
                    if accepted_cnt >= 2:
                        rec.state = 'post_bidding'
                        rec.assign_evaluators()

    def _compute_bid_summary(self):
        for record in self:
            bid_summary = ""
            if self.vendor_id:
                bid_summary = "<b>Negotiated Amount (Gross): </b>" + "{:,.2f}".format(self.vendor_id.negotiated_amount)
                if self.vendor_id.lead_time:
                    bid_summary = bid_summary + "<br/><b>Lead Time: </b>" + str(self.vendor_id.lead_time)
                if self.vendor_id.terms_of_payment_line:
                    bid_summary = bid_summary + "<br/><br/><h4><u>Terms of Payment</u></h4>"
                    for terms_line in self.vendor_id.terms_of_payment_line:
                        bid_summary = bid_summary + "<b>" + terms_line.name + ": </b>" + "{:,.2f}".format(
                            terms_line.payment_percent) + "%<br/>"
            self.bid_summary = bid_summary

    name = fields.Char(string='Bid', required=True, copy=False, default=lambda self: _('New'), readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, track_visibility='onchange')
    company_code = fields.Char(string='Company Code', track_visibility='onchange')
    project_name = fields.Char(string='Project Name', required=True, track_visibility='onchange')
    project_location = fields.Char(string='Project Location', track_visibility='onchange')
    wbs_element = fields.Char(string='Wbs Element', track_visibility='onchange')
    scope_of_work = fields.Char(string='Scope of Work', required=True, track_visibility='onchange')
    scope_of_work_remark = fields.Text(string="Scope of Work Remarks", required=True)
    purchasing_officer = fields.Many2one('res.users', string='Purchasing Officer', required=True,
                                         track_visibility='onchange')
    bid_opening_date = fields.Datetime(string="Bid Opening Date", track_visibility='onchange', copy=False)
    bid_closing_date = fields.Datetime(string="Bid Closing Date", track_visibility='onchange')
    date_halted = fields.Datetime(string="Date Halted", track_visibility='onchange')
    date_resume = fields.Date(string="Date Resume", track_visibility='onchange')
    document_reminder_date = fields.Date(string="Document Submission Reminder Date")
    budget = fields.Float(string="Budget", track_visibility='onchange')
    price_ceiling = fields.Float(string="Price Ceiling", track_visibility='onchange')
    target_price = fields.Float(string="Target Price", track_visibility='onchange')
    deadline_of_submission = fields.Date(string='Document Deadline of Submission', track_visibility='onchange')
    document_requirement_id = fields.Many2many('document.requirement', string='Document Requirement')
    date_created = fields.Datetime(string="Creation Date", default=fields.Datetime.now, copy=False)
    technical_valuation_weight = fields.Float(string="Technical Valuation Weight", track_visibility="always", default=1)
    commercial_valuation_weight = fields.Float(string="Commercial Valuation Weight", track_visibility="always",
                                               default=1)
    evaluation_line = fields.One2many('vendor.evaluation.line', 'bid_id', string='Technical Evaluation Criteria',
                                      copy=True, domain=[('type', '=', 'technical')], track_visibility='onchange')
    commercial_evaluation_line = fields.One2many('vendor.evaluation.line', 'bid_id',
                                                 string='Commercial Evaluation Criteria', copy=True,
                                                 domain=[('type', '=', 'commercial')], track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    vendor_id = fields.Many2one('purchase.bid.vendor', string='Selected Vendor',
                                domain="[('bid_id', '=', id),('is_kicked','=', False),('acceptance','=', 'accepted')]",
                                track_visibility='onchange')
    bid_summary = fields.Text(string='Bid Summary', compute='_compute_bid_summary')
    bid_selection_remarks = fields.Text(string='Bid Selection Remarks')
    date_selected = fields.Date(string='Date', track_visibility='onchange')
    agreement_contract_no = fields.Many2one('contracts.and.agreements', string='Agreement/Contract No.',
                                            track_visibility='onchange')
    start_date = fields.Date(string="Start Date", track_visibility='onchange')
    end_date = fields.Date(string="End Date", track_visibility='onchange')
    vendor_line = fields.One2many('purchase.bid.vendor', 'bid_id', string='Bidders', copy=True,
                                  track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    invitation_acceptance = fields.Boolean(compute='_compute_invitation_acceptance', string='Invitation Acceptance',
                                           store=True)
    invitation_sent = fields.Boolean(string='Invitation Sent', copy=False)
    vendor_count = fields.Integer(compute='_compute_vendor_count', string='Bidders Count')
    event_count = fields.Integer(compute='_compute_event_count', string='Events Count')
    check_date_prebid_postbid = fields.Boolean(compute='_compute_check_date_prebid_postbid',
                                               string='Check date for Pre-Bid & Post-Bid')
    pr_related_ids = fields.Many2many('purchase.requisition.material.details', string='PR Related')
    assigned_evaluator_line = fields.One2many('assigned.evaluator.line', 'bid_id', string='Assigned Evaluator', copy=True)
    # Approver
    confirmed_by = fields.Many2one('res.users', string="Confirmed By", track_visibility='onchange')
    confirmed_date = fields.Datetime('Date Confirmed', track_visibility='onchange')
    verified_by = fields.Many2one('res.users', string="Verified By", track_visibility='onchange')
    verified_date = fields.Datetime('Date Verified', track_visibility='onchange')
    approved_by = fields.Many2one('res.users', string="Approved By", track_visibility='onchange')
    approved_date = fields.Datetime('Date Approved', track_visibility='onchange')
    bs_confirmed_by = fields.Many2one('res.users', string="Confirmed By", track_visibility='onchange')
    bs_confirmed_date = fields.Datetime('Date Confirmed', track_visibility='onchange')
    bs_verified_by = fields.Many2one('res.users', string="Verified By", track_visibility='onchange')
    bs_verified_date = fields.Datetime('Date Verified', track_visibility='onchange')
    bs_approved_by = fields.Many2one('res.users', string="Approved By", track_visibility='onchange')
    bs_approved_date = fields.Datetime('Date Approved', track_visibility='onchange')
    rtd_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reset to Draft Reason', track_visibility='always')
    rtd_description = fields.Text(string='Reset to Draft Description', track_visibility='always')
    cancel_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Cancelation Reason', track_visibility='always')
    cancel_description = fields.Text(string='Cancelation Description', track_visibility='always')
    halt_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Halt Reason', track_visibility='always')
    halt_description = fields.Text(string='Halt Description', track_visibility='always')
    state = fields.Selection(selection=_STATES,
                             string='Bid Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')
    deadline_of_confirmation = fields.Datetime('Deadline of Confirmation')

    @api.onchange('bid_opening_date')
    def onchange_bid_opening_date(self):
        if self.bid_opening_date:
            # Deadline of confirmation is 4 days after opening date excluding saturday and sunday.
            # 0 is monday and 6 is sunday
            week_day = self.bid_opening_date.weekday()
            confirm_days = 4
            if week_day == 5:
                confirm_days = 5
            elif week_day in [1, 2, 3, 4]:
                confirm_days = 6
            self.deadline_of_confirmation = self.bid_opening_date + timedelta(days=confirm_days)

    def unlink(self):
        for rfi_detail in self:
            if not rfi_detail.state == 'cancel':
                raise Warning('In order to delete bidding, you must cancel it first.')
        return super(PurchaseBid, self).unlink()

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
          company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
          if company[:1]:
              self.company_id = company.id

    @api.onchange('deadline_of_submission')
    def onchange_deadline_of_submission(self):
        if self.deadline_of_submission and self.bid_opening_date:
            if self.deadline_of_submission >= self.bid_opening_date.date():
                raise Warning(
                    "Document Deadline Submission date should not be greater than or equal to bid opening date.")

    @api.depends('vendor_line', 'vendor_line.acceptance')
    def _compute_invitation_acceptance(self):
        for record in self:
            acceptance = True
            has_accept = False
            for line in record.vendor_line:
                if not line.is_kicked and line.acceptance:
                    if line.acceptance == 'pending':
                        acceptance = False
                    if line.acceptance == 'accepted':
                        has_accept = True
            if acceptance and not has_accept:
                acceptance = False
            self.invitation_acceptance = acceptance

    def validate_related_pr(self, bid_id, pr_line_new_ids, action_type):
        material_line_obj = self.env['purchase.requisition.material.details']
        pr_related_ids = material_line_obj.search([('id', 'in', pr_line_new_ids)])
        pr_line_ids = []
        error_logs = ""
        for line in pr_related_ids:
            if line.bid_id and line.bid_id.id != bid_id:
                error_logs = error_logs + "\n * " + line.request_id.name + " / " + line.product_id.name + " / related to " + line.bid_id.name
        if error_logs:
            raise Warning("The following PR are already linked to another bid: " + error_logs)
        if pr_line_new_ids:
            pr_related_ids.write({'bid_id': bid_id})
            pr_line_ids = material_line_obj.search([('bid_id', '=', bid_id), ('id', 'not in', pr_line_new_ids)])
        else:
            pr_line_ids = material_line_obj.search([('bid_id', '=', bid_id)])
        if pr_line_ids:
            pr_line_ids.write({'bid_id': False})

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('purchase.bid') or '/'
        res = super(PurchaseBid, self).create(values)
        if 'pr_related_ids' in values:
            self.validate_related_pr(res.id, values['pr_related_ids'][0][2], "create")
        res.onchange_company_code()
        return res

    def write(self, values):
        res = super(PurchaseBid, self).write(values)
        if 'pr_related_ids' in values:
            self.validate_related_pr(self.id, values['pr_related_ids'][0][2], "write")
        return res

    def action_confirm(self):
        if not self.vendor_line:
            raise Warning("No vendors provided, kindly update bidders tab to proceed.")
        if not self.deadline_of_submission:
            raise Warning("Sorry, you cannot proceed without deadline of submission.")
        if not self.document_requirement_id:
            raise Warning("Sorry, you cannot proceed without document requirement.")
        default_evaluation_line = [(0, 0, line._prepare_evaluation_criteria('technical')) for line in
                                   self.evaluation_line]
        default_commercial_line = [(0, 0, line._prepare_evaluation_criteria('commercial')) for line in
                                   self.commercial_evaluation_line]
        for vendor_line in self.vendor_line:
            vendor_line.write({
                'deadline_of_submission': self.deadline_of_submission,
                'technical_valuation_weight': self.technical_valuation_weight,
                'commercial_valuation_weight': self.commercial_valuation_weight,
                'evaluation_line': default_evaluation_line,
                'commercial_evaluation_line': default_commercial_line,
            })
        self.write({
            'confirmed_by': self._uid,
            'confirmed_date': datetime.now(),
            'document_reminder_date': (self.bid_opening_date - timedelta(days=2)).date(),
            'state': 'waiting_for_verification',
        })

    def action_verify(self):
        self.verified_by = self._uid
        self.verified_date = datetime.now()
        self.state = 'waiting_for_approval'

    def action_approve(self):
        if not self.assigned_evaluator_line:
            raise Warning("Please assign evaluator/s.")
        self.approved_by = self._uid
        self.approved_date = datetime.now()
        self.state = 'send_bid_invitation'

    def action_force_initiate_prebid(self):
        sent_bid_cnt = 0
        for line in self.vendor_line:
            if not line.is_kicked and line.invitation == 'sent':
                sent_bid_cnt += 1
        if sent_bid_cnt >= 2:
            self.state = 'pre_bidding'
        else:
            raise Warning("Two(2) or more bidders are required on sending bid invitation.")

    def action_force_postbid(self):
        accepted_cnt = 0
        for line in self.vendor_line:
            if not line.is_kicked and line.acceptance == 'accepted':
                accepted_cnt += 1
        if accepted_cnt < 2:
            raise Warning("Must check, there should be atleast two vendor accepted.")
        self.state = 'post_bidding'
        self.assign_evaluators()

    def action_bid_selection(self):
        for vline in self.vendor_line:
            if not vline.is_kicked and vline.acceptance == 'accepted':
                for line in vline.evaluator_line:
                    for ln in line.evaluation_line:
                        if not ln.display_type and ln.score == 0:
                            raise Warning("Must check, all qualified bidders must be evaluated before moving the stage to bid selections.")
        bidders_highest_score = self.env['purchase.bid.vendor'].search(
                                       [('bid_id', '=', self.id),
                                       ('is_kicked', '=', False),
                                       ('acceptance', '=', 'accepted')],
                                       limit=1, order='overall_score desc')
        if bidders_highest_score[:1]:
            self.vendor_id = bidders_highest_score.id
        self.state = 'bid_selection'

    def action_submit_to_verify_bid_selection(self):
        self.state = 'waiting_bid_selection_ver'

    def action_verify_bid_selection(self):
        self.bs_verified_by = self._uid
        self.bs_verified_date = datetime.now()
        self.state = 'waiting_bid_selection_con'

    def action_confirm_bid_selection(self):
        self.bs_confirmed_by = self._uid
        self.bs_confirmed_date = datetime.now()
        self.state = 'waiting_bid_selection_app'

    def action_approve_bid_selection(self):
        # If accredited open wizard for file attachment.
        if self.vendor_id.partner_id.accredited and self.vendor_id.partner_id.end_date > fields.Date.today():
            return {
                'type': 'ir.actions.act_window',
                'name': _('Bid Selection Approval'),
                'res_model': 'admin.bid.selection.approval',
                'target': 'new',
                'view_mode': 'form',
                'context': {'default_bid_id': self.id},
            }
        else:
            # If selected vendor is not yet accredited.
            # Send notif to awarded and not awarded bidders.
            for line in self.vendor_line:
                if not line.is_kicked and line.state not in ['bidding_cancel','cancel','decline','no_response']:
                    line.state = 'done'
                    if line.id == self.vendor_id.id:
                        m_subject = 'Bid Result - Successful Bidder'
                        line.send_admin_email_notif('bid_winner_unaccredited', m_subject, line.partner_id.email, 'purchase.bid.vendor')
                    else:
                        m_subject = 'Bid Result - Unsuccessful Bidder'
                        line.send_admin_email_notif('bid_not_winner', m_subject, line.partner_id.email, 'purchase.bid.vendor')
            self.write({
                'bs_approved_by': self._uid,
                'bs_approved_date': datetime.now(),
                'state': 'done',
            })

    def action_create_contract_agreement(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Contract/Agreement'),
            'res_model': 'create.contract.agreement',
            'target': 'new',
            'view_mode': 'form',
        }

    def action_view_vendor(self):
        self.ensure_one()
        document_requirement_ids = [line.id for line in self.document_requirement_id]
        return {
            'name': _('Bidders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.bid.vendor',
            'domain': [('id', 'in', [line.id for line in self.vendor_line])],
            'target': 'current',
            'context': {
                'default_bid_id': self.id,
                'default_deadline_of_submission': self.deadline_of_submission,
                'default_technical_valuation_weight': self.technical_valuation_weight,
                'default_commercial_valuation_weight': self.commercial_valuation_weight,
                'default_evaluation_line': [(0, 0, line._prepare_evaluation_criteria('technical')) for line in
                                            self.evaluation_line],
                'default_commercial_evaluation_line': [(0, 0, line._prepare_evaluation_criteria('commercial')) for line
                                                       in self.commercial_evaluation_line],
                'default_document_requirement_available_id': [(6, 0, document_requirement_ids)],
            },
        }

    @api.model
    def _pre_bidding(self):
        current_datetime = datetime.now()
        records = self.search([
            ('state', 'in', ['send_bid_invitation', 'invitation_sent']),
            ('bid_opening_date', '<=', current_datetime),
        ])
        for rec in records:
            sent_bid_cnt = 0
            invitation_not_sent = 0
            for line in rec.vendor_line:
                if not line.is_kicked and line.invitation == 'sent':
                    sent_bid_cnt += 1
                if not line.is_kicked and line.state == 'draft':
                    invitation_not_sent += 1
            if sent_bid_cnt >= 2 and not invitation_not_sent:
                rec.state = 'pre_bidding'

    @api.model
    def _post_bidding(self):
        records = self.search([
            ('state', '=', 'pre_bidding'),
            ('bid_closing_date', '<=', datetime.now()),
        ])
        for rec in records:
            accepted_cnt = 0
            for line in rec.vendor_line:
                if not line.is_kicked and line.acceptance == 'accepted':
                    accepted_cnt += 1
            if accepted_cnt >= 2:
                rec.state = 'post_bidding'
                rec.assign_evaluators()

    @api.model
    def _update_no_response_vendor(self):
        bid_state = ['send_bid_invitation','invitation_sent','pre_bidding','halted']
        records = self.sudo().search([('state', 'in', bid_state),('deadline_of_confirmation', '<=', datetime.now())])
        for rec in records:
            for line in self.env['purchase.bid.vendor'].sudo().search([('bid_id', '=', rec.id), ('state', '=', 'waiting_for_acceptance')]):
                line.state = 'no_response'

    @api.model
    def _resume_bidding(self):
        records = self.search([
            ('state', '=', 'halted'),
            ('date_resume', '<=', fields.Date.today()),
        ])
        for rec in records:
            rec.state = 'pre_bidding'
            for line in rec.vendor_line:
                if not line.is_kicked and line.state not in ['decline', 'cancel']:
                    line.state = line.previous_status

    @api.model
    def _document_submission_reminder(self):
        records = self.search([
            ('state', 'in', ['send_bid_invitation', 'invitation_sent']),
            ('document_reminder_date', '=', fields.Date.today()),
        ])
        for rec in records:
            requirement = rec.document_requirement_id
            for line in rec.vendor_line:
                submitted_req = line.document_requirement_id
                if not line.is_kicked and line.acceptance == 'accepted':
                    if len(requirement) != len(submitted_req):
                        diff = list(set(requirement) - set(submitted_req))
                        req_to_submit = ""
                        for ln in diff:
                            req_to_submit = req_to_submit + ln.name + "<br/>"
                        mail_body = "<p>Dear " + line.partner_id.name + ",<br/><br/> Kindly send the following requirements that are needed to proceed in Pre-Bidding: <br/>" + req_to_submit + "<br/><br/>Thank you very much.</p>"
                        mail_values = {
                            'subject': 'Follow Up Incomplete Document Requirements for Bidding (' + rec.name + ')',
                            'email_to': line.email or line.partner_id.email,
                            'body_html': mail_body,
                            'model': 'purchase.bid.vendor',
                            'res_id': line.id,
                        }
                        self.env['mail.mail'].create(mail_values).send()

    def get_bidders_comparison(self):
        bidders_dictionary = {}
        bidders_description = []
        bidders_description_dict = {}
        bidders_term = []
        bidders_term_dict = {}
        bidders_negotiated_amt = []
        bidders_leadtime = []
        sv_bidder_description = []
        sv_bidder_terms = []
        bidders_cnt = 0
        bidders_name = []
        bidders_empty_col = '<td></td>'
        top_bidders = self.env['purchase.bid.vendor'].search(
            [('bid_id', '=', self.id), ('id', '!=', self.vendor_id.id), ('is_kicked', '=', False),
             ('acceptance', '=', 'accepted')], limit=2, order='overall_score desc')

        for line in top_bidders:
            ln_bidder_description = []
            ln_bidder_terms = []
            bidders_cnt += 1
            bidders_empty_col = bidders_empty_col + '<td></td>'
            for line_desc in line.bid_summary_line:
                ln_bidder_description.append(
                    [line_desc.name, line_desc.amount and "Php {:,.2f}".format(line_desc.amount) or 'N/A'])
                if line_desc.name not in bidders_description:
                    bidders_description.append(line_desc.name)
                    bidders_description_dict[line_desc.name] = []
                bidders_description_dict[line_desc.name].append(
                    {bidders_cnt: line_desc.amount and "Php {:,.2f}".format(line_desc.amount) or 'N/A'})

            for line_terms in line.terms_of_payment_line:
                ln_bidder_terms.append(
                    [line_terms.name, line_terms.payment_percent and str(line_terms.payment_percent) + '%' or 'N/A'])
                if line_terms.name not in bidders_term:
                    bidders_term.append(line_terms.name)
                    bidders_term_dict[line_terms.name] = []
                bidders_term_dict[line_terms.name].append(
                    {bidders_cnt: line_terms.payment_percent and str(line_terms.payment_percent) + '%' or 'N/A'})

            bidders_name.append(line.partner_id.name)
            bidders_dictionary[line.id] = {
                'name': line.partner_id.name,
                'description': ln_bidder_description,
                'lead_time': line.lead_time or 'N/A',
                'terms': ln_bidder_terms,
                'negotiated_amount': line.negotiated_amount and "Php {:,.2f}".format(line.negotiated_amount) or 'N/A'
            }
            bidders_negotiated_amt.append(
                line.negotiated_amount and "Php {:,.2f}".format(line.negotiated_amount) or 'N/A')
            bidders_leadtime.append(str(line.lead_time) or 'N/A')
        bidders_cnt += 1
        for line_desc in self.vendor_id.bid_summary_line:
            sv_bidder_description.append(
                [line_desc.name, line_desc.amount and "Php {:,.2f}".format(line_desc.amount) or 'N/A'])
            if line_desc.name not in bidders_description:
                bidders_description.append(line_desc.name)
                bidders_description_dict[line_desc.name] = []
            bidders_description_dict[line_desc.name].append(
                {bidders_cnt: line_desc.amount and "Php {:,.2f}".format(line_desc.amount) or 'N/A'})

        for line_terms in self.vendor_id.terms_of_payment_line:
            sv_bidder_terms.append(
                [line_terms.name, line_terms.payment_percent and str(line_terms.payment_percent) + '%' or 'N/A'])
            if line_terms.name not in bidders_term:
                bidders_term.append(line_terms.name)
                bidders_term_dict[line_terms.name] = []
            bidders_term_dict[line_terms.name].append(
                {bidders_cnt: line_terms.payment_percent and str(line_terms.payment_percent) + '%' or 'N/A'})

        bidders_name.append(self.vendor_id.partner_id.name)
        bidders_dictionary[self.vendor_id.id] = {
            'name': self.vendor_id.partner_id.name,
            'description': sv_bidder_description,
            'lead_time': self.vendor_id.lead_time or 'N/A',
            'terms': sv_bidder_terms,
            'negotiated_amount': "Php {:,.2f}".format(self.vendor_id.negotiated_amount) or 'N/A'
        }
        bidders_leadtime.append(str(self.vendor_id.lead_time) or 'N/A')
        bc_datas = '<thead><tr><td colspan="2"></td><td colspan="%d" >BIDDERS</td>' % bidders_cnt
        bc_datas = bc_datas + '<thead><tr><td>a. Description</td><td>Bid description</td>'
        # Display vendors name
        for b_name in bidders_name:
            bc_datas = bc_datas + '<td>%s</td>' % b_name
        bc_datas = bc_datas + '</tr></thead><tbody>'
        # Display bid description
        desc_cnt = 1
        for b_desc in bidders_description:
            if desc_cnt == 1:
                bc_datas = bc_datas + '<tr><td rowspan="%s"></td><td>%s</td>' % (
                str(len(bidders_description) + 1), b_desc)
            else:
                bc_datas = bc_datas + '<tr><td>%s</td>' % b_desc
            desc_cnt += 1
            b_cnt = 1
            while b_cnt <= bidders_cnt:
                desc_amount = 'N/A'
                for ln in bidders_description_dict[b_desc]:
                    if b_cnt in ln:
                        desc_amount = ln[b_cnt]
                bc_datas = bc_datas + '<td>%s</td>' % desc_amount
                b_cnt += 1
            bc_datas = bc_datas + '</tr>'
        # Display Negotiated Amount (Gross)
        bc_datas = bc_datas + '<tr class="tr-bold"><td>Negotiated Amount (Gross)</td>'
        for b_negotiated_amt in bidders_negotiated_amt:
            bc_datas = bc_datas + '<td>%s</td>' % b_negotiated_amt
        bc_datas = bc_datas + '<td style="background-color: #FFFF00">%s</td>' % "Php {:,.2f}".format(
            self.vendor_id.negotiated_amount) or 'N/A'
        bc_datas = bc_datas + '</tr>'
        # Display Leadtime
        bc_datas = bc_datas + '<tr class="tr-bold"><td rowspan="2">b. Leadtime</td><td>Required</td>' + bidders_empty_col + '</tr>'
        bc_datas = bc_datas + '<tr><td></td>'
        for b_lead in bidders_leadtime:
            bc_datas = bc_datas + '<td>%s</td>' % b_lead
        bc_datas = bc_datas + '</tr>'
        # Display Terms of Payment
        bc_datas = bc_datas + '<tr><td class="txt-bold" rowspan="%s">' % str(len(bidders_term) + 1)
        bc_datas = bc_datas + 'c. Terms of Payment</td><td class="txt-bold">Downpayment (in Peso)</td>' + bidders_empty_col + '</tr>'
        for b_term in bidders_term:
            bc_datas = bc_datas + '<tr><td>%s</td>' % b_term
            b_cnt = 1
            while b_cnt <= bidders_cnt:
                percent = 'N/A'
                for ln in bidders_term_dict[b_term]:
                    if b_cnt in ln:
                        percent = ln[b_cnt]
                bc_datas = bc_datas + '<td>%s</td>' % percent
                b_cnt += 1
            bc_datas = bc_datas + '</tr>'
        bc_datas = bc_datas + '</tbody>'
        return bc_datas

    def assign_evaluators(self):
        evaluator_values = []
        self = self.with_context(create_evaluator=True)
        for line in self.assigned_evaluator_line:
            evaluator_values.append({
                'evaluator_id': line.user_id.id,
                'type': line.type,
                'bid_id': self.id})
        for ln in self.vendor_line:
            if not ln.is_kicked and ln.invitation == 'sent':
                for v in evaluator_values:
                    v['vendor_bid_id'] = ln.id
                    new_evaluator = self.env['vendor.evaluator'].create(v)
                    new_evaluator._onchange_type()
                    m_subject = 'Evaluation Reminder for Bid: '+ self.name +', Vendor: '+ln.partner_id.name
                    new_evaluator.send_admin_email_notif('bid_evaluation', m_subject, new_evaluator.evaluator_id.email, 'vendor.evaluator')

    def action_view_events(self):
        self.ensure_one()
        return {
            'name': _('Events'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,calendar,tree,form,pivot',
            'res_model': 'event.event',
            'domain': [('bid_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_bid_id': self.id,
            },
        }

    def action_halt(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Halt Bidding'),
            'res_model': 'halt.bidding',
            'target': 'new',
            'view_mode': 'form',
            'context': {'default_bid_closing_date': self.bid_closing_date},
        }

    def action_resume(self):
        self.state = 'pre_bidding'
        for line in self.vendor_line:
            if not line.is_kicked and line.state not in ['decline', 'cancel']:
                line.action_resume()

    @api.constrains('bid_opening_date', 'bid_closing_date', 'date_created')
    def _validate_date(self):
        for rec in self:
            if rec.bid_opening_date:
                if rec.bid_opening_date < rec.date_created:
                    raise Warning("Opening date should be on or after creation date!")
                elif rec.bid_closing_date and (rec.bid_closing_date < rec.bid_opening_date or rec.bid_closing_date < rec.date_created):
                    raise Warning("Closing date should be on or after opening and creation dates!")
                elif rec.bid_closing_date and rec.bid_opening_date.date() == rec.bid_closing_date.date():
                    raise ValidationError("Bid closing date should not be equal to bid opening date!")


class PurchaseBidVendor(models.Model):
    _name = "purchase.bid.vendor"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'admin.email.notif']
    _description = "Bid Vendor"
    _order = "id desc"

    def _compute_evaluator_count(self):
        for rec in self:
            self.evaluator_count = len(rec.evaluator_line)

    def _get_evaluator_comments(self):
        for record in self:
            self.evaluator_comment_line = self.evaluator_line.search(
                [('other_comments', '!=', False), ('vendor_bid_id', '=', record.id)])

    def _compute_negotiated_amount_in_words(self):
        for record in self:
            record.negotiated_amount_in_words = num2words(record.negotiated_amount).title()

    name = fields.Char(related='partner_id.name', string='Name')
    bid_id = fields.Many2one('purchase.bid', 'Bid', ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string='Vendors', required=True, track_visibility='onchange')
    contact_id = fields.Many2one('res.partner', string='Contact Person', domain="[('id', 'child_of', partner_id)]",
                                 track_visibility='onchange')
    invitation = fields.Selection(selection=[('draft', 'Draft'), ('sent', 'Sent')], string='Invitation',
                                  default='draft', track_visibility='onchange', copy=False)
    acceptance = fields.Selection(selection=_ACCEPTANCE, string='Acceptance', track_visibility='onchange', copy=False)
    acceptance_date = fields.Datetime(string='Acceptance Date', track_visibility='onchange', copy=False)
    phone = fields.Char(string='Phone', track_visibility='onchange')
    mobile = fields.Char(string='Mobile', track_visibility='onchange')
    email = fields.Char(string='Email', track_visibility='onchange')
    prebid_attendance = fields.Boolean(string='Pre-bid Meeting Attendance', track_visibility='onchange', copy=False)
    date_attended = fields.Date(string='Date Attended', track_visibility='onchange', copy=False)
    non_disc_agreement = fields.Boolean(string='Non-disclosure Agreement', track_visibility='onchange', copy=False)
    date_aggreed = fields.Date(string='Date Aggreed', track_visibility='onchange', copy=False)
    bid_state = fields.Selection(related='bid_id.state')
    project_name = fields.Char(related='bid_id.project_name')
    project_location = fields.Char(related='bid_id.project_location')
    scope_of_work = fields.Char(related='bid_id.scope_of_work')
    scope_of_work_remark = fields.Text(related='bid_id.scope_of_work_remark')
    purchasing_officer = fields.Many2one(related='bid_id.purchasing_officer')
    bid_opening_date = fields.Datetime(related='bid_id.bid_opening_date')
    bid_closing_date = fields.Datetime(related='bid_id.bid_closing_date')
    company_id = fields.Many2one(related='bid_id.company_id', store=True)
    is_kicked = fields.Boolean(string='Kicked', copy=False)
    kick_out_reason = fields.Text('Kick out reason', copy=False)
    document_requirement_id = fields.Many2many('document.requirement', 'document_id_selection', 'document_id',
                                               string='Pre-bid Documents')
    document_requirement_available_id = fields.Many2many(related='bid_id.document_requirement_id',
                                                         string='Pre-bid Documents Available')
    deadline_of_submission = fields.Date(string='Deadline of Submission', track_visibility='onchange', copy=False)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    # Evaluation
    evaluator_line = fields.One2many('vendor.evaluator', 'vendor_bid_id', string='Evaluator Line')
    evaluator_count = fields.Integer(compute='_compute_evaluator_count', string='Evaluator Count')
    evaluation_line = fields.One2many('vendor.evaluation.line', 'vendor_bid_id', string='Technical Evaluation',
                                      domain=[('type', '=', 'technical')], copy=False)
    commercial_evaluation_line = fields.One2many('vendor.evaluation.line', 'vendor_bid_id',
                                                 string='Commercial Evaluation', domain=[('type', '=', 'commercial')], copy=False)
    evaluator_comment_line = fields.One2many('vendor.evaluator', string='Other Comments',
                                             compute='_get_evaluator_comments')
    # Bid summary
    for_clarification = fields.Boolean('For clarification', track_visibility='onchange', copy=False)
    for_negotiation = fields.Boolean('For negotiation', track_visibility='onchange', copy=False)
    bid_summary_line = fields.One2many('bid.summary.line', 'vendor_bid_id', string='Bid Summary', copy=False)
    negotiated_amount = fields.Float(string='Negotiated Amount (Gross)', track_visibility='onchange', copy=False)
    negotiated_amount_in_words = fields.Text(compute="_compute_negotiated_amount_in_words",
                                             string='Negotiated Amount (Gross) in Words')
    lead_time = fields.Integer(string='Lead Time', track_visibility='onchange', copy=False)
    terms_of_payment_line = fields.One2many('terms.of.payment.line', 'vendor_bid_id', string='Bid Summary')
    technical_valuation_weight = fields.Float(string="Technical Valuation Weight", track_visibility="always")
    commercial_valuation_weight = fields.Float(string="Commercial Valuation Weight", track_visibility="always", default=1)
    technical_valuation_score = fields.Float(string="Technical Valuation Weight", store=True,
                                             compute="_get_valuation_score")
    commercial_valuation_score = fields.Float(string="Commercial Valuation Weight", store=True,
                                              compute="_get_valuation_score")
    overall_score = fields.Float(string="Overall Evaluation Score", store=True, compute="_get_valuation_score")
    previous_status = fields.Char(string='Previous Status')
    halt_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Halt Reason', track_visibility='always', copy=False)
    halt_description = fields.Text(string='Halt Description', track_visibility='always', copy=False)
    state = fields.Selection(selection=_BIDDER_STATES,
                             string='Bidder Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')

    _sql_constraints = [('bidders_uniq', 'unique(bid_id, partner_id)', 'Bidders(vendor/supplier) must be unique per bidding!'),]

    def action_resume(self):
        self.state = self.previous_status
        m_subject = 'Bidding Resumed: '+ self.bid_id.name
        self.send_admin_email_notif('bid_resumed', m_subject, self.partner_id.email, 'purchase.bid.vendor')

    def action_accept(self):
        if self.bid_id and self.bid_id.deadline_of_confirmation and self.bid_id.deadline_of_confirmation < datetime.now():
            raise ValidationError('Bid has already lapsed the deadline of confirmation, please coordinate with the Purchasing Team.')
        self.write({
            'acceptance': 'accepted',
            'acceptance_date': fields.Date.today(),
            'state': 'bidding_in_progress'
        })

    @api.depends('evaluation_line', 'evaluation_line.weight', 'evaluation_line.score',
                 'commercial_evaluation_line', 'commercial_evaluation_line.weight', 'commercial_evaluation_line.score',
                 'technical_valuation_weight', 'commercial_valuation_weight')
    def _get_valuation_score(self):
        for r in self:
            total_technical_valuation_weight = sum(i.weight for i in r.evaluation_line)
            total_commercial_valuation_weight = sum(i.weight for i in r.commercial_evaluation_line)
            total_technical_valuation_score = sum(
                (i.weight / total_technical_valuation_weight) * i.score if i.weight > 0 and total_technical_valuation_weight > 0 else 0
                for i in r.evaluation_line)
            total_commercial_valuation_score = sum(
                (i.weight / total_commercial_valuation_weight) * i.score if i.weight > 0 and total_commercial_valuation_weight > 0 else 0
                for i in r.commercial_evaluation_line)
            overall_weight = sum([r.technical_valuation_weight, r.commercial_valuation_weight])
            overall_score = r.technical_valuation_weight > 0 and overall_weight and (
                        r.technical_valuation_weight / overall_weight) * total_technical_valuation_score or 0
            overall_score += r.commercial_valuation_weight > 0 and overall_weight and (
                        r.commercial_valuation_weight / overall_weight) * total_commercial_valuation_score or 0
            r.technical_valuation_score = total_technical_valuation_score
            r.commercial_valuation_score = total_commercial_valuation_score
            r.overall_score = overall_score

    @api.onchange('deadline_of_submission')
    def onchange_deadline_of_submission(self):
        if self.deadline_of_submission and self.bid_opening_date:
            if self.deadline_of_submission >= self.bid_opening_date.date():
                raise Warning(
                    "Document Deadline Submission date should not be greater than or equal to bid opening date.")

    def validate_invitation(self):
        bidders_data = self.search([('bid_id', '=', self.bid_id.id), ('is_kicked', '=', False), ('id', '!=', self.id)])
        all_invitation_sent = True
        for line in bidders_data:
            if line.invitation == 'draft':
                all_invitation_sent = False
        if all_invitation_sent:
            self.bid_id.state = 'invitation_sent'

    def write(self, values):
        res = super(PurchaseBidVendor, self).write(values)
        if self.bid_state == 'send_bid_invitation' and ('invitation' in values or 'is_kicked' in values):
            self.validate_invitation()
        return res

    def action_send_invitation(self):
        '''
        This function opens a window to compose an email, with the edi bid template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('admin_purchase_bid', 'email_template_edi_bid')[1]
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        partner_ids = [self.contact_id and self.contact_id.id or self.partner_id.id]
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.bid.vendor',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invitation_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'default_partner_ids': partner_ids,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def get_partner_address(self, without_company=False):
        return self.partner_id._display_address(without_company)

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_invitation_as_sent'):
            self.write({'invitation': 'sent', 'state': 'waiting_for_acceptance', 'acceptance': 'pending'})
        return super(PurchaseBidVendor, self).message_post(**kwargs)

    def action_kick(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reason to remove'),
            'res_model': 'kick.out.reason',
            'target': 'new',
            'view_mode': 'form',
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.phone:
                self.phone = self.partner_id.phone
            if self.partner_id.mobile:
                self.mobile = self.partner_id.mobile
            if self.partner_id.email:
                self.email = self.partner_id.email

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        if self.contact_id:
            if self.contact_id.phone and not self.phone:
                self.phone = self.contact_id.phone
            if self.contact_id.mobile and not self.mobile:
                self.mobile = self.contact_id.mobile
            if self.contact_id.email and not self.email:
                self.email = self.contact_id.email

    def action_view_evaluator(self):
        self.ensure_one()
        return {
            'name': _('Evaluation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'vendor.evaluator',
            'domain': [('vendor_bid_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_vendor_bid_id': self.id,
                'default_type': 'technical',
            },
        }


class KickOutReason(models.TransientModel):
    _name = "kick.out.reason"
    _description = "Reason To Kick Out"

    name = fields.Text("Description", required=True)

    def action_confirm_kick(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].browse(active_id)
        active_entry.write({'kick_out_reason': self.name, 'is_kicked': True})


class HaltBidding(models.TransientModel):
    _name = "halt.bidding"
    _description = "Halt Bidding"

    bid_closing_date = fields.Datetime(string="Bid Closing Date", required=True)
    date_halted = fields.Datetime(string="Date Halted", required=True, default=datetime.now())
    date_resume = fields.Date(string="Date Resume", required=True)
    reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reason', required=True)
    description = fields.Text(string='Description')

    @api.onchange('reason_id')
    def onchange_reason_id(self):
        if self.reason_id:
            self.description = self.reason_id.description

    def action_halt_bidding(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].browse(active_id)
        if self.date_resume >= self.bid_closing_date.date():
            raise Warning("Bid closing date must be greater than date resume.")
        active_entry.write({
            'state': 'halted',
             'bid_closing_date': self.bid_closing_date,
             'date_halted': self.date_halted,
             'date_resume': self.date_resume,
             'halt_reason_id': self.reason_id.id,
             'halt_description': self.description,
        })
        m_subject = 'Bidding Halted: '+ active_entry.name
        for line in active_entry.vendor_line:
            if not line.is_kicked and line.state not in ['decline', 'cancel']:
                line.previous_status = line.state
                line.halt_reason_id = self.reason_id.id
                line.halt_description = self.description
                line.state = 'bidding_halt'
                line.send_admin_email_notif('bid_halted', m_subject, line.partner_id.email, 'purchase.bid.vendor')

class VendorEvaluationLine(models.Model):
    _name = "vendor.evaluation.line"
    _description = "Vendor Evaluation Line"
    _rec_name = 'criteria'

    name = fields.Char(string="Description")
    bid_id = fields.Many2one('purchase.bid', string="Bid", index=True, ondelete='cascade')
    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string="Vendor Bid", index=True, ondelete='cascade')
    default_evaluation_temp_id = fields.Many2one('vendor.evaluation.template', string="Default Evaluation Template",
                                                 index=True, ondelete='cascade')
    criteria = fields.Many2one('evaluation.criteria', string='Criteria')
    weight = fields.Float(string="Weight")
    offer = fields.Float(string="Offer")
    other_remark = fields.Text(string="Other Remarks")
    score = fields.Float(string="Score", compute='_compute_average', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Type')

    @api.depends(
        'vendor_bid_id.evaluator_line',
        'vendor_bid_id.evaluator_line.type',
        'vendor_bid_id.evaluator_line.evaluation_line',
        'vendor_bid_id.evaluator_line.evaluation_line.score')
    def _compute_average(self):
        for rec in self:
            evaluation_ids = self.env['vendor.evaluator.line'].search(
                [('evaluation_id', '=', rec.id), ('display_type', '=', False)])
            score_average = 0
            line_cnt = 0
            for line in evaluation_ids:
                score_average += line.score
                line_cnt += 1
            rec.score = score_average and (score_average / line_cnt) or 0

    @api.onchange('criteria')
    def _onchange_criteria(self):
        if self.criteria:
            self.weight = self.criteria.weight or 0
            self.name = self.criteria.description

    def _prepare_evaluation_criteria(self, type):
        create_evaluator = self.env.context.get('create_evaluator', False)
        create_regular_evaluator = self.env.context.get('create_regular_evaluator', False)
        vendor_bid_id = self.env.context.get('vendor_bid_id', False)
        res = {
            'name': self.name,
            'type': type,
            'weight': self.weight,
            'offer': self.offer,
            'sequence': self.sequence,
            'display_type': self.display_type,
            'criteria': self.criteria and self.criteria.id or False,
        }
        if vendor_bid_id:
            res['vendor_bid_id'] = vendor_bid_id or False
        if create_evaluator:
            res['evaluation_id'] = self.id or False
        if create_regular_evaluator:
            res['regular_evaluation_id'] = self.id or False
        return res

    @api.constrains('weight')
    def _validation_evaluation_line(self):
        for rec in self:
            if rec.criteria and rec.weight < 1:
                raise ValidationError("Weight must be higher or equal to 1.")


class VendorEvaluationTemplate(models.Model):
    _name = "vendor.evaluation.template"
    _description = "Evaluation Template"

    name = fields.Char(string='Name', required=True, default="Default Evaluation Template")
    technical_evaluation_line = fields.One2many('vendor.evaluation.line', 'default_evaluation_temp_id',
                                                string='Technical Evaluation', copy=True,
                                                domain=[('type', '=', 'technical')])
    commercial_evaluation_line = fields.One2many('vendor.evaluation.line', 'default_evaluation_temp_id',
                                                 string='Commercial Evaluation', copy=True,
                                                 domain=[('type', '=', 'commercial')])
    vendor_accreditation = fields.Boolean(string="For Vendor Accreditation")
    document_accreditation_requirement_ids = fields.Many2many('document.requirement',
                                                              'evaluation_template_document_rel', string='Documents')
    technical_valuation_weight = fields.Float(string="Technical Valuation Weight", track_visibility="always",default=1)
    commercial_valuation_weight = fields.Float(string="Commercial Valuation Weight", track_visibility="always", default=1)
    template_purpose = fields.Selection(selection=[
                                        ('bid', 'Bid'),
                                        ('vendor_accreditation', 'Vendor Accreditation'),
                                        ('vendor_regular_evaluation', 'Vendor Regular Evaluation')],
                                        string="Template Purpose", required=True)
    type_of_evaluation = fields.Selection(selection=[
                                        ('monthly', 'Monthly'),
                                        ('quarterly', 'Quarterly'),
                                        ('annual', 'Annual'),
                                        ('semi_annual', 'Semi Annual')],
                                        string="Type of Evaluation")
    assigned_evaluator_line = fields.One2many('assigned.evaluator.line', 'evaluation_template_id', string='Assigned Evaluator', copy=True)
    submission_deadline = fields.Integer(string="Submission Deadline", track_visibility="always", default=1)
    instructions = fields.Html(string="Instructions", readonly=False, track_visibility="always")

    @api.onchange('technical_valuation_weight')
    def onchange_technical_valuation_weight(self):
        if self.technical_valuation_weight < 1:
            self.technical_evaluation_line.unlink()
            self.technical_valuation_weight = 0

    @api.onchange('commercial_valuation_weight')
    def onchange_commercial_valuation_weight(self):
        if self.commercial_valuation_weight < 1:
            self.commercial_evaluation_line.unlink()
            self.commercial_valuation_weight = 0

    @api.onchange('template_purpose')
    def onchange_template_purpose(self):
        if self.template_purpose:
            if self.template_purpose == 'vendor_accreditation':
                self.vendor_accreditation = True
            else:
                self.vendor_accreditation = False
            if self.template_purpose != 'vendor_regular_evaluation':
                self.type_of_evaluation = False
        else:
            self.vendor_accreditation = False

    @api.constrains('vendor_accreditation')
    def check_existing_template_for_vendor_accreditation(self):
        if self.search_count([('vendor_accreditation', '=', True)]) > 1:
            raise ValidationError(_("You have existing Vendor Accreditation template, please edit that instead."))

    @api.constrains('technical_evaluation_line', 'commercial_evaluation_line', 'technical_valuation_weight', 'commercial_valuation_weight')
    def _validate_weight_and_criteria(self):
        for rec in self:
            if rec.technical_valuation_weight < 1 and rec.commercial_valuation_weight < 1:
                raise Warning("Either technical or commercial evaluation weight must be greater than zero!")
            else:
                if not rec.technical_evaluation_line and not rec.commercial_evaluation_line:
                    raise Warning("There should be atleast either commercial or technical evaluation criteria defined!")

    @api.model
    def create(self, values):
        res = super(VendorEvaluationTemplate, self).create(values)
        return res


class VendorEvaluator(models.Model):
    _name = "vendor.evaluator"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", 'admin.email.notif']
    _description = "Vendor Evaluation"

    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string="Vendor Bid", index=True, ondelete='cascade')
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, required=True)
    other_comments = fields.Text('Other Comments')
    name = fields.Char(related='evaluator_id.name', string='Name')
    bid_id = fields.Many2one(related='vendor_bid_id.bid_id')
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Evaluation Type',
                            required=True)
    evaluation_line = fields.One2many('vendor.evaluator.line', 'vendor_evaluation_id', string='Evaluation', copy=True)

    @api.model
    def create(self, vals):
        # Adding context mail_create_nosubscribe to prevent error "Error, a partner cannot follow twice the same object".
        # It is because everytime we create new evaluator we also send email notif at the same time we post the notif in threads but the default function of odoo is if we create new entry it will post a message in threads and thats the reason of this error.
        self = self.with_context(mail_create_nosubscribe=True)
        res = super(VendorEvaluator,self).create(vals)
        return res

    @api.onchange('type')
    def _onchange_type(self):
        eval_type = self.type
        if self.evaluation_line:
            self.evaluation_line.unlink()
        if eval_type:
            for rec in self.vendor_bid_id:
                default_eval_entries = rec.evaluation_line
                if eval_type == "commercial":
                    default_eval_entries = rec.commercial_evaluation_line
                self.evaluation_line = [
                    (0, 0, line._prepare_evaluation_criteria(eval_type))
                    for line in default_eval_entries
                ]
        self.type = eval_type


class VendorEvaluationLine(models.Model):
    _name = "vendor.evaluator.line"
    _description = "Vendor Evaluation Line"

    name = fields.Char(string="Description")
    vendor_evaluation_id = fields.Many2one('vendor.evaluator', string="Evaluator", index=True, ondelete='cascade')
    evaluator_id = fields.Many2one(related='vendor_evaluation_id.evaluator_id', store=True)
    vendor_bid_id = fields.Many2one(related='vendor_evaluation_id.vendor_bid_id', store=True)
    evaluation_id = fields.Many2one('vendor.evaluation.line', string='Vendor Evaluation Line')
    criteria = fields.Many2one('evaluation.criteria', string='Criteria')
    weight = fields.Float(string="Weight")
    offer = fields.Float(string="Offer")
    score = fields.Float(string="Score")
    other_remark = fields.Text(string="Other Remarks")
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Type')


class EvaluationCriteria(models.Model):
    _name = "evaluation.criteria"
    _description = "Evaluation Criteria"
    _order = "name asc"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
    weight = fields.Float(string="Weight")


class BidSummaryLine(models.Model):
    _name = "bid.summary.line"
    _description = "Bid Summary Line"

    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string='Bid Vendor', required=True, ondelete="cascade")
    name = fields.Char(string='Bid Description', required=True)
    amount = fields.Float(string='Amount')


class TermsOfPaymentLine(models.Model):
    _name = "terms.of.payment.line"
    _description = "Terms of Payment Line"

    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string='Bid Vendor')
    name = fields.Char(string='Description', required=True)
    payment_percent = fields.Float(string='(%)')


class CreateContractAgreement(models.TransientModel):
    _name = "create.contract.agreement"
    _description = "Create a Contract/Agreement"

    inclusion_line = fields.One2many('contracts.and.agreements.inclusion.wizard', 'contracts_agreement_wizard',
                                     string='Inclusion')

    def create_contract_agreement(self):
        context = self.env.context
        bid_data = self.env['purchase.bid'].browse(context['active_id'])
        contract_id = self.env['contracts.and.agreements'].create({
            'bid_id': bid_data.id,
            'partner_id': bid_data.vendor_id.partner_id.id,
            'contract_agreement_name': bid_data.project_name,
            'purchasing_officer': bid_data.purchasing_officer and bid_data.purchasing_officer.id or False,
            'total_con_agreement_amt': bid_data.vendor_id.negotiated_amount,
            'inclusion_line': [
                (0, 0, {'product_id': line.product_id.id, 'quantity': line.quantity, 'price': line.price}) for line in
                self.inclusion_line],
            'start_date': bid_data.start_date,
            'end_date': bid_data.end_date,
            'state': 'approved',
            'created_by': self._uid,
            'verified_by': self._uid,
            'approved_by': self._uid,
            'created_date': fields.Date.today(),
            'verified_date': fields.Date.today(),
            'approved_date': fields.Date.today(),
        })
        bid_data.agreement_contract_no = contract_id
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Contract/Agreement created.',
                'type': 'rainbow_man',
            }
        }


class ContractsAndAgreementsWizard(models.TransientModel):
    _name = "contracts.and.agreements.inclusion.wizard"
    _description = "Contracts and Agreements Inclusion Wizard"

    contracts_agreement_wizard = fields.Many2one('create.contract.agreement', string='Contract/Agreement Wizard')
    product_id = fields.Many2one('product.product', 'Material', required=True)
    quantity = fields.Float('Quantity')
    price = fields.Float('Price')

class AssignedEvaluatorLine(models.Model):
    _name = "assigned.evaluator.line"
    _description = "Assigned Evaluator Line"

    evaluation_template_id = fields.Many2one('vendor.evaluation.template', 'Evaluation Template')
    bid_id = fields.Many2one('purchase.bid', 'Bid')
    user_id = fields.Many2one('res.users', string='Evaluator', required=True)
    type = fields.Selection([('commercial', 'Commercial'), ('technical', 'Technical')], string='Type', required=True, default='technical')

    def _prepare_evaluation_evaluator(self):
        res = {
            'user_id': self.user_id.id,
            'type': self.type,
        }
        return res
