from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_medical_staff = fields.Boolean(string="Medical Staff")
    appointment_type_id = fields.Many2one('calendar.appointment.type',
                                          string="Test Center")
    