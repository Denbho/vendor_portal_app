# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _

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
    tin = fields.Char(string='TIN')
    registration_date = fields.Date(string='Registration Date')
    product_category_ids = fields.Many2many('product.category', string='Product Categories')
    product_service_offered_line = fields.One2many('product.service.offered', 'partner_id',
                                                   string='Products/Services Offered')
    document_ids = fields.Many2many('pre.bid.documents', string='Documents')
    date_accredited = fields.Date(string='Date Accredited', track_visibility="always")
    start_date = fields.Date(string='Start Date', track_visibility="always")
    end_date = fields.Date(string='End Date', track_visibility="always")
    evaluation_period = fields.Date(string='Evaluation Period', track_visibility="always")
    overall_assessment = fields.Float(string='Overall Assessment', track_visibility="always")
    extend_result = fields.Boolean(string='Extend Result to Vendor?', track_visibility="always")
    show_accredit_button = fields.Boolean(compute='_compute_show_accredit_button', string='Show Accredit Button')

    # @api.onchange('product_category_id')
    # def onchange_product_category_id(self):
    #     self.ensure_one()
    #     if self.product_category_id:
    #         categ_ids = [ line.id for line in self.partner_id.product_category_ids]
    #         if self.product_category_id.id not in categ_ids:
    #             categ_ids.append(self.product_category_id.id)
    #             self.partner_id.write({'product_category_ids': [(6, 0, categ_ids)]})
    # self.partner_id.write({'product_category_ids': [(4, self.product_category_id.id)]})

    # def write(self, values):
    #     res = super(ResPartner, self).write(values)
    #     if 'product_category_ids' in values:
    #         raise Warning(values)
    #         Warning: {
    #         'product_category_ids': [[6, False, [2, 4]]],
    #         'product_service_offered_line':
    #             [[4, 1, False],
    #             [1, 2, {'product_category_id': 2}],
    #         update - [1, 3, {'product_category_id': 1}],
    #             [4, 4, False],
    #         bago -  [0, 'virtual_968', {'display_type': False, 'sequence': 14, 'product_service': 'Paint', 'name': 'Paint 5', 'product_category_id': 4, 'price': 200}]]}
    #     return res

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


class PartnerEvaluation(models.Model):
    _name = "partner.evaluation"
    _description = "Partner Evaluation"

    def _compute_evaluator_count(self):
        for rec in self:
            self.evaluator_count = len(rec.evaluator_line)

    name = fields.Char(related='partner_id.name', string='Name')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    evaluator_line = fields.One2many('partner.evaluator', 'partner_evaluation_id', string='Evaluator Line')
    evaluator_count = fields.Integer(compute='_compute_evaluator_count', string='Evaluator Count')
    # Technical Evaluation
    evaluation_line = fields.One2many('partner.evaluation.line', 'partner_evaluation_id', string='Technical Evaluation',
                                      copy=True, domain=[('type', '=', 'technical')])
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
    commercial_evaluation_line = fields.One2many('partner.evaluation.line', 'partner_evaluation_id',
                                                 string='Commercial Evaluation', copy=True,
                                                 domain=[('type', '=', 'commercial')])
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
    _description = "Partner Evaluator"

    name = fields.Char(related='evaluator_id.name', string='Name')
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, required=True)
    partner_evaluation_id = fields.Many2one('partner.evaluation', string="Partner Evaluation")
    evaluation_line = fields.One2many('partner.evaluator.line', 'partner_evaluator_id', string='Evaluation', copy=True)
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Evaluation Type')

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
            'end_date': self.end_date
        })


class ProductServiceOffered(models.Model):
    _name = 'product.service.offered'
    _description = 'Products/Services Offered'

    name = fields.Char(string="Product/Service Description", required=True)
    product_service = fields.Char(string="Product/Service")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    sequence = fields.Integer(string='Sequence', default=10)
    price = fields.Float(string="Price")
    product_category_id = fields.Many2one('product.category', string='Product Category')
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')
