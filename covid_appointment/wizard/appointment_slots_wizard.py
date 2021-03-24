from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import math
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AppointmentSlotWizard(models.TransientModel):
    _name = "appointment.slot.wizard"
    _description = "Appointment Type Slots Wizard"

    start_time = fields.Datetime("Start Date")
    slot_duration = fields.Float('Duration of Slot')
    flag_monday = fields.Boolean('Monday')
    flag_tuesday = fields.Boolean('Tuesday')
    flag_wednes = fields.Boolean('Wednesday')
    flag_thrus = fields.Boolean('Thrusday')
    flag_friday = fields.Boolean('Friday')
    flag_saturday = fields.Boolean('Saturday')
    flag_sunday = fields.Boolean('Sunday')

    def float_time_convert(self,float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return (factor * int(math.floor(val)), int(round((val % 1) * 60)))

    def submit_configuration(self):

        weekdays_array = []
        expected_hours=8
        current_appointment = self._context.get('default_appointment_id')
        current_appointment = self.env['calendar.appointment.type'].sudo().browse(int(current_appointment))

        if current_appointment.employee_ids:
            expected_hours = current_appointment.employee_ids[0].resource_calendar_id.hours_per_day
        slot_time = self.slot_duration
        if current_appointment.appointment_duration:
            slot_time = current_appointment.appointment_duration
        if not slot_time:
            raise UserError(_('Please provide slot duration'))

        hours,minutes = self.float_time_convert(slot_time)

        if self.flag_monday:
            weekdays_array.append(1)
        if self.flag_tuesday:
            weekdays_array.append(2)
        if self.flag_wednes:
            weekdays_array.append(3)
        if self.flag_thrus:
            weekdays_array.append(4)
        if self.flag_friday:
            weekdays_array.append(5)
        if self.flag_saturday:
            weekdays_array.append(6)
        if self.flag_sunday:
            weekdays_array.append(7)
        start_date = self.start_time

        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)

        start_date = datetime.strftime(pytz.utc.localize(
            datetime.strptime(str(start_date), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
            local), DEFAULT_SERVER_DATETIME_FORMAT)
        start_date = datetime.strptime(start_date,
                                       DEFAULT_SERVER_DATETIME_FORMAT)

        unlink_obj = self.env['calendar.appointment.slot'].sudo().search([
            ('appointment_type_id', '=', current_appointment.id),
        ]).unlink()
        for i in range(0, 15):
            week_day = start_date.weekday()
            week_day = self.get_week_short_day(week_day)

            if week_day in weekdays_array:
                weekdays_array.remove(week_day)
                total_work_hours = 0.0
                current_start_date = start_date
                while total_work_hours <= expected_hours:
                    if total_work_hours != 0:
                        time = current_start_date.hour + total_work_hours
                        total_work_hours += slot_time
                    else:
                        minute = round(current_start_date.minute / 60, 2)
                        time = current_start_date.hour + minute
                        total_work_hours += slot_time
                    create_dict = {'hour': round(time, 2), 'weekday': str(week_day), 'appointment_type_id': current_appointment.id}
                    self.env['calendar.appointment.slot'].sudo().create(create_dict)

            start_date += timedelta(days=1)

    def get_week_short_day(self, day):
        week_day = ''
        if day == 0:
            week_day = 1
        if day == 1:
            week_day = 2
        if day == 2:
            week_day = 3
        if day == 3:
            week_day = 4
        if day == 4:
            week_day = 5
        if day == 5:
            week_day = 6
        if day == 6:
            week_day = 7
        return week_day
