from odoo import api, fields, models
from datetime import datetime, timedelta


class InheritPartner(models.Model):
    _inherit = "res.partner"

    def _cron_execute_update_age(self):
        partner_recs = self.search([('company_type', '=', 'person'),
                                    ('type', '=', 'contact'),
                                    ('dob', '!=', False)])
        partner_recs.calculate_age()

    def update_all_test_center(self):
        """
            This method will filter out the partners which company type will be company.
            And add all the covid test center in the test center column.
        """
        for partner in self.filtered(lambda p: p.company_type != 'person'):
            appointment_centre_ids = self.env['calendar.appointment.type'].search(
                [('is_published', '=', True)]).ids
            partner.appointment_centre_ids = [(6, 0, appointment_centre_ids)] 

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
    appointment_centre_ids = fields.Many2many('calendar.appointment.type', string='Select Test Centre')

    def appointmet_verify_check(self, Partner, date_start):
        """ verify appointment validity """
        data_dict = {}
        message = ''
        date_start = date_start - timedelta(days=14)
        if Partner:
            partner_report = self.env['event.report'].sudo().search([('partner_id', '=', Partner.id),
                                                                     ('create_date', '>=', date_start),
                                                                     ('state', '=', 'positive')])
            if partner_report:
                message += "You are Restricted to test for 14 days since your result was Positive."
                data_dict['message'] = message
                return data_dict

            domain = [('state', '=', 'open'),
                      ('appointment_type_id', '!=', False),
                      ('partner_ids', 'in', Partner.ids)]
            partner_event = self.env['calendar.event'].sudo().search(domain)
            if self.env.user.partner_id.id == Partner.id:
                partner_event = partner_event.filtered(lambda event: len(event.partner_ids) == 1)
            if partner_event:
                message += "The Appointment is already scheduled for you. \n " \
                                    "You can Cancel the prior appointment and reschedul it again."
                data_dict['message'] = message
                return data_dict

        return data_dict
