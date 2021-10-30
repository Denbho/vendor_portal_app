from odoo import fields, models, api
from odoo.exceptions import Warning

class AdminSetMassSourcing(models.TransientModel):
    _name = 'admin.set.mass.sourcing'
    _description = 'Admin Set Mass Sourcing'

    sourcing = fields.Selection(selection=[('bidding', 'Bidding'), ('rfq', 'RFQ'), ('rfp', 'RFP')],
                                string='Sourcing', required=True)

    def btn_set_mass_sourcing(self):
        context = self.env.context
        active_model = context['active_model']
        active_ids = context['active_ids']
        for line in self.env[active_model].sudo().browse(active_ids):
            if line.bid_id and self.sourcing == 'rfq':
                raise Warning("You can't changed the sourcing of %s to RFQ because it is already linked to bidding/rfp." % line.product_id.name)
            if line.rfq_id and self.sourcing == 'bidding':
                raise Warning("You can't changed the sourcing of %s to bidding because it is already linked to rfq/rfp." % line.product_id.name)
            line.sourcing = self.sourcing
        return {'type': 'ir.actions.act_window_close'}
