from odoo import fields, models


class InheritAppointmentType(models.Model):
    _inherit = "calendar.appointment.type"

    user_id = fields.Many2one('res.users', string="User",
        domain=lambda self: [('groups_id', 'in', self.env.ref('base.group_user').id)])
    employee_ids = fields.Many2many('hr.employee', 'website_calendar_type_employee_rel',
                                    string='Employees', domain=[])

    def generate_time_slots(self):

        return {
            'name': "Appointment Type Slot Configuration",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'appointment.slot.wizard',
            'target': 'new',
            'context': {'default_appointment_id': self.id}
        }
