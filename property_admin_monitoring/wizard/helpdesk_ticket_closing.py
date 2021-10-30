# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, date, timedelta

class AdminHelpdeskTicketClosing(models.TransientModel):
    _name = 'admin.helpdesk.ticket.closing'
    _description = "Admin Helpdesk Ticket Closing"

    ticket_id = fields.Many2one("helpdesk.ticket", string="Ticket", required=True)
    remarks = fields.Text(string="Remarks")

    def close_stage(self):
        self.ticket_id.update({
            'remarks': self.remarks,
            'completed_by_id': self.env.user,
            'completion_date': datetime.now(),
        })
        return {'type': 'ir.actions.act_window_close'}
