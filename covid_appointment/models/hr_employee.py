from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_medical_staff = fields.Boolean(string="Medical Staff")
    appointment_type_id = fields.Many2one('calendar.appointment.type',
                                          string="Test Center")

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """
            On Test Centre Login, displayed only test centre's partner.
        """
        user = self.env.user
        if user.user_has_groups('covid_appointment.group_appointment_own_document') and not user.user_has_groups('website_calendar.group_calendar_manager'):
            appointment_type_recs = self.env['calendar.appointment.type'].search([('user_id', '=', user.id)])
            domain += ['|', ('user_id', '=', user.id), ('appointment_type_id', 'in', appointment_type_recs.ids)]
        return super(HrEmployee, self).search_read(domain, fields, offset, limit, order)
    