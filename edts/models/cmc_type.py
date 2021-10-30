# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdtsCmcType(models.Model):
    _name = 'edts.cmc.type'
    _description = 'EDTS CMC Type'
    _order = 'sequence, id'

    name = fields.Char(string='CMC Type')
    sequence = fields.Integer(default=10)
    cmc_type = fields.Char(string='CMC Type')
    cmc_desc = fields.Char(string='CMC Desc')

    @api.model
    def create(self, vals):
        record = super(EdtsCmcType, self).create(vals)
        record.onchange_edts_cmc_type_name()
        return record

    @api.onchange('cmc_type', 'cmc_desc')
    def onchange_edts_cmc_type_name(self):
        for record in self:
            if record.cmc_type or record.cmc_desc:
                self.name = '[%s] %s' % (record.cmc_type, record.cmc_desc)
