# -*- coding: utf-8 -*-

from odoo import fields, models


class PropertyAdminSale(models.Model):
    _inherit = 'property.admin.sale'

    so_date = fields.Date(string="SO Date",
                          default=fields.Datetime.now,
                          required=True,
                          track_visibility="always")

    def _compute_access_url(self):
        super(PropertyAdminSale, self)._compute_access_url()
        for property_sale in self:
            property_sale.access_url = '/my/property_sale/%s' % property_sale.id

    def human_readable_number_format(self, amount):
        amount = amount
        magnitude = 0
        while abs(amount) >= 1000:
            magnitude += 1
            amount /= 1000.0
        readable_number = '%.2f%s' % (amount,
                                      ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
        return readable_number
