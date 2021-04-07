import calendar
from odoo import models, fields
from pytz import timezone
from werkzeug.urls import url_encode
from odoo.tools import html2plaintext


class Attendee(models.Model):
    """ Calendar Attendee Information """

    _inherit = 'calendar.attendee'

    def _send_mail_to_attendees(self, template_xmlid, force_send=False, force_event_id=None):
        if not self.mapped('event_id').appointment_type_id:
            return super(Attendee, self)._send_mail_to_attendees(
                template_xmlid, force_send, force_event_id)

        res = False
        rendering_context = dict(self._context)

        if template_xmlid in ['covid_appointment.email_template_covid_cancel_appointment','covid_appointment.email_template_covid_achieved_appointment']:
            if template_xmlid == 'covid_appointment.email_template_covid_cancel_appointment':
                invitation_template = self.env.ref('covid_appointment.email_template_covid_cancel_appointment')
            if template_xmlid == 'covid_appointment.email_template_covid_achieved_appointment':
                invitation_template = self.env.ref('covid_appointment.email_template_covid_achieved_appointment')
        else:
            invitation_template = self.env.ref('covid_appointment.email_template_covid_test_appointment')

            details = self.event_id.appointment_type_id and self.event_id.appointment_type_id.message_confirmation or event.description or ''
            if not self.event_id.allday:
                url_date_start = fields.Datetime.from_string(self.event_id.start_datetime).strftime('%Y%m%dT%H%M%SZ')
                url_date_stop = fields.Datetime.from_string(self.event_id.stop_datetime).strftime('%Y%m%dT%H%M%SZ')
            else:
                url_date_start = url_date_stop = fields.Date.from_string(event.start_date).strftime('%Y%m%d')
            params = {
                'action': 'TEMPLATE',
                'text': self.event_id.name,
                'dates': url_date_start + '/' + url_date_stop,
                'details': html2plaintext(details.encode('utf-8'))
            }
            if self.event_id.location:
                params.update(location=self.event_id.location.replace('\n', ' '))
            encoded_params = url_encode(params)
            google_url = 'https://www.google.com/calendar/render?' + encoded_params
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            outlook_url = base_url + '/website/calendar/ics/' + self.event_id.access_token + '.ics'
            cancel_url = base_url + '/website/calendar/cancel/' + self.event_id.access_token

            rendering_context.update({
                'dbname': self._cr.dbname,
                'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069'),
                'force_event_id': force_event_id,
                'start_datetime': self.event_id.start_datetime.astimezone(timezone(self.event_id.user_id.tz)).strftime('%d-%m-%Y %H:%M'),
                'google_url': google_url,
                'outlook_url': outlook_url,
                'cancel_url': cancel_url,
            })

        invitation_template = invitation_template.with_context(rendering_context)
        email_values = {
            'model': None,  # We don't want to have the mail in the tchatter while in queue!
            'res_id': None,
        }
        mail_ids = []
        for attendee in self.filtered(lambda att: att.partner_id.parent_id and att.partner_id.gender):
            mail_ids.append(invitation_template.send_mail(attendee.id, email_values=email_values,
                                                          notif_layout='mail.mail_notification_light'))

        return res
