# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import os
import logging

_logger = logging.getLogger(__name__)


class AutoBackupScheduler(models.Model):
    _name = 'autobackup.scheduler'
    _description = 'Auto Backup Scheduler'

    @api.model
    def cron_database_autobackup(self):
        _logger.info(":::: Autobackup Cron Started ::::")
        params = self.env['ir.config_parameter'].sudo()
        autobackup_enabled = params.get_param('database_autobackup.autobackup_enabled', default=False)
        if autobackup_enabled:
            time_now = str(fields.Datetime.now(self)).replace(' ', '_')
            db_name = params.get_param('database_autobackup.db_name', default='')
            master_pwd = params.get_param('database_autobackup.master_pwd', default='')
            backup_dir = params.get_param('database_autobackup.backup_dir', default='')
            backup_format = params.get_param('database_autobackup.backup_format', default='')
            server_url = params.get_param('web.base.url')
            if backup_dir and backup_dir[-1] != '/':
                backup_dir += '/'
            command = 'curl --insecure  -X POST -F "master_pwd=%s" -F "name=%s" -F "backup_format=%s" ' \
                      '-o %s%s_%s_db.%s %s/web/database/backup' % (master_pwd, db_name, backup_format,
                                                                   backup_dir, db_name, time_now,
                                                                   backup_format, server_url)
            unix_code = os.system(command)
            _logger.info(":::: Autobackup Cron Feedback Unix Code (Backup): %s ::::" % unix_code)
        _logger.info(":::: Autobackup Cron Finished ::::")
