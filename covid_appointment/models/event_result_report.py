from odoo import api, fields, models, tools


class AppointmentReport(models.Model):
    _name = "covid.appointment.result.report"
    _description = "Covid Appointment Result Report"
    _auto = False

    partner_company_id = fields.Many2one('res.partner', string="Company")
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other')], string="Gender")
    appointment_type_id = fields.Many2one('calendar.appointment.type',
                                          string="Test Center")
    total = fields.Integer(string="Total")
    coid_status = fields.Selection([('positive', 'Positive'),
                                    ('negative', 'Negative')],
                                    string="Result")
    partner_id = fields.Many2one('res.partner', string="Patient")
    email = fields.Char(string="Email")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT ROW_NUMBER () OVER () AS id,
                company.id AS partner_company_id,
                apt_type.id AS appointment_type_id,
                partner.gender AS gender,
                partner.email AS email,
                partner.id AS partner_id,
                report.state AS coid_status,
                count(*) as total
                FROM calendar_event AS event
                LEFT JOIN calendar_appointment_type AS apt_type ON apt_type.id = event.appointment_type_id
                LEFT JOIN event_report AS report on report.calendar_event_id = event.id
                LEFT JOIN calendar_appointment_type_res_partner_rel AS ap_type_partner_rel ON apt_type.id = ap_type_partner_rel.calendar_appointment_type_id
                LEFT JOIN res_partner AS company on company.id = ap_type_partner_rel.res_partner_id
                LEFT JOIN calendar_event_res_partner_rel AS event_partner_rel ON event_partner_rel.calendar_event_id = event.id
                LEFT JOIN res_partner AS partner on partner.id = event_partner_rel.res_partner_id
                WHERE event.state = 'done' and event.appointment_type_id IS NOT NULL AND partner.gender IS NOT NULL
                GROUP BY company.id, apt_type.id, 
                partner.gender, report.state, partner.id
            )''' % (self._table,))
