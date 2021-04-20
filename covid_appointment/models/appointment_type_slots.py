from odoo import fields, models


class InheritAppointmentType(models.Model):
    _inherit = "calendar.appointment.type"

    user_id = fields.Many2one('res.users', string="User",
        domain=lambda self: [('groups_id', 'in', self.env.ref('base.group_user').id)])
    medical_staff_employee_ids = fields.One2many('hr.employee', 'appointment_type_id',
                                                 string="Medical Staff",
                                                 domain=[('is_medical_staff', '=', True)])
    completed_appointment_count = fields.Integer('# Appointments', compute='_compute_completed_appointment_count')

    def _compute_completed_appointment_count(self):
        meeting_data = self.env['calendar.event'].read_group([('appointment_type_id', 'in', self.ids), ('state', '=', 'done')], ['appointment_type_id'], ['appointment_type_id'])
        mapped_data = {m['appointment_type_id'][0]: m['appointment_type_id_count'] for m in meeting_data}
        for appointment_type in self:
            appointment_type.completed_appointment_count = mapped_data.get(appointment_type.id, 0)

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

    def action_calendar_completed_meetings(self):
        self.ensure_one()
        action = self.env.ref('covid_appointment.calendar_event_action').read()[0]
        action['context'] = {
            'default_appointment_type_id': self.id,
            'search_default_appointment_type_id': self.id
        }
        action['domain'] = [('state', '=', 'done')]
        return action
