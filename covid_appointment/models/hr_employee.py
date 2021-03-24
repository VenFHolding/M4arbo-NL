from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    appointment_type_id = fields.Many2one('calendar.appointment.type',
                                          string="Test Center")
    