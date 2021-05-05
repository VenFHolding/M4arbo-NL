from odoo import api, fields, models, _


class AppointmentHistoryReport(models.TransientModel):
    _name = "appointment.history.report"
    _desc = "Appointment History Xlsx Report"

    partner_ids = fields.Many2many('res.partner', string="Company")
    max_age = fields.Integer(string="Max Age")
    min_age = fields.Integer(string="Min Age")
    covid_status = fields.Selection(
        [('positive', 'Positive'),
         ('negative', 'Negative')], string="Covid Status")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    appointment_max_date = fields.Date(string="Appointment Max Date")
    appointment_min_date = fields.Date(string="Appointment Min Date")

    @api.onchange('partner_ids')
    def onchange_partner_ids(self):
        # Applied domain in partner ids to show only company records.
        partner_recs = self.env['res.partner'].search([])
        company_partner_recs = partner_recs.filtered(lambda partner:partner.company_type == 'company' and partner.appointment_centre_ids)
        domain = [('id', 'in', company_partner_recs.ids)]
        return {'domain': {'partner_ids': domain}}

    def get_calendar_event_domain(self):
        domain = []
        if self.appointment_max_date:
            date_to = str(self.appointment_max_date) + " 23:59:59"
            domain += [('start_datetime', '<=', date_to)]
        if self.appointment_min_date:
            date_from = str(self.appointment_min_date) + " 00:00:00"
            domain += [('start_datetime', '>=', date_from)]
        return domain

    def get_partner_domain(self):
        partner_ids = []
        if self.partner_ids:
            partner_recs = self.partner_ids
        else:
            partner_recs = self.env['res.partner'].search([])
        company_partner_recs = partner_recs.filtered(lambda partner:partner.company_type == 'company')

        domain = [('parent_id', 'in', company_partner_recs.ids)]
        if self.max_age:
            domain += [('age', '<=', self.max_age)]
        if self.min_age:
            domain += [('age', '>=', self.min_age)]
        if self.gender:
            domain += [('gender', '=', self.gender)]
        if self.covid_status and self.covid_status == 'positive':
            sql = """
                SELECT er1.partner_id FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
                LEFT JOIN event_report AS er2 ON er2.id = er1.id
                WHERE er2.state = 'positive'
            """
            self.env.cr.execute(sql)
            partner_ids_data = self.env.cr.fetchall()
            partner_ids += [partner[0] for partner in partner_ids_data]
        if self.covid_status and self.covid_status == 'negative':
            sql = """
                SELECT er1.partner_id FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
                LEFT JOIN event_report AS er2 ON er2.id = er1.id
                WHERE er2.state = 'negative'
            """
            self.env.cr.execute(sql)
            partner_ids_data = self.env.cr.fetchall()
            partner_ids += [partner[0] for partner in partner_ids_data]
        if partner_ids:
            domain += [('id', 'in', partner_ids)]

        return domain

    def get_xlsx_data(self):
        partner_rec = self.env['res.partner'].search([], limit=1)
        xlsx_data = partner_rec.get_xlsx_report(appointment_history_id=self.id)
        return xlsx_data

    def download_covid_xlsx_report(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/covid_report_history/download/excel/' + str(self.id),
        }
