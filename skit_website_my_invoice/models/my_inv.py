# -*- coding: utf-8 -*-
from odoo import models


class AdminSalesInvoice(models.Model):
    _name = 'admin.sales.invoice'
    _inherit = ['admin.sales.invoice', 'portal.mixin']

    def _compute_access_url(self):
        super(AdminSalesInvoice, self)._compute_access_url()
        for invoice in self:
            invoice.access_url = '/my/myinvoice/%s' % (invoice.id)
