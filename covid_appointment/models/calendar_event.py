from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def action_send_mail_with_qr(self):
        email_values = {
            'model': None,  # We don't want to have the mail in the tchatter while in queue!
            'res_id': None,
        }
        mail_template = self.env.ref('covid_appointment.email_template_testing_qr_code_image')
        event_rec = self.search([], order='id desc', limit=1)
        rendering_context = {
            'qr_code_string': event_rec.qr_code_string,
        }
        mail_template = mail_template.with_context(rendering_context)
        mail_template.send_mail(event_rec.attendee_ids[0].id, email_values=email_values,
                                notif_layout='mail.mail_notification_light')


    def _cron_execute_archive_event(self):
        """
            This method is called from scheduler to make invalid the QR code.
        """
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) - timedelta(days=3)

        event_recs = self.search([('start_datetime', '>=', start),
                                  ('start_datetime', '<=', end),
                                  ('state', '=', 'done'),
                                  ('appointment_type_id', '!=', False)])
        event_recs.sudo().write({'is_qr_valid': False})

    @api.depends('access_token')
    def fetch_qr_code_string(self):
        for event_rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
            event_access_token = event_rec.access_token or ''
            event_rec.qr_code_string = base_url + "/covid_report/" + event_access_token


    state = fields.Selection(selection_add=[('done', 'Done'),
                                            ('cancel', 'Cancelled'),
                                            ('not achieved', 'Not Achieved')])
    event_report_ids = fields.One2many(
        'event.report', 'calendar_event_id', string="Reports")
    event_name = fields.Char()
    qr_code_string = fields.Char(compute="fetch_qr_code_string", store=True, copy=False)
    not_achived_reason = fields.Text(readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Test Center Staff",
                                  help="This employee is a test center's staff member who\
                                  is going to test the patient.")
    is_qr_valid = fields.Boolean(string="Is QR Valid", default=True)
    cancelled_by = fields.Selection([('company', 'Company'), ('customer', 'Customer')],
                                    default="customer", string="Cancelled By")
    is_label_printed = fields.Boolean(default=False, copy=False)
    patient_partner_id = fields.Many2one('res.partner', string="Patient")
    covid_status = fields.Selection([('positive', 'Positive'),
                                     ('negative', 'Negative'),
                                     ('failed', 'Test Failed')],
                                    string="Covid State", readonly=1)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s-%s' % (self.partner_ids[0].parent_id.ref, self.partner_ids[0].name)

    def button_event_reports(self):
        """
        Display report records of covid Appointments. 
        """
        return {
            'name': _('Reports'),
            'view_mode': 'tree,form',
            'res_model': 'event.report',
            'type': 'ir.actions.act_window',
            'domain': [('calendar_event_id', '=', self.id)],
            'context': {'default_calendar_event_id': self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['event_name'] = self.env['ir.sequence'].next_by_code(
                'calendar.event') or _('New')
        return super(CalendarEvent, self).create(vals_list)

    def mark_done(self, covid_status=False):
        if self.employee_id:
            vals = {
                'state': 'done',
            }
            if covid_status:
                vals.update({
                    'covid_status': covid_status
                })
            self.write(vals)
        else:
            raise ValidationError(_("Test Centre staff is missing. Please entre the Test Centre Staff details."))

    def mark_not_achieved(self):
        return {
            'name': "Not Archived Reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'archived.reason.wizard',
            'target': 'new',
            'context': {'default_event_id': self.id}
        }

    def mark_cancel(self):
        return {
            'name': "Event Cancel Reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cancel.reason.wizard',
            'target': 'new',
            'context': {'default_event_id': self.id}
        }
