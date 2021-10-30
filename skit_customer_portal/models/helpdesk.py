from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    property_sale_id = fields.Many2one('property.admin.sale',
                                       string="Property",
                                       store=True,
                                       compute="_get_property_sale",
                                       inverse="_get_inverse_property_sale")

    def _get_inverse_property_sale(self):
        for r in self:
            r.so_number = r.property_sale_id.so_number
