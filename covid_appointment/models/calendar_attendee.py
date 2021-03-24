from odoo import models
from pytz import timezone


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
            rendering_context.update({
                'dbname': self._cr.dbname,
                'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069'),
                'force_event_id': force_event_id,
                'start_datetime': self.event_id.start_datetime.astimezone(timezone(self.event_id.user_id.tz)).strftime('%d-%m-%Y %H:%M')
            })

        invitation_template = invitation_template.with_context(rendering_context)
        email_values = {
            'model': None,  # We don't want to have the mail in the tchatter while in queue!
            'res_id': None,
        }
        mail_ids = []
        for attendee in self:
            mail_ids.append(invitation_template.send_mail(attendee.id, email_values=email_values,
                                                          notif_layout='mail.mail_notification_light'))

        # if mail_ids:
        #     res = self.env['mail.mail'].browse(mail_ids).send()
        return res
