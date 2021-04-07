# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from babel.dates import format_datetime
from pytz import timezone

from odoo.addons.website_calendar.controllers.main import WebsiteCalendar  # Import the class
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf, email_split
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
from odoo.tools.misc import get_lang

def extract_email(email):
    """ extract the email address from a user-friendly email address """
    addresses = email_split(email)
    return addresses[0] if addresses else ''

class DownloadReport(CustomerPortal):

    """ Print Label Controller. """

    @http.route('/download/covid_test/label/<model("calendar.event"):event>', type='http', auth='user', website=True)
    def download_covid_test_label(self, event,**kw):
        event.is_label_printed = True
        return self._show_report(model=event, report_type='pdf', report_ref='covid_appointment.calendar_event_label_report', download=False)


class CovidAppointments(http.Controller):

    @http.route('/covid/appointment/history', type='http', auth='public', website=True)
    def search_covid_appointment_history(self, **kw):
        return http.request.render('covid_appointment.search_covid_appointment_layout')

    @http.route('/website/covid/policy', type='http', auth='public', website=True)
    def search_covid_privacy_policy(self, **kw):
        policy_id = request.env['custom.website.policy'].sudo().search([])
        data={}
        if policy_id:
            policy_id=policy_id[-1]

            data = {
                'policy_data': policy_id,
            }
        return http.request.render('covid_appointment.search_covid_privacy_layout', data)

    @http.route(['/covid/appointment/view_history'], type='http', auth="public", methods=['POST', 'GET'], website=True)
    def view_covid_appointment_history(self, **post):
        if not post.get('company_ref') or not post.get('email'):
            return request.redirect('/covid/appointment/history')
        partner = request.env['res.partner'].sudo()
        events = request.env['calendar.event'].sudo()
        partner_company_rec = partner.search([('ref', '=', post.get('company_ref'))], limit=1)
        calendar_event_data = []
        error_msg = ""
        if partner_company_rec:
            customer = partner.search([('email', '=', post.get('email'))], limit=1)
            if not customer:
                error_msg = 'Entered email is not found in the system.'
            calendar_event_recs = events.with_context(active_test=False).search([('partner_ids', 'in', customer.ids),
                                                 ('appointment_type_id', '!=', False)])
            if not calendar_event_recs:
                error_msg = "No records found for this customer"
            for event_rec in calendar_event_recs:
                event_datetime = event_rec.start_datetime.astimezone(timezone(event_rec.user_id.tz))
                event_data = {
                    'date': event_datetime.strftime('%d-%m-%Y %H:%M'),
                    'test_center': event_rec.appointment_type_id.name,
                    'partner_name': event_rec.patient_partner_id.name,
                    'company_ref': event_rec.patient_partner_id.parent_id.name,
                    'appointment_status': dict(event_rec._fields['state'].selection).get(event_rec.state),
                    'covid_status': False,
                }
                if event_rec.state == 'done' and event_rec.event_report_ids:
                    event_data.update({
                        'covid_status': event_rec.event_report_ids[0].state.capitalize()
                    })
                calendar_event_data.append(event_data)
        else:
            error_msg = 'Entered Company Reference is not found in the system.'
        if error_msg:
            data = {
                'error_msg': error_msg,
            }
            return http.request.render('covid_appointment.search_covid_appointment_layout', data)
        data = {
            'calendar_event_data': calendar_event_data,
        }
        return http.request.render('covid_appointment.covid_appointment_history_data_template', data)

    @http.route('/covid_report/<string:event_access_token>',
                type='http', auth="public", website=True)
    def view_calendar_event_data(self, event_access_token, is_completed=False, **kw):
        """check fetched calendar event reports.
        If it is not exists then upload document screen will be discplayed.
        otherwise it will display the report output."""
        event_rec = http.request.env['calendar.event'].sudo().with_context(active_test=False).search(
            [('access_token', '=', event_access_token)], limit=1)
        if not event_rec:
            return request.not_found()
        user = request.env.user
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069')
        message = ''
        data = {
            'base_url': base_url,
            'event_rec': event_rec,
            'is_internal_user': True,
        }
        if is_completed:
            data.update({
                'is_completed': True
            })
        if not user.has_group('base.group_user'):
            data.update({
                'is_internal_user': False,
            })
        if event_rec:
            # If event is in confirmed state then event can be cancelled or test center can fill the data
            # for the covid status.
            if event_rec.state not in ['done', 'cancel', 'not achieved']:
                return http.request.render('covid_appointment.upload_covid_document', data)

            # If event is not in confirmed state then it will show the message based on conditions.
            if event_rec.state == 'cancel':
                if event_rec.cancelled_by == 'company':
                    cancelled_by = 'Test Center'
                else:
                    cancelled_by = 'Customer'
                message = "This appointment has been cancelled by the " + cancelled_by + "."
                data.update({
                    'reason': event_rec.not_achived_reason,
                })
            if event_rec.state == 'not achieved':
                message = "This Test is not achived."
                data.update({
                    'reason': event_rec.not_achived_reason,
                })
            if event_rec.state == 'done':
                if not event_rec.is_qr_valid:
                    message = "This Test not valid anymore."
                else:
                    if event_rec.event_report_ids:
                        covid_state = event_rec.event_report_ids[0].state
                        if covid_state == 'positive':
                            message = "This employee is marked as covid positive on %s." % str(
                                event_rec.event_report_ids[0].create_date.date())
                            data.update({
                                'covid_status': 'positive'
                            })
                        if covid_state == 'negative':
                            message = "This employee is marked as covid negative."
                            data.update({
                                'covid_status': 'negative'
                            })
                        if covid_state == 'failed':
                            message = "This employee's test is failed."
                    else:
                        message = "Test Result is not updated in the system."
            data.update({
                'message': message,
            })
            return http.request.render('covid_appointment.display_covid_report_template', data)

    @http.route('/calender/event/cancel/<model("calendar.event"):event>',
                type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cancel_covid_appointment(self, event, **post):
        """
            This controller will be called when an employee wants to cancel the appoitment.
        """

        res_user = request.env.user
        cancelled_by = 'customer'
        user_name = ''

        if fields.Datetime.from_string(event.allday and event.start or event.start_datetime) < datetime.now() + relativedelta(hours=event.appointment_type_id.min_cancellation_hours):
            return request.redirect('/website/calendar/view/' + event.access_token + '?message=no-cancel')

        if res_user.has_group('base.group_portal'):
            cancelled_by = 'customer'
            user_name = str(event.sudo().patient_partner_id.name)

        if res_user.has_group('base.group_user'):
            cancelled_by = 'company'
            user_name = str(res_user.partner_id.name)

        event.sudo().write({
            'state': 'cancel',
            'cancelled_by': cancelled_by,
            'not_achived_reason': post.get('cancel_reason'),
            'active': False,
        })            

        msg = "<b>"
        msg = msg + 'The event is Cancelled by ' + str(user_name) + '. \n '
        msg = msg + "</b><ul>"
        msg = msg + "Reason : " + post.get('cancel_reason') + '. \n </ul>'
        event.sudo().message_post(body=msg)
        if event.sudo().attendee_ids:
            event.sudo().attendee_ids._send_mail_to_attendees(
                'covid_appointment.email_template_covid_cancel_appointment')

        return request.redirect('/website/calendar?message=cancel')

    @http.route('/calender/event/post_covid_data/<model("calendar.event"):event>',
                type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def process_covid_appointment(self, event, **post):
        """
            This controller will be called when any internal user scan the QR code 
            and fill the data for the selected event.
        """
        event_achived = False
        covid_status = 'negative'
        test_failed_reason = ''
        patient_partner_id = event.patient_partner_id
        attendee = event.attendee_ids.filtered(
            lambda atd: atd.partner_id.id == patient_partner_id.id)
        if post.get('is_achived') == 'yes':
            event_achived = True
            if post.get('is_positive') == 'yes':
                covid_status = 'positive'
            if post.get('is_positive') == 'failed':
                covid_status = 'failed'
                test_failed_reason = post.get('test_failed_reason')

            event_report = request.env['event.report']

            event_report_rec = event_report.sudo().create({
                'state': covid_status,
                'calendar_event_id': event.id,
                'partner_id': patient_partner_id.id or False,
                'test_failed_reason': test_failed_reason,
            })
            event.sudo().mark_done()

            # Send mail to attendees if covid report is positive or negative.
            if event.sudo().attendee_ids:
                invitation_template = request.env.ref('covid_appointment.email_template_covid_result_of_appointment')
                context = {
                    'covid_result': event_report_rec.state
                }
                invitation_template.with_context(context).send_mail(attendee.id, notif_layout='mail.mail_notification_light')

        else:
            event.sudo().write({
                'state': 'not achieved',
                'not_achived_reason': post.get('not_achived_reason'),
            })
            event.sudo().attendee_ids._send_mail_to_attendees(
                'covid_appointment.email_template_covid_achieved_appointment')

        url = "/covid_report/" + event.access_token + "?is_completed=True"
        return request.redirect(url)

    @http.route(['/get_company_appointments'], auth='public', type='json', website=True)
    def get_company_appointments(self, data, **kw):
        company_ref_ids = request.env['res.partner'].sudo().search([('ref', '=', data.get('company_ref'))], limit=1)
        appointment_list = []
        user_rec = request.env.user

        appointment_centre_ids = company_ref_ids.appointment_centre_ids.filtered(
            lambda app: app.is_published)
        
        is_test_center_user = False
        if user_rec.has_group('base.group_user') and not user_rec.has_group('website_calendar.group_calendar_manager'):
            is_test_center_user = True

        if is_test_center_user:
            appointment_centre_ids = company_ref_ids.appointment_centre_ids.filtered(
                lambda app: app.user_id.id == user_rec.id)

        for rec in appointment_centre_ids:
            appointment_dict = {
                'id': rec.id,
                'name': rec.name,
            }
            appointment_list.append(appointment_dict)
        if appointment_list:
            return appointment_list
        return False


class CustomWebsiteCalendar(WebsiteCalendar):  # Inherit in WebsiteCalendar class


    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/submit'], type='http', auth="public", website=True, method=["POST"])
    def calendar_appointment_submit(self, appointment_type, datetime_str, employee_id, name, phone, email, country_id=False, **kwargs):
        """
            Override this controller for stop to add partner or employee which is related
            to the appointment type user.
            Also checked the previous appointment before create a new one for same person.
        """
        timezone = request.session['timezone']
        tz_session = pytz.timezone(timezone)
        date_start = tz_session.localize(fields.Datetime.from_string(datetime_str)).astimezone(pytz.utc)
        date_end = date_start + relativedelta(hours=appointment_type.appointment_duration)

        # check availability of the employee again (in case someone else booked while the client was entering the form)
        Employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if Employee.user_id and Employee.user_id.partner_id:
            if not Employee.user_id.partner_id.calendar_verify_availability(date_start, date_end):
                return request.redirect('/website/calendar/%s/appointment?failed=employee' % appointment_type.id)

        company_id = request.env['res.company'].search([], limit=1).id
        country_id = int(country_id) if country_id else None
        country_name = country_id and request.env['res.country'].browse(country_id).name or ''
        Partner = request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)
        partner_company_ref = request.env['res.partner'].sudo().search(
            [('ref', '=', kwargs.get('company_ref')),
             ('company_type', '=', 'company')], limit=1)
        if Partner:
            data_dict = Partner.appointmet_verify_check(Partner, date_start)
            if data_dict.get('message'):
                request.session['event_error_message'] = data_dict.get('message')
                url = appointment_type.website_url
                url = url.split('/')[:-1]
                url = '/'.join(url)
                url += "/info"
                if employee_id:
                    url += '?employee_id=' + employee_id
                if datetime_str and not employee_id:
                    url += '?date_time=' + datetime_str
                if datetime_str and employee_id:
                    url += '&date_time=' + datetime_str
                return request.redirect(url)
            if not Partner.calendar_verify_availability(date_start, date_end):
                return request.redirect('/website/calendar/%s/appointment?failed=partner' % appointment_type.id)
            if not Partner.mobile or len(Partner.mobile) <= 5 and len(phone) > 5:
                Partner.write({'mobile': phone})
            if not Partner.country_id:
                Partner.country_id = country_id
        else:
            Partner = Partner.create({
                'name': name,
                'country_id': country_id,
                'mobile': phone,
                'email': email,
                'gender': kwargs.get('gender'),
                'dob': kwargs.get('dob_datepicker'),
                'parent_id': partner_company_ref.id,
            })
            group_portal = request.env.ref('base.group_portal')
            user_rec = request.env['res.users'].sudo().with_context(no_reset_password=True)._create_user_from_template({
                'email': extract_email(email),
                'login': extract_email(email),
                'company_id': company_id,
                'company_ids': [(6, 0, [company_id])],
                'partner_id': Partner.id,
            })
            user_rec.sudo().write({'active': True, 'groups_id': [(4, group_portal.id)]})
            user_rec.partner_id.signup_prepare()
            user_rec.action_reset_password()

        description = (_('Country: %s') + '\n' +
                       _('Mobile: %s') + '\n' +
                       _('Email: %s') + '\n') % (country_name, phone, email)
        for question in appointment_type.question_ids:
            key = 'question_' + str(question.id)
            if question.question_type == 'checkbox':
                answers = question.answer_ids.filtered(lambda x: (key + '_answer_' + str(x.id)) in kwargs)
                description += question.name + ': ' + ', '.join(answers.mapped('name')) + '\n'
            elif kwargs.get(key):
                if question.question_type == 'text':
                    description += '\n* ' + question.name + ' *\n' + kwargs.get(key, False) + '\n\n'
                else:
                    description += question.name + ': ' + kwargs.get(key) + '\n'

        categ_id = request.env.ref('website_calendar.calendar_event_type_data_online_appointment')
        alarm_ids = appointment_type.reminder_ids and [(6, 0, appointment_type.reminder_ids.ids)] or []
        partner_ids = list(set([Employee.user_id.partner_id.id] + [Partner.id]))
        event = request.env['calendar.event'].sudo().create({
            'state': 'open',
            'name': _('%s with %s') % (appointment_type.name, name),
            'start': date_start.strftime(dtf),
            # FIXME master
            # we override here start_date(time) value because they are not properly
            # recomputed due to ugly overrides in event.calendar (reccurrencies suck!)
            #     (fixing them in stable is a pita as it requires a good rewrite of the
            #      calendar engine)
            'start_date': date_start.strftime(dtf),
            'start_datetime': date_start.strftime(dtf),
            'stop': date_end.strftime(dtf),
            'stop_datetime': date_end.strftime(dtf),
            'allday': False,
            'duration': appointment_type.appointment_duration,
            'description': description,
            'alarm_ids': alarm_ids,
            'location': appointment_type.location,
            'partner_ids': [(4, pid, False) for pid in partner_ids],
            'categ_ids': [(4, categ_id.id, False)],
            'appointment_type_id': appointment_type.id,
            'user_id': Employee.user_id.id,
            'patient_partner_id': Partner.id,
        })
        event.attendee_ids.write({'state': 'accepted'})
        return request.redirect('/website/calendar/view/' + event.access_token + '?message=new')

    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/info'], type='http',
                auth="public", website=True)
    def calendar_appointment_form(self, appointment_type, employee_id, date_time, **kwargs):
        """
            Override this controller to display error message on submit the calendar event form.
        """
        partner_data = {}
        if request.env.user.partner_id != request.env.ref('base.public_partner'):
            partner_data = request.env.user.partner_id.read(fields=['name', 'mobile', 'country_id', 'email'])[0]
        day_name = format_datetime(datetime.strptime(date_time, dtf), 'EEE', locale=get_lang(request.env).code)
        date_formated = format_datetime(datetime.strptime(date_time, dtf), locale=get_lang(request.env).code)
        countries_recs = request.env['res.country'].search([])
        template_data = {
            'partner_data': partner_data,
            'appointment_type': appointment_type,
            'datetime': date_time,
            'datetime_locale': day_name + ' ' + date_formated,
            'datetime_str': date_time,
            'employee_id': employee_id,
            'countries': countries_recs,
        }
        if request.session.get('event_error_message'):
            template_data.update({
                'error_msg': request.session.get('event_error_message')
            })
            request.session.pop('event_error_message')
        if request.session.get('partner_id'):
            company_ref_id = request.env['res.partner'].sudo().search([('ref', '=', request.session.get('partner_id'))], limit=1)
            if company_ref_id.restrict_country_ids:
                countries_recs = company_ref_id.restrict_country_ids
            template_data.update({
                'ref_partner_ref': company_ref_id.ref,
                'countries': countries_recs,
            })
        return request.render("website_calendar.appointment_form", template_data)

    @http.route([
        '/website/calendar',
        '/website/calendar/<model("calendar.appointment.type"):appointment_type>',
    ], type='http', auth="public", website=True)
    def calendar_appointment_choice(self, appointment_type=None, employee_id=None, message=None, **kwargs):
        """
            Override this controller to display company details on calendar event form.
        """
        company_ref_ids = request.env['res.partner'].sudo().search([('appointment_centre_ids', '!=', False)])
        if not appointment_type:
            country_code = request.session.geoip and request.session.geoip.get('country_code')
            if country_code:
                suggested_appointment_types = request.env['calendar.appointment.type'].search([
                    '|', ('country_ids', '=', False),
                    ('country_ids.code', 'in', [country_code])])
            else:
                suggested_appointment_types = request.env['calendar.appointment.type'].search([])
            if not suggested_appointment_types:
                return request.render("website_calendar.setup", {})
            appointment_type = suggested_appointment_types[0]
        else:
            suggested_appointment_types = appointment_type
        suggested_employees = []
        if employee_id and int(employee_id) in appointment_type.employee_ids.ids:
            suggested_employees = request.env['hr.employee'].sudo().browse(int(employee_id)).name_get()
        elif appointment_type.assignation_method == 'chosen':
            suggested_employees = appointment_type.sudo().employee_ids.name_get()
        return request.render("website_calendar.index", {
            'appointment_type': appointment_type,
            'suggested_appointment_types': suggested_appointment_types,
            'suggested_company': company_ref_ids,
            'message': message,
            'selected_employee_id': employee_id and int(employee_id),
            'suggested_employees': suggested_employees,
        })

    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/appointment'], type='http', auth="public", website=True)
    def calendar_appointment(self, appointment_type=None, employee_id=None, timezone=None, failed=False, **kwargs):
        request.session['partner_id'] = kwargs.get('company_ref')
        request.session['timezone'] = timezone or appointment_type.appointment_tz
        Employee = request.env['hr.employee'].sudo().browse(int(employee_id)) if employee_id else None
        Slots = appointment_type.sudo()._get_appointment_slots(request.session['timezone'], Employee)
        return request.render("website_calendar.appointment", {
            'appointment_type': appointment_type,
            'timezone': request.session['timezone'],
            'failed': failed,
            'slots': Slots,
        })