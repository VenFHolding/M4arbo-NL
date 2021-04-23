import io
from odoo import api, fields, models
from datetime import datetime, timedelta
import xlsxwriter


class InheritPartner(models.Model):
    _inherit = "res.partner"    

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """
            On Test Centre Login, displayed only test centre's partner.
        """
        user = self.env.user
        if user.user_has_groups('covid_appointment.group_appointment_own_document') and not user.user_has_groups('website_calendar.group_calendar_manager'):
            domain += [('id', '=', user.partner_id.id)]
        return super(InheritPartner, self).search_read(domain, fields, offset, limit, order)

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
        partner_detail_format = workbook.add_format({'bold': True, 'font_name': 'Liberation Sans', 'bg_color': '#807e7e', 'font_color': '#ffffff'})
        partner_detail_data_format = workbook.add_format({'font_name': 'Liberation Sans', 'bg_color': '#807e7e', 'font_color': '#ffffff', 'align': 'left'})
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 27)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 20)
        sheet.merge_range(0, 0, 1, 6, 'Employee’s Covid Status Report', header_format)

        # Write Data
        row = 3
        for partner_rec in self.child_ids:
            col = 0
            sr_no = 1
            sheet.write(row, col, "Name", partner_detail_format)
            sheet.write(row, col+1, partner_rec.name, partner_detail_data_format)
            sheet.write(row, col+2, "Gender", partner_detail_format)
            gender = partner_rec.gender
            if gender:
                gender = gender.capitalize()
            sheet.write(row, col+3, gender, partner_detail_data_format)
            sheet.write(row, col+4, "Contact No.", partner_detail_format)
            sheet.write(row, col+5, partner_rec.mobile, partner_detail_data_format)
            row += 1
            sheet.write(row, col, "Email", partner_detail_format)
            sheet.write(row, col+1, partner_rec.email, partner_detail_data_format)
            sheet.write(row, col+2, "Age", partner_detail_format)
            sheet.write(row, col+3, partner_rec.age, partner_detail_data_format)
            row += 1
            sheet.write(row, col, "Sr. No.", table_header_format)
            sheet.write(row, col+1, "Appointment ID", table_header_format)
            sheet.write(row, col+2, "Appointment Date", table_header_format)
            sheet.write(row, col+3, "Test Centre", table_header_format)
            sheet.write(row, col+4, "Appointment Status", table_header_format)
            sheet.write(row, col+5, "Covid Status", table_header_format)
            row += 1

            calendar_event_recs = self.env['calendar.event'].sudo().search(
                [('patient_partner_id', '=', partner_rec.id)])
            for event_rec in calendar_event_recs:
                covid_status = event_rec.covid_status
                if covid_status:
                    covid_status = covid_status.capitalize()
                sheet.write(row, col, sr_no)
                sheet.write(row, col+1, event_rec.event_name)
                sheet.write(row, col+2, str(event_rec.start_datetime))
                sheet.write(row, col+3, event_rec.appointment_type_id.name)
                sheet.write(row, col+4, event_rec.state)
                sheet.write(row, col+5, covid_status or '')
                row += 1
                sr_no += 1

            row += 1

        workbook.close()
        output.seek(0)
        data = output.read()
        return data
