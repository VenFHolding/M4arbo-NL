import io
from odoo import api, fields, models
from odoo.http import request
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

    def get_domain(self):
        """
            This function will be called when company user tries to download
            covid report of thier employees.
            This function will returns a domain based on filters, which
            are applied by the user.
        """
        domain = [('parent_id', '=', self.id)]
        calendar_event_domain = []
        partner_ids = []

        # Age filter domain
        if request.session.get('contact_age_filter'):
            min_age = int(request.session.get('contact_age_filter').split('-')[0])
            max_age = int(request.session.get('contact_age_filter').split('-')[1])
            domain += [('age', '>=', min_age), ('age', '<=', max_age)]
        if request.session.get('max_age'):
            domain += [('age', '<=', max_age)]
        if request.session.get('min_age'):
            domain += [('age', '>=', min_age)]
        if request.session.get('gender_filter'):
            gender = request.session.get('gender_filter')
            domain += [('gender', '=', gender)]

        # Covid status domain
        if request.session.get('positive_check'):
            sql = """
                SELECT er1.partner_id FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
                LEFT JOIN event_report AS er2 ON er2.id = er1.id
                WHERE er2.state = 'positive'
            """
            request.env.cr.execute(sql)
            partner_ids_data = request.env.cr.fetchall()
            partner_ids += [partner[0] for partner in partner_ids_data]

        if request.session.get('negative_check'):
            sql = """
                SELECT er1.partner_id FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
                LEFT JOIN event_report AS er2 ON er2.id = er1.id
                WHERE er2.state = 'negative'
            """
            request.env.cr.execute(sql)
            partner_ids_data = request.env.cr.fetchall()
            partner_ids += [partner[0] for partner in partner_ids_data]

        # Appointment Date range domain
        if request.session.get('app_date_from'):
            date_from = request.session.get('app_date_from')
            date_from += " 00:00:00"
            calendar_event_domain += [('start_datetime', '>=', date_from)]
        if request.session.get('app_date_to'):
            date_to = request.session['app_date_to']
            date_to += " 23:59:59"
            calendar_event_domain += [('start_datetime', '<=', date_to)]
        if calendar_event_domain:
            calendar_event_recs = request.env['calendar.event'].sudo().search(calendar_event_domain)
            partner_ids += calendar_event_recs.mapped('partner_ids').ids
        
        if partner_ids:
            domain += [('id', 'in', partner_ids)]

        return domain


    def get_xlsx_report(self, appointment_history_id=False):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Write header
        header_format = workbook.add_format({'align': 'center', 'bold': True, 'valign':   'vcenter', 'font_name': 'Liberation Sans'})
        table_header_format = workbook.add_format({'bold': True, 'border': 1, 'font_name': 'Liberation Sans'})

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 27)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 27)
        sheet.set_column(6, 6, 12)
        sheet.set_column(7, 7, 5)
        sheet.set_column(8, 8, 12)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 23)
        sheet.set_column(12, 12, 17)
        sheet.set_column(13, 13, 15)
        sheet.merge_range(0, 0, 1, 8, 'Employee’s Covid Status Report', header_format)

        # Write Data
        row = 3
        
        col = 0
        sr_no = 1

        sheet.write(row, col, "Sr. No.", table_header_format)
        sheet.write(row, col+1, "Company", table_header_format)
        sheet.write(row, col+2, "Name", table_header_format)
        sheet.write(row, col+3, "Gender", table_header_format)
        sheet.write(row, col+4, "Contact No.", table_header_format)
        sheet.write(row, col+5, "Email", table_header_format)
        sheet.write(row, col+6, "DOB", table_header_format)
        sheet.write(row, col+7, "Age", table_header_format)
        sheet.write(row, col+8, "Appointment ID", table_header_format)
        sheet.write(row, col+9, "Create Date", table_header_format)
        sheet.write(row, col+10, "Appointment Date", table_header_format)
        sheet.write(row, col+11, "Test Centre", table_header_format)
        sheet.write(row, col+12, "Appointment Status", table_header_format)
        sheet.write(row, col+13, "Covid Status", table_header_format)
        row += 1
        
        if appointment_history_id:
            appointment_history_wizard_rec = self.env['appointment.history.report'].browse([appointment_history_id])
            domain = appointment_history_wizard_rec.get_partner_domain()
        else:
            domain = self.get_domain()

        partner_recs = self.sudo().search(domain)
        for partner_rec in partner_recs:
            gender = partner_rec.gender
            if gender:
                gender = gender.capitalize()

            calendar_event_domain = [('patient_partner_id', '=', partner_rec.id)]
            if appointment_history_id:
                user_rec = self.env.user
                appointment_type_recs = False
                if user_rec.user_has_groups('covid_appointment.group_appointment_own_document') and not user_rec.user_has_groups('website_calendar.group_calendar_manager'):
                    appointment_type_recs = self.env['calendar.appointment.type'].search(
                        [('user_id', '=', user_rec.id)])

                appointment_history_wizard_rec = self.env['appointment.history.report'].browse([appointment_history_id])
                calendar_event_domain += appointment_history_wizard_rec.get_calendar_event_domain()
                calendar_event_recs = self.env['calendar.event'].sudo().search(calendar_event_domain)
                if appointment_history_wizard_rec.covid_status and appointment_history_wizard_rec.covid_status == 'positive':
                    calendar_event_recs = calendar_event_recs.filtered(lambda event: event.covid_status == 'positive')
                if appointment_history_wizard_rec.covid_status and appointment_history_wizard_rec.covid_status == 'negative':
                    calendar_event_recs = calendar_event_recs.filtered(lambda event: event.covid_status == 'negative')
                if appointment_type_recs:
                    calendar_event_recs = calendar_event_recs.filtered(lambda event: event.appointment_type_id.id in appointment_type_recs.ids)

            else:
                if request.session.get('app_date_from'):
                    date_from = request.session.get('app_date_from')
                    date_from += " 00:00:00"
                    calendar_event_domain += [('start_datetime', '>=', date_from)]
                if request.session.get('app_date_to'):
                    date_to = request.session['app_date_to']
                    date_to += " 23:59:59"
                    calendar_event_domain += [('start_datetime', '<=', date_to)]

                calendar_event_recs = self.env['calendar.event'].sudo().search(calendar_event_domain)

                if request.session.get('positive_check'):
                    calendar_event_recs = calendar_event_recs.filtered(lambda event: event.covid_status == 'positive')
                if request.session.get('negative_check'):
                    calendar_event_recs = calendar_event_recs.filtered(lambda event: event.covid_status == 'negative')

            for event_rec in calendar_event_recs:
                covid_status = event_rec.covid_status
                if covid_status:
                    covid_status = covid_status.capitalize()
                sheet.write(row, col, sr_no)
                sheet.write(row, col+1, partner_rec.parent_id.name)
                sheet.write(row, col+2, partner_rec.name)
                sheet.write(row, col+3, gender)
                sheet.write(row, col+4, partner_rec.mobile)
                sheet.write(row, col+5, partner_rec.email)
                sheet.write(row, col+6, partner_rec.dob.strftime('%d-%m-%Y'))
                sheet.write(row, col+7, partner_rec.age)
                sheet.write(row, col+8, event_rec.event_name)
                sheet.write(row, col+9, event_rec.create_date.strftime('%d-%m-%Y %H:%M'))
                sheet.write(row, col+10, event_rec.start_datetime.strftime('%d-%m-%Y %H:%M'))
                sheet.write(row, col+11, event_rec.appointment_type_id.name)
                sheet.write(row, col+12, event_rec.state)
                sheet.write(row, col+13, covid_status or '')
                row += 1
                sr_no += 1

        workbook.close()
        output.seek(0)
        data = output.read()
        return data
