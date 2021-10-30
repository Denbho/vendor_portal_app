# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AdminPurchaseRequisition(models.Model):
    _inherit = "admin.purchase.requisition"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.env.user.plant_ids:
            args.append(('warehouse_id','in', self.env.user.plant_ids.ids))
        return super(AdminPurchaseRequisition, self)._search(args, offset=offset, limit=limit, order=order,
                                            count=count, access_rights_uid=access_rights_uid)


class PurchaseRequisitionMaterialDetails(models.Model):
    _inherit = 'purchase.requisition.material.details'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.env.user.plant_ids:
            args.append(('warehouse_id','in', self.env.user.plant_ids.ids))
        return super(PurchaseRequisitionMaterialDetails, self)._search(args, offset=offset, limit=limit, order=order,
                                            count=count, access_rights_uid=access_rights_uid)
