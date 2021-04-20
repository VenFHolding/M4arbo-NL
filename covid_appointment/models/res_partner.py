import io
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.tools.misc import xlsxwriter


class InheritPartner(models.Model):
    _inherit = "res.partner"

    def _cron_execute_update_age(self):
        partner_recs = self.search([('company_type', '=', 'person'),
                                    ('type', '=', 'contact'),
                                    ('dob', '!=', False)])
        partner_recs.calculate_age()

    def get_partner_age(self):
        today = datetime.now().date()
        age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return age

    @api.depends('dob')
    def calculate_age(self):
        """
            Calculate the age based on the date of birth and the today's date.
        """
        for partner_rec in self:
            partner_rec.age = 0
            if partner_rec.dob:
                partner_age = partner_rec.get_partner_age()
                partner_rec.age = partner_age


    gender = fields.Selection([('male', 'Male'), ('female', 'Female'),
                               ('other', 'Other')], string="Gender", placeholder="Gender")
    dob = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute="calculate_age", store=True)
    appointment_centre_ids = fields.Many2many('calendar.appointment.type', string='Select Test Centre *')
    restrict_country_ids = fields.Many2many(
        'res.country', string="Restrict Countries",
        help="Keep empty to display all countries on create appointment, otherwise you display selected countries.")
    add_all_test_centre = fields.Boolean(string="Add All Test Centre")

    @api.onchange('add_all_test_centre')
    def _onchange_add_all_test_centre(self):
        """
            This method will filter out the partners which company type will be company.
            And add all the covid test center in the test center column.
        """
        if self.add_all_test_centre:
            appointment_centre_ids = self.env['calendar.appointment.type'].search(
                [('is_published', '=', True)]).ids
            self.appointment_centre_ids = [(6, 0, appointment_centre_ids)] 

    def appointmet_verify_check(self, Partner, date_start):
        """ verify appointment validity """
        data_dict = {}
        message = ''
        covid_positive_date_start = date_start - timedelta(days=14)
        if Partner:
            partner_report = self.env['event.report'].sudo().search([('partner_id', '=', Partner.id),
                                                                     ('create_date', '>=', covid_positive_date_start),
                                                                     ('state', '=', 'positive')])
            if partner_report:
                message += "You are Restricted to test for 14 days since your result was Positive."
                data_dict['message'] = message
                return data_dict

            date_start = date_start - timedelta(hours=48)
            domain = [('state', '=', 'open'),
                      ('appointment_type_id', '!=', False),
                      ('patient_partner_id', '=', Partner.id),
                      ('start_datetime', '>', date_start)]
            partner_event = self.env['calendar.event'].sudo().search(domain)
            if partner_event:
                message += "The Appointment is already scheduled for you. \n " \
                                    "You can Cancel the prior appointment and reschedul it again."
                data_dict['message'] = message
                return data_dict

        return data_dict

    def get_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Write header
        header_format = workbook.add_format({'align': 'center', 'bold': True, 'valign':   'vcenter', 'font_name': 'Liberation Sans'})
        table_header_format = workbook.add_format({'bold': True, 'border': 1, 'font_name': 'Liberation Sans'})
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 25)
        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.merge_range(0, 0, 1, 6, 'Employee’s Covid Status Report', header_format)
        sheet.write(3, 0, "Sr. No.", table_header_format)
        sheet.write(3, 1, "Name", table_header_format)
        sheet.write(3, 2, "Gender", table_header_format)
        sheet.write(3, 3, "Age", table_header_format)
        sheet.write(3, 4, "Last Appointment Date", table_header_format)
        sheet.write(3, 5, "Test Centre", table_header_format)
        sheet.write(3, 6, "Covid Status", table_header_format)

        # Write Data
        sql_query = """
            SELECT er1.partner_id AS partner_id,
            er2.state AS covid_status,
            er2.calendar_event_id AS event_id
            FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
            LEFT JOIN event_report AS er2 ON er2.id = er1.id
        """
        self._cr.execute(sql_query)
        appointment_report_data = self._cr.dictfetchall()
        sr_no = 1
        row = 4
        col = 0
        for report_data in appointment_report_data:
            partner_rec = self.env['res.partner'].browse([report_data.get('partner_id')])
            calendar_event_rec = self.env['calendar.event'].sudo().browse([report_data.get('event_id')])
            sheet.write(row, col, sr_no)
            sheet.write(row, col+1, partner_rec.name)
            sheet.write(row, col+2, partner_rec.gender.capitalize())
            sheet.write(row, col+3, partner_rec.age)
            sheet.write(row, col+4, str(calendar_event_rec.start_datetime))
            sheet.write(row, col+5, calendar_event_rec.appointment_type_id.name)
            sheet.write(row, col+6, report_data.get('covid_status').capitalize())
            sr_no += 1
            row += 1

        workbook.close()
        output.seek(0)
        data = output.read()
        return data
