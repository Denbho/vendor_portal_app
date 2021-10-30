from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.exceptions import Warning

class AdminSelectTypeOfEvaluation(models.TransientModel):
    _name = 'admin.select.type.of.evaluation'
    _description = 'Select Type of Evaluation'

    @api.model
    def default_get(self, default_fields):
        res = super(AdminSelectTypeOfEvaluation, self).default_get(default_fields)
        if 'partner_evaluation_id' in res:
            accredit_vendor = self.env['partner.evaluation'].sudo().browse(res['partner_evaluation_id'])
            res.update({
                'company_code': accredit_vendor.partner_id.company_code,
                'vat_type': accredit_vendor.partner_id.vat_type,
                'is_subject_to_wh_tax': accredit_vendor.partner_id.is_subject_to_wh_tax,
                'wh_tax_code_id': accredit_vendor.partner_id.wh_tax_code_id and accredit_vendor.partner_id.wh_tax_code_id.id or False,
                'purchase_org_id': accredit_vendor.partner_id.purchase_org_id and accredit_vendor.partner_id.purchase_org_id.id or False,
                'vendor_account_group_id': accredit_vendor.partner_id.vendor_account_group_id and accredit_vendor.partner_id.vendor_account_group_id.id or False,
                'property_supplier_payment_term_id': accredit_vendor.partner_id.property_supplier_payment_term_id and accredit_vendor.partner_id.property_supplier_payment_term_id.id or False,
            })
        return res

    partner_evaluation_id = fields.Many2one('partner.evaluation', string="Partner Evaluation")
    company_code = fields.Char(string="Company Code", required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True)
    vat_type = fields.Selection([('vat', "Vatable"), ('nvat', "Non-vatable")],
                                string='VAT Type', required=True)
    is_subject_to_wh_tax = fields.Boolean(string='Subject to WH Tax?')
    wh_tax_code_id = fields.Many2one('admin.wh.tax.code', string="WH Tax Code")
    purchase_org_id = fields.Many2one('admin.purchase.organization', string="Purchase Organization", required=True)
    vendor_account_group_id = fields.Many2one('vendor.account.group', string="Account Group", required=True)
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', required=True)
    type_of_evaluation = fields.Selection(selection=[
                                        ('monthly', 'Monthly'),
                                        ('quarterly', 'Quarterly'),
                                        ('annual', 'Annual'),
                                        ('semi_annual', 'Semi Annual')],
                                        string="How often should we evaluate this vendor ?")
    evaluation_responsible_ids = fields.Many2many('res.users', 'evaluation_responsible_rel', string='Responsible: ')

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

    @api.onchange('is_subject_to_wh_tax')
    def onchange_is_subject_to_wh_tax(self):
        if not self.is_subject_to_wh_tax:
            self.wh_tax_code_id = False

    def approve(self):
        partner_update = {}
        for line in self.partner_evaluation_id.evaluator_line:
            for ln in line.evaluation_line:
                if not ln.display_type and ln.score == 0:
                    raise Warning("Evaluators must complete evaluation per criteria.")
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
                    new_sched_activity = self.env['mail.activity'].create({
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
