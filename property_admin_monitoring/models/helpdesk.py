from odoo import fields, models, api, _


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    project_subdivision_ids = fields.Many2many('property.subdivision.phase', 'helpdesk_team_subdivision_rel', string="Subdivision Project Assignments")
    customer_care_team = fields.Boolean(string="Default Customer Care Team", help="If activated, this will be available in the mobile app as default CCD for the company")
    ticket_type_ids = fields.Many2many('helpdesk.ticket.type', 'helpdesk_team_ticket_type_rel', string="Ticket Types")


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    so_number = fields.Char('Property SO Number')
    property_sale_id = fields.Many2one('property.admin.sale', string="Property")
    be_code = fields.Char(string="BE Code", store=True, related="property_sale_id.be_code")
    project_subdivision_id = fields.Many2one('property.subdivision.phase', string="Subdivision",
                                             store=True, related="property_sale_id.subdivision_phase_id")

    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_name = fields.Char(string='Customer Name', store=True, related="partner_id.name")
    partner_email = fields.Char(string='Customer Email', store=True, related="partner_id.email")

    customer_number = fields.Char(string='Customer Number', store=True, related="property_sale_id.customer_number")
    project_location = fields.Text(string='Project Location', compute='_compute_project_location', store=True)
    unit_type = fields.Char(string='Unit Type', store=True, related="property_sale_id.unit_type")
    block_lot = fields.Char(string='Block-Lot', store=True, related="property_sale_id.block_lot")
    unit_house_model_id = fields.Many2one('housing.model', string='Unit/House Model', store=True, related="property_sale_id.house_model_id")
    floor_area = fields.Float(string='Floor Area', store=True, related="property_sale_id.floor_area")
    lot_area = fields.Char(string='Lot Area')
    move_in_date = fields.Datetime(string='Move In Date')
    acceptance_date = fields.Datetime(string='Acceptance Date')
    house_completion_date = fields.Datetime(string='House Completion Date')
    house_contractor = fields.Char(string='House Contractor')

    department_id = fields.Many2one('hr.department', string='Department')
    completed_by_id = fields.Many2one('res.users', string='Completed By')
    completion_date = fields.Datetime(string='Completion Date')
    ticket_source = fields.Char(string='Ticket Source')
    remarks = fields.Text(string='Remarks')

    @api.depends('project_subdivision_id')
    def _compute_project_location(self):
        for rec in self:
            address = ''
            if rec.project_subdivision_id:
                if rec.project_subdivision_id.street:
                    address += rec.project_subdivision_id.street
                if rec.project_subdivision_id.street2:
                    address += ', '+rec.project_subdivision_id.street2
                if rec.project_subdivision_id.barangay_id:
                    address += ', '+rec.project_subdivision_id.barangay_id.name
                if rec.project_subdivision_id.city_id:
                    address += ', '+rec.project_subdivision_id.city_id.name
                if rec.project_subdivision_id.province_id:
                    address += ', '+rec.project_subdivision_id.province_id.name
                if rec.project_subdivision_id.zip:
                    address += ', '+rec.project_subdivision_id.zip
            rec.project_location = address

    @api.model_create_multi
    def create(self, list_value):
        for vals in list_value:
            if vals.get('property_sale_id'):
                sale = self.env['property.admin.sale'].sudo().browse(vals.get('property_sale_id'))
                vals.update({
                    'so_number': sale.so_number,
                    'partner_id': sale.partner_id and sale.partner_id.id or False,
                })
        return super(HelpdeskTicket, self).create(list_value)

    @api.onchange('so_number', 'team_id')
    def onchange_so_number(self):
        query = [('so_number', '=', self.so_number)]
        if self.team_id:
            if self.team_id.company_id and self.team_id.company_id.sap_client_id:
                query.append(('sap_client_id', '=', self.team_id.company_id.sap_client_id))
        if self.so_number:
            sale = self.env['property.admin.sale'].sudo().search(query, limit=1)
            self.update({
                'property_sale_id': sale.id,
                'partner_id': sale.partner_id and sale.partner_id.id or False
            })

    @api.onchange('property_sale_id')
    def onchange_property_sale_id(self):
        if self.property_sale_id:
            self.update({
                'so_number': self.property_sale_id.so_number,
                'partner_id': self.property_sale_id.partner_id and self.property_sale_id.partner_id.id or False6
            })

    # @api.depends('so_number')
    # def _get_property_sale_partner(self):
    #     property_sale = self.env['property.admin.sale']
    #     for r in self:
    #         property_data = property_sale.sudo().search([('so_number', '=', r.so_number)], limit=1)
    #         r.partner_id = property_data[:1] and property_data.partner_id or False
    #         r.partner_name = property_data[:1] and property_data.partner_id.name or None
    #         r.partner_name = property_data[:1] and property_data.partner_id.email or None
    #
    # def _get_inverse_property_sale_partner(self):
    #     for r in self:
    #         continue
    #
    # @api.depends('so_number')
    # def _get_property_sale(self):
    #     property_sale = self.env['property.admin.sale']
    #     for r in self:
    #         property_data = property_sale.sudo().search([('so_number', '=', r.so_number)], limit=1)
    #         r.property_sale_id = property_data[:1] and property_data.id or False
    #         r.be_code = property_data[:1] and property_data.be_code or None
    #         r.project_subdivision_id = property_data[:1] and property_data.subdivision_phase_id or False
