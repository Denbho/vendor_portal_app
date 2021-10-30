# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class EmployeeeCustomDirectory(models.Model):
    _name = 'emp.custom.directory'
    _inherit = ['mail.thread']
    _rec_name = 'emp_fullname'


    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('emp.custom.directory')

    @api.model
    def year_selection(self):
        year = 1990 
        year_list = []
        while year != 2030: 
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    @api.depends('emp_lname','emp_fname', 'emp_mname')
    def get_fullname(self):
        self.emp_fullname = f"{self.emp_lname or ''}, {self.emp_fname or ''} {self.emp_mname or ''}"#(self.emp_fname or '')+' '+(self.emp_mname or '')+' '+(self.emp_lname or '')

    # # Calculated age based on dob
    # @api.depends('emp_dob')
    # def get_age(self):
    #     if self.emp_dob is not False:
    #         self.emp_age1 = (datetime.today().date() - datetime.strptime(str(self.emp_dob), '%Y-%m-%d').date()) // timedelta(days=365)
    #
    # @api.depends('emp_age1', 'emp_age2')
    # def _get_age_range(self):
    #     for i in self:
    #         if i.emp_age1 and i.emp_age2:
    #             i.emp_range = f"{int(i.emp_age1)} - {int(i.emp_age2)}"

    report_num = fields.Integer('Number')
    report_date = fields.Date('Report Date')
    name = fields.Char('Employee Reference', size=32, readonly=True,
                           default=_get_default_name,
                           track_visibility='onchange')
    emp_lname = fields.Char('Last Name', required=True)
    emp_mname = fields.Char('Middle Name')
    emp_fname = fields.Char('First Name', required=True)

    emp_fullname = fields.Char('Fullname', compute='get_fullname', store=True)

    emp_rank1 = fields.Char('Rank 1')
    emp_rank2 = fields.Char('Rank 2')
    emp_rc = fields.Char('RC')

    emp_brand1 = fields.Char('Brand 1')
    emp_brand2 = fields.Char('Brand 2')

    emp_division = fields.Char('Division')
    emp_region 	= fields.Char('Region')

    emp_proj_handle = fields.Char('Project handled')
    emp_assingment = fields.Char('Office Assignment')

    emp_dep1 = fields.Char('Dept 1')
    emp_dep2 = fields.Char('Dept 2')
    emp_dh = fields.Char('DH')
    emp_los1 = fields.Float('Los 1')
    emp_los2 = fields.Char('Los 2')
    gender = fields.Char(string="Gender", tracking=True)
    emp_cs = fields.Char('CS')

    emp_dob = fields.Date('Date of Birth')

    emp_age1 = fields.Float('Age 1')
    emp_age2 = fields.Char('Age 2')
    emp_range = fields.Char('Range')

    emp_school = fields.Char('School')
    emp_course = fields.Char('Course')
    year = fields.Selection(year_selection, String="Year", default="2020" )

    emp_ver = fields.Float('Ver')
    emp_num = fields.Float('Num')
    emp_abs = fields.Float('Abs')
    emp_iq_average = fields.Float('IQ')
    emp_gpa = fields.Float('Gpa')
    emp_prc = fields.Float('Prc')
    emp_rating = fields.Float('Rating')
    emp_award = fields.Char('Awards')
    emp_other_award = fields.Text('Other Awards')

    emp_payroll_comp = fields.Char('Payroll Company')
    emp_last_appraisal = fields.Char('Last Appraisal')
    emp_rating = fields.Float('Rating')
    emp_us_batch = fields.Char('US Batch')
    emp_status = fields.Char('Status')

    emp_separation = fields.Char('SEPARATION REASON')
    emp_separtion2 = fields.Char('SEPARATION REASON 2')
    emp_head = fields.Char('Head')
    emp_supervisor = fields.Char('TL/Supervisor')
    emp_separation_date = fields.Date('Separation Date')
    emp_transfer_type = fields.Char('Transfer Type')
    emp_trasnfer_from = fields.Char('Transfer From/To Brand')
    emp_trasnfer_loc = fields.Char('Transfer From/To_Location')
    emp_trasnfer_position = fields.Char('Transfer From/To_Position')
    emp_transfer_date = fields.Date('Transfer Date')

    # dyob = fields.Integer("Day of Birth", compute='_compute_yy_mm_of_birth', store=True, index=True,
    #                       help="The day of birth from the Date of Birth.")
    # mob = fields.Integer(string='Month of Birth', compute='_compute_yy_mm_of_birth', store=True, index=True,
    #                      help="The month of birht from the Date of Birth.")
    # yob = fields.Integer(string='Year of Birth', compute='_compute_yy_mm_of_birth', store=True, index=True,
    #                      help="The year of birth from the Date of Birth.")
    # age = fields.Integer(string="Age", readonly=True)
    # age_range_id = fields.Many2one('res.partner.age.range', string="Age Range")
    # calendar_birthday = fields.Date(string="Calendar Birthday", readonly=True)
    # birthday = fields.Date(string="Date of Birth")
    # marital = fields.Selection([
    #     ('single', 'Single'),
    #     ('married', 'Married'),
    #     ('cohabitant', 'Legal Cohabitant'),
    #     ('widower', 'Widowed'),
    #     ('divorced', 'Divorced'),
    #     ('separated', 'Separated'),
    #     ('annulled', 'Annulled')
    # ], string='Marital Status', tracking=True)

    def cron_calendar_birthday(self):
        current_year, current_month, current_day = self.split_date(date.today() - timedelta(days=1))
        employee = self.search([
            ('mob', '=', current_month),
            ('dyob', '=', current_day)
        ])
        for i in employee:
            i.write({
                'calendar_birthday': date.today() - relativedelta(days=1) + relativedelta(years=1)
            })

    def cron_compute_age(self):
        current_year, current_month, current_day = self.split_date(date.today())
        employee = self.search([
            ('mob', '=', current_month),
            ('dyob', '=', current_day)
        ])
        for i in employee:
            age = date.today().year - i.birthday.year
            age_range = self.env['res.partner.age.range'].search(
                [('range_from', '<=', age), ('range_to', '>=', age)], limit=1)
            i.write({
                'age': age,
                'age_range_id': age_range[:1] and age_range.id or False
            })

    @api.model
    def create(self, vals):
        if vals.get('birthday'):
            bday = datetime.strptime(vals.get('birthday'), "%Y-%m-%d")
            current_year, current_month, current_day = self.split_date(bday)
            age = date.today().year - bday.year
            age_range = self.env['res.partner.age.range'].search(
                [('range_from', '<=', age), ('range_to', '>=', age)], limit=1)
            vals.update({
                'age': age,
                'age_range_id': age_range[:1] and age_range.id or False
            })
            calendar_birthday = datetime.strptime(f"{date.today().year}-{current_month}-{current_day}", "%Y-%m-%d")
            if calendar_birthday <= datetime.now():
                calendar_birthday = calendar_birthday + relativedelta(years=1)
            vals['calendar_birthday'] = calendar_birthday
        return super(EmployeeeCustomDirectory, self).create(vals)

    def write(self, vals):
        if 'birthday' in vals and vals.get('birthday'):
            bday = datetime.strptime(vals.get('birthday'), "%Y-%m-%d")
            current_year, current_month, current_day = self.split_date(bday)
            age = date.today().year - bday.year
            age_range = self.env['res.partner.age.range'].search(
                [('range_from', '<=', age), ('range_to', '>=', age)], limit=1)
            vals.update({
                'age': age,
                'age_range_id': age_range[:1] and age_range.id or False
            })
            calendar_birthday = datetime.strptime(f"{date.today().year}-{current_month}-{current_day}", "%Y-%m-%d")
            if calendar_birthday <= datetime.now():
                calendar_birthday = calendar_birthday + relativedelta(years=1)
            vals['calendar_birthday'] = calendar_birthday
        return super(EmployeeeCustomDirectory, self).write(vals)

    @api.depends('birthday')
    def _compute_yy_mm_of_birth(self):
        for r in self:
            if not r.birthday:
                r.mob = False
                r.yob = False
                r.dyob = False
            else:
                year, month, day = self.split_date(fields.Date.from_string(r.birthday))
                r.dyob = day
                r.mob = month
                r.yob = year

    def split_date(self, date):
        """
        Method to split a date into year,month,day separatedly
        @param date date:
        """
        year = date.year
        month = date.month
        day = date.day
        return year, month, day








