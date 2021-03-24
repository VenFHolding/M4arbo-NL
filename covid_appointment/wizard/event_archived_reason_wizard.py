from odoo import fields, models


class ArchivedReasonWizard(models.TransientModel):
    _name = "archived.reason.wizard"
    _description = "Calendar Event Archived Reason Wizard"

    reason = fields.Text(required=True)
    event_id = fields.Many2one('calendar.event', string="Event")

    def submit_reason(self):
        self.event_id.sudo().write({
    		'state': 'not achieved',
    		'not_achived_reason': self.reason,
    	})
        event_obj = self.event_id
        res_user = self.env['res.users'].sudo().search([('id', '=', self._context.get('uid'))])
        msg = "<b>"
        msg = msg + 'The event is Not Achieved by ' + str(res_user.partner_id.name) + '. \n '
        msg = msg + "</b><ul>"
        msg = msg + "Reason : " + str(self.reason) + '. \n </ul>'
        event_obj.message_post(body=msg)
        if self.event_id.attendee_ids:
            self.event_id.attendee_ids._send_mail_to_attendees('covid_appointment.email_template_covid_achieved_appointment')

