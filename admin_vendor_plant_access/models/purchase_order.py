# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.env.user.plant_ids:
            args.append(('plant_id','in', self.env.user.plant_ids.ids))
        return super(PurchaseOrder, self)._search(args, offset=offset, limit=limit, order=order,
                                            count=count, access_rights_uid=access_rights_uid)
