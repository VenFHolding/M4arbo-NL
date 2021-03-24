from odoo import api, fields, models, tools


class AppointmentReport(models.Model):
    _name = "appointment.report"
    _description = "Appointment Report"
    _auto = False

    partner_company_id = fields.Many2one('res.partner', string="Company")
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other')], string="Gender")
    appointment_type_id = fields.Many2one('calendar.appointment.type',
                                          string="Test Center")
    total = fields.Integer(string="Total")
    event_state = fields.Selection([('draft', 'Unconfirmed'),
                                    ('open', 'Confirmed'),
                                    ('done', 'Done'),
                                    ('cancel', 'Cancelled'),
                                    ('not achieved', 'Not Achieved')],
                                    string="State")
    partner_id = fields.Many2one('res.partner', string="Patient")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT ROW_NUMBER () OVER () AS id,
                company.id AS partner_company_id,
                apt_type.id AS appointment_type_id,
                partner.gender AS gender,
                partner.id AS partner_id,
                event.state AS event_state,
                count(*) AS total
                FROM calendar_event AS event
                LEFT JOIN calendar_appointment_type AS apt_type ON apt_type.id = event.appointment_type_id
                LEFT JOIN calendar_appointment_type_res_partner_rel AS ap_type_partner_rel ON apt_type.id = ap_type_partner_rel.calendar_appointment_type_id
                LEFT JOIN res_partner AS company ON company.id = ap_type_partner_rel.res_partner_id
                LEFT JOIN calendar_event_res_partner_rel AS event_partner_rel ON event_partner_rel.calendar_event_id = event.id
                LEFT JOIN res_partner AS partner ON partner.id = event_partner_rel.res_partner_id
                WHERE event.appointment_type_id IS NOT NULL AND partner.gender IS NOT NULL
                GROUP BY company.id, apt_type.id, partner.gender, event.state, partner.id
            )''' % (self._table,))
