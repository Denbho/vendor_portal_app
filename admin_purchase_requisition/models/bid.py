# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime,date
from odoo.exceptions import Warning

_STATES = [
    ('draft', 'Draft'),
    ('waiting_for_verification', 'Waiting for Verification'),
    ('waiting_for_approval', 'Waiting for Approval'),
    ('send_bid_invitation', 'Sending Bid Invitation'),
    ('pre_bidding', 'Pre-Bidding'),
    ('post_bidding', 'Post-Bidding'),
    ('bid_selection', 'Bid Selection'),
    ('waiting_bid_selection_ver', 'Waiting for Bid Selection Verification'),
    ('waiting_bid_selection_con', 'Waiting for Bid Selection Confirmation'),
    ('waiting_bid_selection_app', 'Waiting for Bid Selection Approval'),
    ('done', 'Done'),
    ('cancel', 'Cancelled')
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
    _order = 'id desc'

    def _compute_vendor_count(self):
        for record in self:
            record.vendor_count = len([line.id for line in record.vendor_line])

    def _default_technical_evaluation_line(self):
        res = []
        default_template_data = self.env['vendor.evaluation.template'].search([], limit=1)
        for rec in default_template_data:
            res = [
                (0, 0, line._prepare_evaluation_criteria('technical'))
                for line in rec.technical_evaluation_line
            ]
        return res

    def _default_commercial_evaluation_line(self):
        res = []
        default_template_data = self.env['vendor.evaluation.template'].search([], limit=1)
        for rec in default_template_data:
            res = [
                (0, 0, line._prepare_evaluation_criteria('commercial'))
                for line in rec.commercial_evaluation_line
            ]
        return res

    def _compute_check_date_prebid_postbid(self):
        for rec in self:
            rec.check_date_prebid_postbid = True
            current_datetime = datetime.now()
            if rec.state == 'send_bid_invitation' and rec.invitation_sent:
                if rec.bid_opening_date and current_datetime >= rec.bid_opening_date:
                    rec.state = 'pre_bidding'
            if rec.state == 'pre_bidding':
                if rec.bid_closing_date and current_datetime >= rec.bid_closing_date:
                    rec.state = 'post_bidding'

    name = fields.Char(string='Bid', required=True, copy=False, default=lambda self: _('New'), readonly=True)
    bid_ref = fields.Char(string='Bid Ref. No.')
    bid_name = fields.Char(string='Bid Name')
    pr_id = fields.Many2one('admin.purchase.requisition', 'PR No.')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    date_created = fields.Date(string="Bid Creation Date", default=fields.Date.today())
    purchasing_officer = fields.Many2one('res.users', string='Purchasing Officer')
    bid_opening_date = fields.Datetime(string="Bid Opening Date")
    bid_closing_date = fields.Datetime(string="Bid Closing Date")
    wbs_budget = fields.Float(string="WBS (Budget)")
    bom_budget = fields.Float(string="BOM (Budget)")
    price_ceiling = fields.Float(string="Price Ceiling")
    target_price = fields.Float(string="Target Price")
    vendor_id = fields.Many2one('purchase.bid.vendor', string='Selected Vendor', domain="[('bid_id', '=', id),('is_kicked','=', False),('acceptance','=', 'accepted')]")
    date_selected = fields.Date(string='Date')
    agreement_contract_no = fields.Many2one('contracts.and.agreements', string='Agreement/Contract No.')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    scope_of_work = fields.Char(string='Scope of Work', required=True)
    scope_description = fields.Text(string="Scope of Work Description")
    scope_line = fields.One2many('purchase.bid.scope.of.work', 'bid_id', string='Scope of Work', copy=True)
    vendor_line = fields.One2many('purchase.bid.vendor', 'bid_id', string='Vendors', copy=True)
    evaluation_line = fields.One2many('vendor.evaluation.line', 'bid_id', string='Technical Evaluation', copy=True, default=_default_technical_evaluation_line, domain=[('type', '=', 'technical')])
    commercial_evaluation_line = fields.One2many('vendor.evaluation.line', 'bid_id', string='Commercial Evaluation', copy=True, default=_default_commercial_evaluation_line, domain=[('type', '=', 'commercial')])
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    invitation_acceptance = fields.Boolean(compute='_compute_invitation_acceptance', string='Invitation Acceptance', store=True)
    invitation_sent = fields.Boolean(string='Invitation Sent', copy=False)
    vendor_count = fields.Integer(compute='_compute_vendor_count', string='Vendor Count')
    check_date_prebid_postbid = fields.Boolean(compute='_compute_check_date_prebid_postbid', string='Check date for Pre-Bid & Post-Bid')
    pre_bid_documents_id = fields.Many2many('pre.bid.documents', string='Pre-bid Documents')
    state = fields.Selection(selection=_STATES,
                             string='Bid Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft',)
                             # track_visibility='always')

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

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('purchase.bid') or '/'
        res = super(PurchaseBid, self).create(values)
        return res

    def action_confirm(self):
        return self.write({'state': 'waiting_for_verification'})

    def action_verify(self):
        return self.write({'state': 'waiting_for_approval'})

    def action_approve(self):
        return self.write({'state': 'send_bid_invitation'})

    def action_force_initiate_prebid(self):
        return self.write({'state': 'pre_bidding'})

    def action_force_postbid(self):
        return self.write({'state': 'post_bidding'})

    def action_bid_selection(self):
        return self.write({'state': 'bid_selection'})

    def action_submit_to_verify_bid_selection(self):
        return self.write({'state': 'waiting_bid_selection_ver'})

    def action_verify_bid_selection(self):
        return self.write({'state': 'waiting_bid_selection_con'})

    def action_confirm_bid_selection(self):
        return self.write({'state': 'waiting_bid_selection_app'})

    def action_approve_bid_selection(self):
        if not self.vendor_id:
            raise Warning('Please assign Selected Vendor.')
        return self.write({'state': 'done'})

    def action_create_contract_agreement(self):
        contract_id = self.env['contracts.and.agreements'].create({
            'bid_id': self.id,
            'partner_id': self.vendor_id.partner_id.id,
            'contract_agreement_name': self.bid_name,
            'purchasing_officer': self.purchasing_officer and self.purchasing_officer.id or False,
            'total_con_agreement_amt': self.vendor_id.negotiated_amount,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'state': 'approved',
            'created_by': self._uid,
            'verified_by': self._uid,
            'approved_by': self._uid,
            'created_date': fields.Date.today(),
            'verified_date': fields.Date.today(),
            'approved_date': fields.Date.today(),
        })
        self.agreement_contract_no = contract_id
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Contract/Agreement created.',
                'type': 'rainbow_man',
            }
        }

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_view_vendor(self):
        self.ensure_one()
        pre_bid_doc_ids = [line.id for line in self.pre_bid_documents_id]
        return {
            'name': _('Vendors'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.bid.vendor',
            'domain': [('id','in', [line.id for line in self.vendor_line])],
            'target': 'current',
            'context': {
                'default_bid_id': self.id,
                'default_evaluation_line': [(0, 0, line._prepare_evaluation_criteria('technical')) for line in self.evaluation_line],
                'default_commercial_evaluation_line': [(0, 0, line._prepare_evaluation_criteria('commercial')) for line in self.commercial_evaluation_line],
                'default_pre_bid_documents_available_id': [(6, 0, pre_bid_doc_ids)],
            },
        }

    def action_send_invitation(self):
        '''
        This function opens a window to compose an email, with the edi bid template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('admin_purchase_requisition', 'email_template_edi_bid')[1]
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        partner_ids = []
        for line in self.vendor_line:
            if not line.is_kicked:
                partner_ids.append(line.partner_id.id)

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.bid',
            'active_model': 'purchase.bid',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_invitation_as_sent': True,
            'model_description': 'Bids',
            'default_partner_ids': partner_ids,
        })

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_invitation_as_sent'):
            self.write({'invitation_sent': True})
            for line in self.vendor_line:
                if not line.is_kicked:
                    line.write({'invitation': 'sent', 'acceptance': 'pending'})
        return super(PurchaseBid, self).message_post(**kwargs)

class ContractsAndAgreements(models.Model):
    _inherit = "contracts.and.agreements"

    bid_id = fields.Many2one('purchase.bid', 'Bid Ref.')

class PurchaseBidScopeOfWork(models.Model):
    _name = "purchase.bid.scope.of.work"
    _description = "Bid Scope of Work"
    _order = "id desc"

    bid_id = fields.Many2one('purchase.bid', 'Bid', required=True)
    project = fields.Char(string='Project')
    location = fields.Char(string='Location')

class PurchaseBidVendor(models.Model):
    _name = "purchase.bid.vendor"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Bid Vendor"
    _order = "id desc"

    def _compute_evaluator_count(self):
        for rec in self:
            self.evaluator_count = len(rec.evaluator_line)

    name = fields.Char(related='partner_id.name', string='Name')
    bid_id = fields.Many2one('purchase.bid', 'Bid')
    partner_id = fields.Many2one('res.partner', string='Vendors', required=True)
    contact_id = fields.Many2one('res.partner', string='Contact Person', domain="[('id', 'child_of', partner_id)]")
    invitation = fields.Selection(selection=[('draft','Draft'),('sent','Sent')], string='Invitation', default='draft')
    acceptance = fields.Selection(selection=_ACCEPTANCE, string='Acceptance')
    acceptance_date = fields.Datetime(string='Acceptance Date')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    prebid_attendance = fields.Boolean(string='Pre-bid Meeting Attendance')
    date_attended = fields.Date(string='Date Attended ')
    non_disc_agreement = fields.Boolean(string='Non-disclosure Agreement')
    date_aggreed = fields.Date(string='Date Aggreed ')
    bid_ref = fields.Char(related='bid_id.bid_ref')
    bid_name = fields.Char(related='bid_id.bid_name')
    date_created = fields.Date(related='bid_id.date_created')
    purchasing_officer = fields.Many2one(related='bid_id.purchasing_officer')
    bid_opening_date = fields.Datetime(related='bid_id.bid_opening_date')
    bid_closing_date = fields.Datetime(related='bid_id.bid_closing_date')
    is_kicked = fields.Boolean(string='Kicked')
    kick_out_reason = fields.Text('Kick out reason')
    pre_bid_documents_id = fields.Many2many('pre.bid.documents', 'document_selection', 'document_id', string='Pre-bid Documents')
    pre_bid_documents_available_id = fields.Many2many('pre.bid.documents', 'document_available', 'document_id', string='Pre-bid Documents Available')
    deadline_of_submission = fields.Date(string='Deadline of Submission')
    evaluator_line = fields.One2many('vendor.evaluator', 'vendor_bid_id', string='Evaluator Line')
    evaluator_count = fields.Integer(compute='_compute_evaluator_count', string='Evaluator Count')
    # Technical Evaluation
    evaluation_line = fields.One2many('vendor.evaluation.line', 'vendor_bid_id', string='Technical Evaluation', copy=True, domain=[('type', '=', 'technical')])
    technical_eval_status = fields.Selection(selection=_EVALUATION, string='Technical Evaluation Status')
    other_comments = fields.Text('Other Comments')
    for_clarification = fields.Boolean('For clarification')
    for_negotiation = fields.Boolean('For negotiation')
    prepared_by = fields.Many2one('res.users', string="Preparer")
    prepared_date = fields.Date('Date Prepared')
    reviewed_by = fields.Many2one('res.users', string="Reviewer")
    reviewed_date = fields.Date('Date Reviewed')
    approved_by = fields.Many2one('res.users', string="Approver")
    approved_date = fields.Date('Date Approved')
    # Commercial Evaluation
    commercial_evaluation_line = fields.One2many('vendor.evaluation.line', 'vendor_bid_id', string='Commercial Evaluation', copy=True, domain=[('type', '=', 'commercial')])
    commercial_eval_status = fields.Selection(selection=_EVALUATION, string='Commercial Evaluation Status')
    c_other_comments = fields.Text('Other Comments')
    c_for_clarification = fields.Boolean('For Clarification')
    c_for_negotiation = fields.Boolean('For Negotiation')
    c_prepared_by = fields.Many2one('res.users', string="Preparer")
    c_prepared_date = fields.Date('Date Prepared')
    c_reviewed_by = fields.Many2one('res.users', string="Reviewer")
    c_reviewed_date = fields.Date('Date Reviewed')
    c_approved_by = fields.Many2one('res.users', string="Approver")
    c_approved_date = fields.Date('Date Approved')
    # Bid summary
    bid_summary_line = fields.One2many('bid.summary.line', 'vendor_bid_id', string='Bid Summary')
    negotiated_amount = fields.Float(string='Negotiated Amount (Gross)')
    lead_time = fields.Integer(string='Lead Time')
    terms_of_payment_line = fields.One2many('terms.of.payment.line', 'vendor_bid_id', string='Bid Summary')

    @api.model
    def create(self, values):
        if 'bid_id' in values and 'evaluation_line' not in values:
            bid_data = self.env['purchase.bid'].browse(values['bid_id'])
            pre_bid_doc_ids = [line.id for line in bid_data.pre_bid_documents_id]
            values['evaluation_line'] = [(0, 0, line._prepare_evaluation_criteria('technical')) for line in bid_data.evaluation_line]
            values['commercial_evaluation_line'] = [(0, 0, line._prepare_evaluation_criteria('commercial')) for line in bid_data.commercial_evaluation_line]
            values['pre_bid_documents_available_id'] = [(6, 0, pre_bid_doc_ids)]
        return super(PurchaseBidVendor, self).create(values)

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
            'domain': [('vendor_bid_id','=', self.id)],
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

class VendorEvaluationLine(models.Model):
    _name = "vendor.evaluation.line"
    _description = "Vendor Evaluation Line"

    name = fields.Char(string="Description")
    bid_id = fields.Many2one('purchase.bid', string="Bid", index=True, ondelete='cascade')
    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string="Vendor Bid", index=True, ondelete='cascade')
    default_evaluation_temp_id = fields.Many2one('vendor.evaluation.template', string="Default Evaluation Template", index=True, ondelete='cascade')
    criteria = fields.Many2one('evaluation.criteria', string='Criteria')
    weight = fields.Float(string="Weight")
    offer = fields.Float(string="Offer")
    score = fields.Float(string="Score", compute='_compute_average', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False, help="Technical field for UX purpose.", string='Display Type')
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Type')

    @api.depends(
        'vendor_bid_id.evaluator_line',
        'vendor_bid_id.evaluator_line.type',
        'vendor_bid_id.evaluator_line.evaluation_line',
        'vendor_bid_id.evaluator_line.evaluation_line.score')
    def _compute_average(self):
        for rec in self:
            evaluation_ids = self.env['vendor.evaluator.line'].search([('evaluation_id','=',rec.id),('display_type','=',False)])
            score_average = 0
            line_cnt = 0
            for line in evaluation_ids:
                score_average += line.score
                line_cnt += 1
            rec.score = score_average and (score_average / line_cnt) or 0

    @api.onchange('criteria')
    def _onchange_criteria(self):
        self.weight = self.criteria and self.criteria.weight or 0

    def _prepare_evaluation_criteria(self, type):
        create_evaluator = self.env.context.get('create_evaluator', False)
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
        return res

class VendorEvaluationTemplate(models.Model):
    _name = "vendor.evaluation.template"
    _description = "Vendor Evaluation Template"

    name = fields.Char(string='Name', required=True, default="Default Evaluation Template")
    technical_evaluation_line = fields.One2many('vendor.evaluation.line', 'default_evaluation_temp_id', string='Technical Evaluation', copy=True, domain=[('type', '=', 'technical')])
    commercial_evaluation_line = fields.One2many('vendor.evaluation.line', 'default_evaluation_temp_id', string='Commercial Evaluation', copy=True, domain=[('type', '=', 'commercial')])

class VendorEvaluator(models.Model):
    _name = "vendor.evaluator"
    _description = "Vendor Evaluation"

    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string="Vendor Bid", index=True, ondelete='cascade')
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, required=True)
    name = fields.Char(related='evaluator_id.name', string='Name')
    bid_id = fields.Many2one(related='vendor_bid_id.bid_id')
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Evaluation Type')
    evaluation_line = fields.One2many('vendor.evaluator.line', 'vendor_evaluation_id', string='Evaluation', copy=True)

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
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False, help="Technical field for UX purpose.", string='Display Type')
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Type')

class EvaluationCriteria(models.Model):
    _name = "evaluation.criteria"
    _description = "Evaluation Criteria"
    _order = "name asc"

    name = fields.Char(string="Name")
    weight = fields.Float(string="Weight")

class BidSummaryLine(models.Model):
    _name = "bid.summary.line"
    _description = "Bid Summary Line"

    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string='Bid Vendor', required=True)
    name = fields.Char(string='Bid Description', required=True)
    amount = fields.Float(string='Amount')
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False, help="Technical field for UX purpose.", string='Display Type')

class TermsOfPaymentLine(models.Model):
    _name = "terms.of.payment.line"
    _description = "Terms of Payment Line"

    vendor_bid_id = fields.Many2one('purchase.bid.vendor', string='Bid Vendor', required=True)
    name = fields.Char(string='Description')
    payment_percent = fields.Float(string='(%)')
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False, help="Technical field for UX purpose.", string='Display Type')

class PreBidDocuments(models.Model):
    _name = "pre.bid.documents"
    _description = "Pre-bid Documents"
    _order = "name asc"

    name = fields.Char(string="Name", required=True)
