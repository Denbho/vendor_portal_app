# -*- coding: utf-8 -*-

from odoo import fields, api, models, _


class AutoBackupConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(AutoBackupConfigSettings, self).get_values()
        res['autobackup_enabled'] = self.env['ir.config_parameter'].sudo(). \
            get_param('database_autobackup.autobackup_enabled', default=False)
        res['db_name'] = self.env['ir.config_parameter'].sudo().get_param('database_autobackup.db_name',
                                                                          default='')
        res['master_pwd'] = self.env['ir.config_parameter'].sudo().get_param('database_autobackup.master_pwd',
                                                                             default='')
        res['backup_dir'] = self.env['ir.config_parameter'].sudo().get_param('database_autobackup.backup_dir',
                                                                             default='')
        res['backup_format'] = self.env['ir.config_parameter'].sudo().get_param('database_autobackup.backup_format',
                                                                                default='zip')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('database_autobackup.autobackup_enabled',
                                                         self.autobackup_enabled)
        self.env['ir.config_parameter'].sudo().set_param('database_autobackup.db_name',
                                                         self.db_name)
        self.env['ir.config_parameter'].sudo().set_param('database_autobackup.master_pwd',
                                                         self.master_pwd)
        self.env['ir.config_parameter'].sudo().set_param('database_autobackup.backup_dir',
                                                         self.backup_dir)
        self.env['ir.config_parameter'].sudo().set_param('database_autobackup.backup_format',
                                                         self.backup_format)
        super(AutoBackupConfigSettings, self).set_values()

    autobackup_enabled = fields.Boolean(string="Auto Backup Enabled?",
                                        config_parameter='database_autobackup.default_autobackup_enabled')
    db_name = fields.Char(string="Database Name")
    master_pwd = fields.Char(string="Odoo Master Password")
    backup_dir = fields.Char(string="Backup Directory")
    backup_format = fields.Selection([('zip', 'ZIP (includes filestore)'), ('dump', 'Dump File')],
                                     string="Backup Format", default='zip')
