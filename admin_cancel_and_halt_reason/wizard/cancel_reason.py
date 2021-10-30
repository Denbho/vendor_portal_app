from odoo import fields, models, api
from odoo.exceptions import Warning

class AdminCancelReason(models.TransientModel):
    _name = 'admin.cancel.reason'
    _description = 'Admin Cancelation Reason'

    reason_id = fields.Many2one('admin.cancel.and.halt.reason', string='Reason', required=True)
    description = fields.Text(string='Description')

    @api.onchange('reason_id')
    def onchange_reason_id(self):
        if self.reason_id:
            self.description = self.reason_id.description

    def btn_cancel(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].sudo().browse(active_id)
        active_entry.write({
            'cancel_reason_id': self.reason_id.id,
            'cancel_description': self.description,
        })
        if active_model == 'purchase.bid':
            m_subject = 'Cancelation of Bidding: '+ active_entry.name
            for line in active_entry.vendor_line:
                if not line.is_kicked and line.state not in ['decline', 'cancel']:
                    line.state = 'bidding_cancel'
                    if active_entry.state != 'send_bid_invitation':
                        line.send_admin_email_notif('bid_cancelation', m_subject, line.partner_id.email, 'purchase.bid.vendor')
            active_entry.state = 'cancel'
        elif active_model == 'admin.request.for.quotation':
            active_entry.state = 'canceled'
            m_subject = 'Cancelation of RFQ: '+ active_entry.name
            rfq_vendors = self.env['admin.vendor.rfq'].sudo().search([
                                    ('rfq_id','=',active_entry.id),
                                    ('state','not in',['declined', 'canceled'])])
            for line in rfq_vendors:
                line.state = 'canceled'
                line.send_admin_email_notif('rfq_cancelation', m_subject, line.partner_id.email, 'admin.vendor.rfq')
            for ln in active_entry.rfq_line_ids:
                ln.state = 'cancel'
        elif active_model == 'admin.request.for.proposals':
            active_entry.state = 'canceled'
            m_subject = 'Cancelation of RFP: '+ active_entry.name
            rfp_vendors = self.env['admin.request.for.proposal.line'].sudo().search([
                                    ('rfp_id','=',active_entry.id),
                                    ('state','!=','declined')])
            for line in rfp_vendors:
                line.state = 'canceled'
                line.send_admin_email_notif('rfp_cancelation', m_subject, line.partner_id.email, 'admin.request.for.proposal.line')
        elif active_model == 'admin.request.for.information':
            active_entry.state = 'canceled'
            m_subject = 'Cancelation of RFI: '+ active_entry.name
            rfi_vendors = self.env['admin.request.for.information.line'].sudo().search([
                                    ('rfi_id','=',active_entry.id),
                                    ('state','!=','declined')])
            for line in rfi_vendors:
                line.state = 'canceled'
                line.send_admin_email_notif('rfi_cancelation', m_subject, line.partner_id.email, 'admin.request.for.information.line')
        elif active_model == 'partner.evaluation':
            active_entry.state = 'canceled'
        return {'type': 'ir.actions.act_window_close'}
