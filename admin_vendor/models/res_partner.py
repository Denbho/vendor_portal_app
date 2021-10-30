# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, ValidationError
import logging
import json
from lxml import etree
import re

_logger = logging.getLogger("_name_")

_EVALUATION = [
    ('pending', 'Pending'),
    ('ongoing_review', 'Ongoing review'),
    ('approved', 'Approved'),
]

class ResPartnerAffiliation(models.Model):
    _name = 'res.partner.affiliation'
    _description = "Contact Affiliations"

    name = fields.Char(string="Company/Subsidiary", required=True)
    contact_partner_id = fields.Many2one('res.partner', string="Contact Details")
    email = fields.Char(string="Email")
    relationship = fields.Char(string="Relationship")
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.onchange('email')
    def onchange_email(self):
        if self.email:
            contact = self.env['res.partner'].sudo().search([('email', '=', self.email)])
            if contact[:1]:
                self.contact_partner_id = contact.id


class ResUsers(models.Model):
    _inherit = 'res.users'

    def copy(self, default=None):
      self.ensure_one()
      prev_email = default.get('email') if default else ''
      new_email = prev_email or _('%s (copy)') % self.email
      default = dict(default or {}, email=new_email)
      return super(ResUsers, self).copy(default)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_show_accredit_button(self):
        for rec in self:
            rec.check_date_prebid_postbid = True
            current_date = fields.Date.today()
            show_accredit = False
            if rec.end_date:
                if current_date >= rec.end_date:
                    show_accredit = True
            else:
                show_accredit = True
            self.show_accredit_button = show_accredit

    affiliated_subsidiary_comp_ids = fields.Many2many(comodel_name='res.partner',
                                                      relation='affiliated_subsidiary_comp_rel',
                                                      column1='affiliated_subsidiary_comp_id',
                                                      column2='affiliated_subsidiary_comp_id2',
                                                      string='Affiliated/Subsidiary Companies')
    affiliated_contact_ids = fields.One2many('res.partner.affiliation', 'partner_id',
                                             string="Affiliated/Subsidiary Companies")
    registration_date = fields.Date(string='Registration Date', track_visibility="always")
    product_classification_ids = fields.Many2many('product.classification', string='Product Classifications')
    product_service_offered_line = fields.One2many('product.service.offered', 'partner_id',
                                                   string='Products/Services Offered')
    document_ids = fields.Many2many('document.requirement', string='Documents')
    for_accreditation = fields.Boolean(string='For Accreditation', track_visibility="always")
    accredited = fields.Boolean(string='For Accredited', track_visibility="always")
    date_accredited = fields.Date(string='Date Accredited', track_visibility="always")
    start_date = fields.Date(string='Start Date', track_visibility="always")
    end_date = fields.Date(string='End Date', track_visibility="always")
    evaluation_period = fields.Date(string='Evaluation Period', track_visibility="always")
    overall_assessment = fields.Float(string='Overall Assessment', track_visibility="always")
    extend_result = fields.Boolean(string='Extend Result to Vendor?', track_visibility="always")
    evaluation_count = fields.Integer(compute="_get_evaluation_count")
    regular_evaluation_count = fields.Integer(compute="_get_regular_evaluation_count")
    supplier_number = fields.Char('Supplier No.', track_visibility="always")
    has_other_category = fields.Boolean('Other', track_visibility="always")
    other_categories = fields.Text('Other Categories', track_visibility="always")
    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    vendor_account_group_code = fields.Char(string="Vendor Account Group Code", track_visibility="always")
    vendor_account_group_id = fields.Many2one('vendor.account.group', string="Vendor Account Group", track_visibility="always")
    business_name = fields.Char(string='Business Owner Name', track_visibility="always")
    business_type = fields.Selection([
                                    ('Individual', "Individual"), ('Cooperative', "Cooperative"),
                                    ('Corporation', "Corporation"), ('Partnership', "Partnership")
                                    ], string='Business Type', track_visibility="always")
    department = fields.Char(string='Department', track_visibility="always")
    vendor_code_113 = fields.Char(string='Vendor Code 113', track_visibility="always")
    vendor_code_303 = fields.Char(string='Vendor Code 303', track_visibility="always")
    universal_vendor_code = fields.Char(string='Universal Vendor Code', track_visibility="always")
    vat_type = fields.Selection([('vat', "Vatable"), ('nvat', "Non-vatable")],
                                string='VAT Type', track_visibility="always")
    is_subject_to_wh_tax = fields.Boolean(string='Subject to WH Tax?', track_visibility="always")
    wh_tax_code_id = fields.Many2one('admin.wh.tax.code', string="WH Tax Code", track_visibility="always")
    wh_tax_code = fields.Char(string="Tax Code")
    purchase_org_id = fields.Many2one('admin.purchase.organization', string="Purchase Organization", track_visibility="always")
    purchase_org_code = fields.Char(string="Purchase Organization Code")
    next_evaluation_date = fields.Date(string="Next Evaluation Date", track_visibility="always")
    evaluation_responsible_ids = fields.Many2many('res.users', 'partner_evaluation_responsible_rel', string='Responsible')
    type_of_evaluation = fields.Selection(selection=[
                                                    ('monthly', 'Monthly'),
                                                    ('quarterly', 'Quarterly'),
                                                    ('annual', 'Annual'),
                                                    ('semi_annual', 'Semi Annual')],
                                                    string="How often should we evaluate this vendor ?")
    accreditation_id = fields.Many2one('partner.evaluation', 'Accreditation Ref.')
    is_blocked = fields.Boolean(string='Is Blocked')

    _sql_constraints = [
        # ('vendor_tin_key', 'unique(vat)', "TIN must be unique !"),
        ('vendor_email', 'unique(email)', "Email must be unique !"),
    ]

    @api.constrains('vat')
    def _check_duplicate_tin(self):
        for rec in self:
            if rec.vat:
                tin = self.env['res.partner'].sudo().search([('vat', '=', rec.vat), ('id', '!=', rec.id), ('parent_id', '!=', rec.id)], limit=1)
                if rec.parent_id:
                    tin = self.env['res.partner'].sudo().search([('vat', '=', rec.vat), ('id', '!=', rec.id), ('id', '!=', rec.parent_id.id)], limit=1)
                if tin:
                    raise ValidationError("TIN must be unique !")

    # @api.constrains('email')
    # def _check_duplicate_email(self):
    #     for rec in self:
    #         emails = self.env['res.partner'].sudo().search([('email', '=', rec.email), ('id', '!=', rec.id)], limit=1)
    #         if emails[:1]:
    #             raise ValidationError("Email must be unique!")

    @api.onchange('purchase_org_id')
    def onchange_purchase_org_id(self):
        if self.purchase_org_id:
            self.purchase_org_code = self.purchase_org_id.code

    @api.onchange('purchase_org_code')
    def onchange_purchase_org_code(self):
        if self.purchase_org_code:
            purchase_org_id = self.env['admin.purchase.organization'].sudo().search([('code', '=', self.purchase_org_code)], limit=1)
            if purchase_org_id[:1]:
                self.purchase_org_id = purchase_org_id.id

    @api.onchange('wh_tax_code_id')
    def onchange_wh_tax_code_id(self):
        if self.wh_tax_code_id:
            self.wh_tax_code = self.wh_tax_code_id.code

    @api.onchange('wh_tax_code')
    def onchange_wh_tax_code(self):
        if self.wh_tax_code:
            wh_tax_code_id = self.env['admin.wh.tax.code'].sudo().search([('code', '=', self.wh_tax_code)], limit=1)
            if wh_tax_code_id[:1]:
                self.wh_tax_code_id = wh_tax_code_id.id

    @api.onchange('is_subject_to_wh_tax')
    def onchange_is_subject_to_wh_tax(self):
        if not self.is_subject_to_wh_tax:
            self.wh_tax_code_id = False

    @api.onchange('vendor_account_group_id')
    def onchange_vendor_account_group_id(self):
        if self.vendor_account_group_id:
            self.vendor_account_group_code = self.vendor_account_group_id.code

    @api.onchange('vendor_account_group_code')
    def onchange_vendor_account_group_code(self):
        if self.vendor_account_group_code:
            vendor_account_group = self.env['vendor.account.group'].sudo().search([('code', '=', self.vendor_account_group_code)], limit=1)
            if vendor_account_group[:1]:
                self.vendor_account_group_id = vendor_account_group.id

    @api.depends('for_accreditation', 'registration_date', 'accredited',
                 'is_company', 'name', 'parent_id.display_name', 'type', 'company_name')
    def _compute_display_name(self):
        return super(ResPartner, self)._compute_display_name()

    def name_get(self):
        res = []
        for partner in self:
            name = partner._get_name()
            if partner.registration_date or partner.date_accredited or partner.supplier_rank >= 1 or partner.evaluation_count >= 1:
                if partner.end_date and not partner.accredited:
                    name += ' [For re-accreditation]'
                elif not partner.accredited and (partner.registration_date or partner.supplier_rank >= 1 or partner.evaluation_count >= 1):
                    name += ' [For Accreditation]'
                elif partner.accredited:
                    name += ' [ Accredited]'
            res.append((partner.id, name))
        return res

    def check_vendor_accreditation_and_reg_evaluation(self):
        default_template_data_monthly = self.env['vendor.evaluation.template'].sudo().search([
                  ('template_purpose', '=', 'vendor_regular_evaluation'),
                  ('type_of_evaluation', '=', 'monthly')], limit=1)
        default_template_data_quarterly = self.env['vendor.evaluation.template'].sudo().search([
              ('template_purpose', '=', 'vendor_regular_evaluation'),
              ('type_of_evaluation', '=', 'quarterly')], limit=1)
        default_template_data_annual = self.env['vendor.evaluation.template'].sudo().search([
              ('template_purpose', '=', 'vendor_regular_evaluation'),
              ('type_of_evaluation', '=', 'annual')], limit=1)
        default_template_data_semi_annual = self.env['vendor.evaluation.template'].sudo().search([
              ('template_purpose', '=', 'vendor_regular_evaluation'),
              ('type_of_evaluation', '=', 'semi_annual')], limit=1)
        accredited = self.sudo().search([('accredited', '=', True)])
        for r in accredited:
            vals = {}
            if r.end_date and r.accredited and r.end_date <= date.today():
                vals.update({
                    'for_accreditation': True,
                    'accredited': False
                })
                r.send_admin_email_notif('re_accreditation_request', 'Re-Accreditation Request', r.email, 'res.partner')
            else:
                if r.type_of_evaluation and r.next_evaluation_date <= date.today():
                    default_template_data = default_template_data_monthly
                    eval_months = 1
                    if r.type_of_evaluation == 'quarterly':
                        eval_months = 3
                        default_template_data = default_template_data_quarterly
                    elif r.type_of_evaluation == 'annual':
                        eval_months = 12
                        default_template_data = default_template_data_annual
                    elif r.type_of_evaluation == 'semi_annual':
                        eval_months = 6
                        default_template_data = default_template_data_semi_annual
                    # Create regular evaluation.
                    new_regular_evaluation = self.env['partner.regular.evaluation'].sudo().create({
                        'accreditation_id': r.accreditation_id and r.accreditation_id.id or False,
                        'partner_id': r.id,
                        'evaluation_date': fields.Date.today(),
                        'type_of_evaluation': r.type_of_evaluation,
                        'evaluation_line': [
                          (0, 0, ln._prepare_evaluation_criteria('technical')) for ln in
                          default_template_data.technical_evaluation_line
                        ],
                        'commercial_evaluation_line': [
                          (0, 0, ln._prepare_evaluation_criteria('commercial')) for ln in
                          default_template_data.commercial_evaluation_line
                        ],
                        'assigned_vendor_evaluator_line': [
                            (0, 0, ln._prepare_evaluation_evaluator()) for ln in
                            default_template_data.assigned_evaluator_line
                        ],
                        'technical_valuation_weight': default_template_data.technical_valuation_weight,
                        'commercial_valuation_weight': default_template_data.commercial_valuation_weight
                    })
                    next_evaluation_date = r.next_evaluation_date + relativedelta(months=eval_months)
                    r.next_evaluation_date = next_evaluation_date
                    if r.evaluation_responsible_ids:
                        partner_model = self.env['ir.model'].sudo().search([('model','=','res.partner')])
                        if partner_model[:1]:
                            # Create schedule activity in vendor profile.
                            new_sched_activity = self.env['mail.activity'].create({
                                'activity_type_id': 4,     #To Do
                                'res_model_id': partner_model.id,
                                'res_id': r.id,
                                'summary': 'For Regular Evaluation',
                                'user_id': r.evaluation_responsible_ids.ids[0],
                                'note': '<b>Regular Evaluation.</b>',
                                'date_deadline': next_evaluation_date,
                                'res_name': r.name+': For Regular Evaluation',
                            })
                            new_sched_activity.action_close_dialog()
                        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                        base_url += '/web#id=%d&view_type=form&model=%s' % (new_regular_evaluation.id, new_regular_evaluation._name)
                        # Notify regular evaluation responsibles assigned in vendor profile.
                        for ln in r.evaluation_responsible_ids:
                            mail_body = '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                                              <b>Dear '+ln.name+',</b><br/><br/>\
                                              We would like to inform you that vendor <b>'+ r.name +'</b> is for regular evaluation. <br/><br/> \
                                              Link: <a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                                              Regards,<br/>'+self.env.company.name+'</p></div>'
                            mail_values = {
                              'subject': 'Regular Evaluation for '+ r.name,
                              'email_to': ln.email,
                              'body_html': mail_body,
                              'model': 'partner.regular.evaluation',
                              'res_id': new_regular_evaluation.id,
                            }
                            self.env['mail.mail'].sudo().create(mail_values).send()
            if vals:
                r.sudo().write(vals)

    def create_evaluation_accreditation(self):
        data = self.env['partner.evaluation'].sudo().create({
            'partner_id': self.id
        })
        self.sudo().write({'for_accreditation': True})
        return data

    @api.model
    def create(self, vals):
        if vals.get('vat'):
            vat = vals.get('vat')
            if vat:
                vat_int_list = re.findall(r'\b\d+\b', vat)
                vat = [str(vat_line) for vat_line in vat_int_list]
                vals['vat'] = "".join(vat)

        res = super(ResPartner, self).create(vals)
        res.onchange_vendor_account_group_code()
        res.onchange_wh_tax_code()
        res.onchange_purchase_org_code()
        if vals.get('registration_date') and (not vals.get('start_date') or not vals.get('date_accredited')):
            res.create_evaluation_accreditation()
        elif vals.get('end_date') and datetime.strptime(vals.get('end_date'), '%Y-%m-%d').date() <= date.today():
            res.create_evaluation_accreditation()
        return res

    def _compute_show_accredit_button(self):
        for rec in self:
            current_date = fields.Date.today()
            show_accredit = False
            if rec.end_date:
                if current_date >= rec.end_date:
                    show_accredit = True
            else:
                show_accredit = True
            self.show_accredit_button = show_accredit

    def _get_evaluation_count(self):
        for r in self:
            r.evaluation_count = self.env['partner.evaluation'].search_count([('partner_id', '=', r.id)])

    def _get_regular_evaluation_count(self):
        for r in self:
            r.regular_evaluation_count = self.env['partner.regular.evaluation'].search_count([('partner_id', '=', r.id)])

    def action_accredit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Accredit'),
            'res_model': 'vendor.accredit',
            'target': 'new',
            'view_mode': 'form',
        }

    def action_evaluate(self):
        self.ensure_one()
        return {
            'name': _('Evaluations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.evaluation',
            'domain': [('partner_id', '=', self.id)],
            'target': 'current',
            'context': {'default_partner_id': self.id},
        }

    def action_show_regular_evaluation(self):
        self.ensure_one()
        return {
            'name': _('Regular Evaluations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.regular.evaluation',
            'domain': [('partner_id', '=', self.id)],
            'target': 'current',
            'context': {'default_partner_id': self.id, 'default_type_of_evaluation': self.type_of_evaluation,
                        'default_evaluation_date': self.next_evaluation_date },
        }


class PartnerEvaluationLine(models.Model):
    _name = "partner.evaluation.line"
    _inherit = "vendor.evaluation.line"
    _description = "Partner Evaluation Line"

    name = fields.Char(string="Description")
    partner_evaluation_id = fields.Many2one('partner.evaluation', string="Partner Evaluation", index=True,
                                            ondelete='cascade')
    score = fields.Float(string="Score", compute='_compute_average', store=True)

    @api.depends(
        'partner_evaluation_id.evaluator_line',
        'partner_evaluation_id.evaluator_line.type',
        'partner_evaluation_id.evaluator_line.evaluation_line',
        'partner_evaluation_id.evaluator_line.evaluation_line.score')
    def _compute_average(self):
        for rec in self:
            evaluation_ids = self.env['partner.evaluator.line'].search(
                [('evaluation_id', '=', rec.id), ('display_type', '=', False)])
            score_average = 0
            line_cnt = 0
            for line in evaluation_ids:
                score_average += line.score
                line_cnt += 1
            rec.score = score_average and (score_average / line_cnt) or 0


class PartnerEvaluator(models.Model):
    _name = "partner.evaluator"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "admin.email.notif"]
    _description = "Partner Evaluator"

    name = fields.Char(related='evaluator_id.name', string='Name')
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, required=True)
    partner_evaluation_id = fields.Many2one('partner.evaluation', string="Partner Evaluation")
    state = fields.Selection(related='partner_evaluation_id.state')
    evaluation_line = fields.One2many('partner.evaluator.line', 'partner_evaluator_id', string='Evaluation',
                                        readonly=False, states={'approved': [('readonly', True)]}, copy=True)
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Evaluation Type')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    @api.onchange('type')
    def _onchange_type(self):
        eval_type = self.type
        if self.evaluation_line:
            self.evaluation_line.unlink()
        if eval_type:
            for rec in self.partner_evaluation_id:
                default_eval_entries = rec.evaluation_line
                if eval_type == "commercial":
                    default_eval_entries = rec.commercial_evaluation_line
                self.evaluation_line = [
                    (0, 0, line._prepare_evaluation_criteria(eval_type))
                    for line in default_eval_entries
                ]
        self.type = eval_type

    @api.model
    def create(self, vals):
        res = super(PartnerEvaluator, self).create(vals)
        mail_subject = 'Evaluation Reminder for Vendor Accreditation: '+ res.partner_evaluation_id.name +', Vendor: '+res.partner_evaluation_id.partner_id.name
        res.send_admin_email_notif('vendor_evaluation', mail_subject, res.evaluator_id.email, 'partner.evaluator')
        return res

class PartnerEvaluatorLine(models.Model):
    _name = "partner.evaluator.line"
    _inherit = "vendor.evaluator.line"
    _description = "Partner Evaluator Line"

    partner_evaluator_id = fields.Many2one('partner.evaluator', string="Evaluator", index=True, ondelete='cascade')
    evaluation_id = fields.Many2one('partner.evaluation.line', string='Partner Evaluation Line')


class VendorAccredit(models.TransientModel):
    _name = "vendor.accredit"
    _description = "Accredit"

    date_accredited = fields.Date(string='Date Accredited', default=fields.Date.today(), required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def action_confirm_accredit(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].browse(active_id)
        active_entry.write({
            'date_accredited': self.date_accredited,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'for_accreditation': False
        })


class ProductServiceOffered(models.Model):
    _name = 'product.service.offered'
    _inherit = 'image.mixin'
    _description = 'Products/Services Offered'

    name = fields.Char(string="Product/Service Description", required=True)
    product_service = fields.Char(string="Product/Service")
    product_id = fields.Many2one('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    sequence = fields.Integer(string='Sequence', default=10)
    price = fields.Float(string="Price")
    product_classification_id = fields.Many2one('product.classification', string='Product Classification')
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')
    attachment_ids = fields.Many2many('ir.attachment', 'partner_product_offered_rel', string="Attachments")

    def view_product(self):
        self.ensure_one()
        context = self._context.copy()
        return {
            'name': _('Product'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            'domain': [('id', '=', self.product_id.id)],
            'target': 'current',
            'context': context,
        }


class PartnerEvaluation(models.Model):
    _name = "partner.evaluation"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "resource.mixin", "document.default.approval", "admin.email.notif"]
    _description = "Partner Evaluation"

    @api.model
    def view_init(self, fields):
        res = super(PartnerEvaluation, self).view_init(fields)
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
        _logger.info("\n\n I am Called!\n\n")
        if partner.end_date and partner.end_date > date.today():
            raise ValidationError(_("This vendor accreditation is still active. You process the re accreditation once it expires."))
        return res

    def _compute_evaluator_count(self):
        for rec in self:
            self.evaluator_count = len(rec.evaluator_line)

    @api.model
    def default_get(self, default_fields):
        res = super(PartnerEvaluation, self).default_get(default_fields)
        default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', True)],
                                                                              limit=1)
        res.update({
            'evaluation_line': [
                (0, 0, line._prepare_evaluation_criteria('technical')) for line in
                default_template_data.technical_evaluation_line
            ],
            'commercial_evaluation_line': [
                (0, 0, line._prepare_evaluation_criteria('commercial')) for line in
                default_template_data.commercial_evaluation_line
            ],
            'assigned_vendor_evaluator_line': [
                  (0, 0, line._prepare_evaluation_evaluator()) for line in
                  default_template_data.assigned_evaluator_line
            ],
            'required_document_accreditation_requirement_ids': [
                (6, 0, [line.id for line in default_template_data.document_accreditation_requirement_ids])],
            'technical_valuation_weight': default_template_data.technical_valuation_weight,
            'commercial_valuation_weight': default_template_data.commercial_valuation_weight,
            'submission_deadline': date.today() + relativedelta(days=default_template_data.submission_deadline),
            'instructions': default_template_data.instructions,
        })
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PartnerEvaluation, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                             toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        context = self.env.context
        if 'default_partner_id' not in context:
            if view_type == 'tree':
                doc.set('create', 'false')
                doc.set('import', 'false')
            if view_type == 'form':
                doc.set('create', 'false')
        res['arch'] = etree.tostring(doc)
        return res

    name = fields.Char(string="Accreditation Number", copy=False, readonly=True, index=True,
                       default=lambda self: _('New'), track_visibility="always")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, track_visibility="always")
    evaluation_line = fields.One2many('partner.evaluation.line', 'partner_evaluation_id', string='Technical Evaluation',
                                      copy=True, domain=[('type', '=', 'technical')],
                                      readonly=True, states={'draft': [('readonly', False)]})
    commercial_evaluation_line = fields.One2many('partner.evaluation.line', 'partner_evaluation_id',
                                    string='Commercial Evaluation', copy=True, domain=[('type', '=', 'commercial')],
                                    readonly=True, states={'draft': [('readonly', False)]})
    evaluator_line = fields.One2many('partner.evaluator', 'partner_evaluation_id', string='Evaluator Line')
    evaluator_count = fields.Integer(compute='_compute_evaluator_count', string='Evaluator Count')
    required_document_accreditation_requirement_ids = fields.Many2many('document.requirement',
                                                    'evaluation_required_document_requirement_rel', string='Required Documents')
    document_accreditation_requirement_ids = fields.Many2many('document.requirement',
                                                              'evaluation_document_requirement_rel', string='Documents',
                                                              readonly=True, states={'draft': [('readonly', False)]})
    accreditation_validity = fields.Integer(string="Accreditation Validity", default=2, track_visibility="always",
                                            readonly=True, states={'draft': [('readonly', False)]})
    start_date = fields.Date(string='Start Date', track_visibility="always", readonly=True,
                            states={'draft': [('readonly', False)]})
    end_date = fields.Date(string='End Date', readonly=True, force_save=True)
    accreditation_remarks = fields.Html(string="Accreditation Remarks", readonly=False,
                                        states={'approved': [('readonly', True)]})
    technical_valuation_weight = fields.Float(string="Technical Valuation Weight", track_visibility="always",
                                              default=1, readonly=True, states={'draft': [('readonly', False)]})
    commercial_valuation_weight = fields.Float(string="Commercial Valuation Weight", track_visibility="always",
                                               default=1, readonly=True, states={'draft': [('readonly', False)]})
    technical_valuation_score = fields.Float(string="Technical Valuation Weight", store=True,
                                             compute="_get_valuation_score")
    commercial_valuation_score = fields.Float(string="Commercial Valuation Weight", store=True,
                                              compute="_get_valuation_score")
    overall_score = fields.Float(string="Overall Evaluation Score", store=True, compute="_get_valuation_score")
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    assigned_vendor_evaluator_line = fields.One2many('assigned.vendor.evaluator.line', 'partner_evaluation_id',
                                                    string='Assigned Vendor Evaluators', copy=True,
                                                    readonly=True, states={'draft': [('readonly', False)]})
    type_of_evaluation = fields.Selection(selection=[
                                        ('monthly', 'Monthly'),
                                        ('quarterly', 'Quarterly'),
                                        ('annual', 'Annual'),
                                        ('semi_annual', 'Semi Annual')],
                                        string="How often should we evaluate this vendor ?")
    inactive = fields.Boolean(string="Inactive")
    submission_deadline = fields.Date(string="Submission Deadline", track_visibility="always")
    instructions = fields.Html(string="Instructions", readonly=False,
                                        states={'approved': [('readonly', True)]})
    rtd_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reset to Draft Reason', track_visibility='always')
    rtd_description = fields.Text(string='Reset to Draft Reasons Description', track_visibility='always')
    cancel_reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Cancelation Reason', track_visibility='always')
    cancel_description = fields.Text(string='Cancelation Description', track_visibility='always')
    state = fields.Selection(selection_add=[('rejected','Rejected')])

    def btn_reject(self):
        self.state = 'rejected'

    def submit_request(self):
        if not self.assigned_vendor_evaluator_line:
            raise Warning("Please assign evaluator/s.")
        else:
            self = self.with_context(create_evaluator=True)
            for line in self.assigned_vendor_evaluator_line:
                new_evaluator = self.env['partner.evaluator'].create({
                    'partner_evaluation_id': self.id,
                    'evaluator_id': line.user_id.id,
                    'type': line.type
                })
                new_evaluator._onchange_type()
        return super(PartnerEvaluation, self).submit_request()

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
            overall_score = r.technical_valuation_weight > 0 and overall_weight and (r.technical_valuation_weight / overall_weight) * total_technical_valuation_score or 0
            overall_score += r.commercial_valuation_weight > 0 and overall_weight and (r.commercial_valuation_weight / overall_weight) * total_commercial_valuation_score or 0
            r.technical_valuation_score = total_technical_valuation_score
            r.commercial_valuation_score = total_commercial_valuation_score
            r.overall_score = overall_score

    @api.onchange('start_date', 'accreditation_validity')
    def onchange_start_date(self):
        if self.start_date and self.accreditation_validity:
            self.end_date = self.start_date + relativedelta(years=self.accreditation_validity)

    def approve_request(self):
        if self.overall_score == 0:
            raise Warning("Evaluation score must be greater than zero.")
        vals = {}
        start_date = self.start_date
        if not start_date:
            start_date = date.today()
            vals['start_date'] = start_date
        vals['end_date'] = start_date + relativedelta(years=self.accreditation_validity)
        self.partner_id.write({
            'date_accredited': date.today(),
            'start_date': start_date,
            'end_date': start_date + relativedelta(years=self.accreditation_validity),
            'for_accreditation': False,
            'accredited': True,
        })
        partner_evaluation_ids = self.sudo().search([('partner_id', '=', self.partner_id.id),
                                ('inactive', '=', False), ('id', '!=', self.id)])
        for line in partner_evaluation_ids:
            line.inactive = True
        self.send_admin_email_notif('accreditation_result', 'Accreditation Result', self.partner_id.email, 'partner.evaluation')
        self.write(vals)
        return super(PartnerEvaluation, self).approve_request()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('vendor.accreditation')
        res = super(PartnerEvaluation, self).create(vals)
        res.send_admin_email_notif('accreditation_request', 'Accreditation Request', self.partner_id.email, 'partner.evaluation')
        if not res.partner_id.for_accreditation:
            res.partner_id.write({'for_accreditation': True})
        return res

    def write(self, vals):
        res = super(PartnerEvaluation, self).write(vals)
        if 'document_accreditation_requirement_ids' in vals:
            if len(self.document_accreditation_requirement_ids) == len(self.required_document_accreditation_requirement_ids):
                self.send_admin_email_notif('accreditation_submitted', 'Accreditation Submitted', self.partner_id.email, 'partner.evaluation')
        return res

    def action_view_evaluator(self):
        self.ensure_one()
        return {
            'name': _('Evaluator'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.evaluator',
            'domain': [('partner_evaluation_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_partner_evaluation_id': self.id,
                'default_type': 'technical',
            },
        }


class AssignedVendorEvaluatorLine(models.Model):
    _name = "assigned.vendor.evaluator.line"
    _description = "Assigned Vendor Evaluator Line"

    partner_evaluation_id = fields.Many2one('partner.evaluation', 'Vendor Evaluation')
    regular_evaluation_id = fields.Many2one('partner.regular.evaluation', 'Regular Evaluation')
    user_id = fields.Many2one('res.users', string='Evaluator', required=True)
    type = fields.Selection([('commercial', 'Commercial'), ('technical', 'Technical')], string='Type', required=True, default='technical')

    def _prepare_evaluation_evaluator(self):
        res = {
            'user_id': self.user_id.id,
            'type': self.type,
        }
        return res

class PurchaseBid(models.Model):
    _inherit = "purchase.bid"

    def _default_technical_evaluation_line(self):
        res = []
        default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', False)],
                                                                              limit=1)
        for rec in default_template_data:
            res = [
                (0, 0, line._prepare_evaluation_criteria('technical')) for line in rec.technical_evaluation_line
            ]
        return res

    def _default_commercial_evaluation_line(self):
        res = []
        default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', False)],
                                                                              limit=1)
        for rec in default_template_data:
            res = [
                (0, 0, line._prepare_evaluation_criteria('commercial')) for line in rec.commercial_evaluation_line
            ]
        return res


class VendorAccountGroup(models.Model):
    _name = "vendor.account.group"
    _description = "Vendor Account Group"

    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    number_range = fields.Integer("Number Range")
    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PartnerRegularEvaluation(models.Model):
    _name = "partner.regular.evaluation"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "resource.mixin", "document.default.approval", "admin.email.notif"]
    _description = "Partner Regular Evaluation"

    def _compute_evaluator_count(self):
        for rec in self:
            self.evaluator_count = len(rec.evaluator_line)

    @api.model
    def default_get(self, default_fields):
        res = super(PartnerRegularEvaluation, self).default_get(default_fields)
        context = self.env.context
        if 'default_type_of_evaluation' in context and context['default_type_of_evaluation']:
            default_template_data = self.env['vendor.evaluation.template'].search([
                ('template_purpose', '=', 'vendor_regular_evaluation'),
                ('type_of_evaluation', '=', context['default_type_of_evaluation'])], limit=1)
            if default_template_data:
                res.update({
                    'evaluation_line': [
                        (0, 0, line._prepare_evaluation_criteria('technical')) for line in
                        default_template_data.technical_evaluation_line
                    ],
                    'commercial_evaluation_line': [
                        (0, 0, line._prepare_evaluation_criteria('commercial')) for line in
                        default_template_data.commercial_evaluation_line
                    ],
                    'assigned_vendor_evaluator_line': [
                          (0, 0, line._prepare_evaluation_evaluator()) for line in
                          default_template_data.assigned_evaluator_line
                    ],
                    'technical_valuation_weight': default_template_data.technical_valuation_weight,
                    'commercial_valuation_weight': default_template_data.commercial_valuation_weight
                })
        return res

    name = fields.Char(string="Evaluation Number", copy=False, readonly=True, index=True,
                         default=lambda self: _('New'), track_visibility="always")
    evaluation_date = fields.Date(string="Evaluation Date")
    evaluation_remarks = fields.Html(string="Evaluation Remarks", readonly=False,
                                        states={'approved': [('readonly', True)]})
    accreditation_id = fields.Many2one('partner.evaluation', 'Accreditation Ref.')
    evaluation_line = fields.One2many('partner.regular.evaluation.line', 'regular_evaluation_id', string='Technical Evaluation',
                                      copy=True, domain=[('type', '=', 'technical')],
                                      readonly=True, states={'draft': [('readonly', False)]})
    commercial_evaluation_line = fields.One2many('partner.regular.evaluation.line', 'regular_evaluation_id',
                                    string='Commercial Evaluation', copy=True, domain=[('type', '=', 'commercial')],
                                    readonly=True, states={'draft': [('readonly', False)]})
    technical_valuation_weight = fields.Float(string="Technical Valuation Weight", track_visibility="always",
                                          default=1, readonly=True, states={'draft': [('readonly', False)]})
    commercial_valuation_weight = fields.Float(string="Commercial Valuation Weight", track_visibility="always",
                                               default=1, readonly=True, states={'draft': [('readonly', False)]})
    technical_valuation_score = fields.Float(string="Technical Valuation Weight", store=True,
                                             compute="_get_valuation_score")
    commercial_valuation_score = fields.Float(string="Commercial Valuation Weight", store=True,
                                              compute="_get_valuation_score")
    overall_score = fields.Float(string="Overall Evaluation Score", store=True, compute="_get_valuation_score")
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    assigned_vendor_evaluator_line = fields.One2many('assigned.vendor.evaluator.line', 'regular_evaluation_id',
                                                string='Assigned Evaluators', copy=True,
                                                readonly=True, states={'draft': [('readonly', False)]})
    type_of_evaluation = fields.Selection(selection=[
                                    ('monthly', 'Monthly'),
                                    ('quarterly', 'Quarterly'),
                                    ('annual', 'Annual'),
                                    ('semi_annual', 'Semi Annual')],
                                    string="How often regularly the accredited vendor to be evaluated ?")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, track_visibility="always")
    evaluator_line = fields.One2many('partner.regular.evaluator', 'partner_evaluation_id', string='Evaluator Line')
    evaluator_count = fields.Integer(compute='_compute_evaluator_count', string='Evaluator Count')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('partner.regular.evaluation')
        return super(PartnerRegularEvaluation, self).create(vals)

    def submit_request(self):
        if not self.assigned_vendor_evaluator_line:
            raise Warning("Please assign evaluator/s.")
        else:
            self = self.with_context(create_regular_evaluator=True)
            for line in self.assigned_vendor_evaluator_line:
                new_evaluator = self.env['partner.regular.evaluator'].create({
                    'partner_evaluation_id': self.id,
                    'evaluator_id': line.user_id.id,
                    'type': line.type
                })
                new_evaluator._onchange_type()
        return super(PartnerRegularEvaluation, self).submit_request()

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
            overall_score = r.technical_valuation_weight > 0 and overall_weight and (r.technical_valuation_weight / overall_weight) * total_technical_valuation_score or 0
            overall_score += r.commercial_valuation_weight > 0 and overall_weight and (r.commercial_valuation_weight / overall_weight) * total_commercial_valuation_score or 0
            r.technical_valuation_score = total_technical_valuation_score
            r.commercial_valuation_score = total_commercial_valuation_score
            r.overall_score = overall_score

    def approve_request(self):
        if self.overall_score == 0:
            raise Warning("Evaluation score must be greater than zero.")
        self.send_admin_email_notif('regular_evaluation_result', 'Regular Evaluation Result', self.partner_id.email, 'partner.regular.evaluation')
        return super(PartnerRegularEvaluation, self).approve_request()

    def action_view_evaluator(self):
        self.ensure_one()
        return {
            'name': _('Evaluator'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.regular.evaluator',
            'domain': [('partner_evaluation_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_partner_evaluation_id': self.id,
                'default_type': 'technical',
            },
        }


class PartnerRegularEvaluationLine(models.Model):
    _name = "partner.regular.evaluation.line"
    _inherit = "vendor.evaluation.line"
    _description = "Partner Regular Evaluation Line"

    name = fields.Char(string="Description")
    regular_evaluation_id = fields.Many2one('partner.regular.evaluation', string="Regular Evaluation", index=True,
                                            ondelete='cascade')
    score = fields.Float(string="Score", compute='_compute_average', store=True)

    @api.depends(
        'regular_evaluation_id.evaluator_line',
        'regular_evaluation_id.evaluator_line.type',
        'regular_evaluation_id.evaluator_line.evaluation_line',
        'regular_evaluation_id.evaluator_line.evaluation_line.score')
    def _compute_average(self):
        for rec in self:
            evaluation_ids = self.env['partner.regular.evaluator.line'].search(
                [('regular_evaluation_id', '=', rec.id), ('display_type', '=', False)])
            score_average = 0
            line_cnt = 0
            for line in evaluation_ids:
                score_average += line.score
                line_cnt += 1
            rec.score = score_average and (score_average / line_cnt) or 0


class PartnerRegularEvaluator(models.Model):
    _name = "partner.regular.evaluator"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "admin.email.notif"]
    _description = "Partner Regular Evaluator"

    name = fields.Char(related='evaluator_id.name', string='Name')
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, required=True)
    partner_evaluation_id = fields.Many2one('partner.regular.evaluation', string="Partner Regular Evaluation")
    state = fields.Selection(related='partner_evaluation_id.state')
    evaluation_line = fields.One2many('partner.regular.evaluator.line', 'partner_regular_evaluator_id', string='Evaluation',
                                        readonly=False, states={'approved': [('readonly', True)]}, copy=True)
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Evaluation Type')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    @api.onchange('type')
    def _onchange_type(self):
        eval_type = self.type
        if self.evaluation_line:
            self.evaluation_line.unlink()
        if eval_type:
            for rec in self.partner_evaluation_id:
                default_eval_entries = rec.evaluation_line
                if eval_type == "commercial":
                    default_eval_entries = rec.commercial_evaluation_line
                self.evaluation_line = [
                    (0, 0, line._prepare_evaluation_criteria(eval_type))
                    for line in default_eval_entries
                ]
        self.type = eval_type

    @api.model
    def create(self, vals):
        res = super(PartnerRegularEvaluator, self).create(vals)
        mail_subject = 'Regular Evaluation Reminder: '+ res.partner_evaluation_id.name +', Vendor: '+res.partner_evaluation_id.partner_id.name
        res.send_admin_email_notif('regular_evaluation', mail_subject, res.evaluator_id.email, 'partner.regular.evaluator')
        return res


class PartnerRegularEvaluatorLine(models.Model):
    _name = "partner.regular.evaluator.line"
    _inherit = "vendor.evaluator.line"
    _description = "Partner Regular Evaluator Line"

    partner_regular_evaluator_id = fields.Many2one('partner.regular.evaluator', string="Partner Regular Evaluator", index=True, ondelete='cascade')
    regular_evaluation_id = fields.Many2one('partner.regular.evaluation.line', string='Partner Regular Evaluation Line')


class AdminPurchaseOrganization(models.Model):
    _name = "admin.purchase.organization"
    _description = "Purchase Organization"

    name = fields.Char(string="Description", required=True)
    code = fields.Char(string='Code')


class AdminWHTaxCode(models.Model):
    _name = "admin.wh.tax.code"
    _description = "WH Tax Code"

    name = fields.Char(string="Description", required=True)
    code = fields.Char(string='Code')
