# -*- coding: utf-8 -*-

import json
from odoo import http, _
from odoo.http import content_disposition, request
from pytz import timezone
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self):
        """
            Override this method to display count of total child contacts
            of login user.
        """
        values = super(CustomerPortal, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id
        total_login_partner_child = len(partner.child_ids.filtered(
            lambda contact: contact.type == 'contact'))
        total_covid_appointments = request.env['calendar.event'].search_count(
            [('patient_partner_id', 'in', partner.ids)])
        values.update({
            'total_login_partner_child': total_login_partner_child,
            'total_covid_appointments': total_covid_appointments
        })
        return values

    @http.route(['/covid_report/download/excel/<model("res.partner"):partner>'], type='http', auth="user", website=True)
    def download_xlsx_covid_report(self, partner, **kw):
        xlsx_data = partner.get_xlsx_report()
        report_name = "covid_report"
        try:
            response = request.make_response(
                        xlsx_data,
                        headers=[('Content-Type', 'application/vnd.ms-excel'), ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                        ]
                    )
            return response

        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))


    @http.route(['/my/covid_appointments', '/my/covid_appointments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_covid_appointments(self, page=1, **kw):
        calendar_event_data = []
        calendar_event = request.env['calendar.event'].sudo()
        partner = request.env.user.partner_id
        calendar_event_recs = calendar_event.search([('partner_ids', 'in', partner.ids)])
        for event_rec in calendar_event_recs:
            user_timezone = self.event_id.user_id.tz
            if not user_timezone:
                user_timezone = "Europe/Amsterdam"
            event_datetime = event_rec.start_datetime.astimezone(timezone(user_timezone))
            event_data = {
                'appointment_id': event_rec.event_name,
                'date': event_datetime.strftime('%d-%m-%Y %H:%M'),
                'test_center': event_rec.appointment_type_id.name,
                'partner_name': event_rec.partner_ids[0].name,
                'company_ref': event_rec.partner_ids[0].parent_id.name,
                'appointment_status': dict(event_rec._fields['state'].selection).get(event_rec.state),
                'covid_status': False,
                'link': event_rec.qr_code_string,
            }
            if event_rec.state == 'done' and event_rec.event_report_ids:
                event_data.update({
                    'covid_status': event_rec.event_report_ids[0].state.capitalize()
                })
            calendar_event_data.append(event_data)
        values = {
            'contact': partner,
            'calendar_event_data': calendar_event_data,
        }
        return http.request.render('covid_appointment.view_contact_covide_appointment', values)

    @http.route(['/my/child/employees', '/my/child/employees/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_child_employees(self, page=1, name=None, sortby=None, **kw):
        partner = request.env.user.partner_id
        domain = [('parent_id', '=', partner.id), ('type', '=', 'contact')]
        filter_data = {}
        if name:
            domain += [('name', 'ilike', name)]

        # Remove all Filters
        if kw.get('rm_filters'):
            kw = {}
            if request.session.get('contact_age_filter'):
                request.session.pop('contact_age_filter')
            if request.session.get('positive_check'):
                request.session.pop('positive_check')
            if request.session.get('negative_check'):
                request.session.pop('negative_check')
            if request.session.get('gender_filter'):
                request.session.pop('gender_filter')
            if request.session.get('app_date_from'):
                request.session.pop('app_date_from')
            if request.session.get('app_date_to'):
                request.session.pop('app_date_to')
            if request.session.get('min_age'):
                request.session.pop('min_age')
            if request.session.get('max_age'):
                request.session.pop('max_age')


        # Applied Gender Filter
        if kw.get('gender_filter') or request.session.get('gender_filter'):
            if kw.get('gender_filter'):
                request.session['gender_filter'] = kw.get('gender_filter')
                gender = kw.get('gender_filter')
            if not kw.get('gender_filter') and request.session.get('gender_filter'):
                gender = request.session.get('gender_filter')
            filter_data.update({
                'gender_filter': gender
            })
            domain += [('gender', '=', gender)]

        # Applied Age Filter
        if kw.get('min_age') or kw.get('max_age'):
            if request.session.get('contact_age_filter'):
                request.session.pop('contact_age_filter')
            if kw.get('contact_age_filter'):
                kw.pop('contact_age_filter')

        if kw.get('min_age') or request.session.get('min_age'):
            if kw.get('min_age'):
                min_age = int(kw.get('min_age'))
                request.session['min_age'] = min_age
            else:
                min_age = request.session.get('min_age')

            filter_data.update({
                'min_age': min_age
            })
            domain += [('age', '>=', min_age)]

        if kw.get('max_age') or request.session.get('max_age'):
            if kw.get('max_age'):
                max_age = int(kw.get('max_age'))
                request.session['max_age'] = max_age
            else:
                max_age = request.session.get('max_age')
            filter_data.update({
                'max_age': max_age
            })
            domain += [('age', '<=', max_age)]

        if kw.get('contact_age_filter') or request.session.get('contact_age_filter'):
            if kw.get('contact_age_filter'):
                min_age = int(kw.get('contact_age_filter').split('-')[0])
                max_age = int(kw.get('contact_age_filter').split('-')[1])
                request.session['contact_age_filter'] = kw.get('contact_age_filter')
            if not kw.get('contact_age_filter') and request.session.get('contact_age_filter'):
                min_age = int(request.session.get('contact_age_filter').split('-')[0])
                max_age = int(request.session.get('contact_age_filter').split('-')[1])
            filter_data.update({
                'contact_age_filter': request.session.get('contact_age_filter'),
            })
            domain += [('age', '>=', min_age), ('age', '<=', max_age)]

        # Covid Positive and Negative Filter
        if kw and not kw.get('positive_check') and request.session.get('positive_check'):
            request.session.pop('positive_check')
        if kw and not kw.get('negative_check') and request.session.get('negative_check'):
            request.session.pop('negative_check')

        partner_ids = []
        if kw.get('positive_check') or request.session.get('positive_check'):
            if kw.get('positive_check'):
                request.session['positive_check'] = True
            sql = """
                SELECT er1.partner_id FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
                LEFT JOIN event_report AS er2 ON er2.id = er1.id
                WHERE er2.state = 'positive'
            """
            request.env.cr.execute(sql)
            partner_ids_data = request.env.cr.fetchall()
            partner_ids += [partner[0] for partner in partner_ids_data]
            filter_data.update({
                'positive_check': True
            })

        if kw.get('negative_check') or request.session.get('negative_check'):
            if kw.get('negative_check'):
                request.session['negative_check'] = True
            sql = """
                SELECT er1.partner_id FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
                LEFT JOIN event_report AS er2 ON er2.id = er1.id
                WHERE er2.state = 'negative'
            """
            request.env.cr.execute(sql)
            partner_ids_data = request.env.cr.fetchall()
            partner_ids += [partner[0] for partner in partner_ids_data]
            filter_data.update({
                'negative_check': True
            })

        # Appointment Date Filter
        calendar_event_domain = []
        if kw.get('app_date_from') or request.session.get('app_date_from'):
            if kw.get('app_date_from'):
                date_from = kw.get('app_date_from')
                request.session['app_date_from'] = date_from
            else:
                date_from = request.session.get('app_date_from')
            filter_data.update({
                'app_date_from': date_from
            })
            date_from += " 00:00:00"
            calendar_event_domain += [('start_datetime', '>=', date_from)]

        if kw.get('app_date_to') or request.session.get('app_date_to'):
            if kw.get('app_date_to'):
                date_to = kw.get('app_date_to')
                request.session['app_date_to'] = date_to
            else:
                date_to = request.session.get('app_date_to')
            filter_data.update({
                'app_date_to': date_to
            })
            date_to += " 23:59:59"
            calendar_event_domain += [('start_datetime', '<=', date_to)]

        if calendar_event_domain:
            if partner_ids:
                calendar_event_domain += [('patient_partner_id', 'in', partner_ids)]
            calendar_event_recs = request.env['calendar.event'].sudo().search(calendar_event_domain)
            partner_ids += calendar_event_recs.mapped('partner_ids').ids

        if filter_data.get('negative_check') or filter_data.get('positive_check') or calendar_event_domain:
            domain += [('id', 'in', partner_ids)]

        total_login_partner_child = request.env['res.partner'].sudo().search_count(domain)


        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name'},
            'age': {'label': _('Age'), 'order': 'age'},
        }

        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']

        pager = portal_pager(
            url="/my/child/employees",
            url_args={'name': name, 'sortby': sortby},
            total=total_login_partner_child,
            page=page,
            step=15
        )
        child_partner_recs = request.env['res.partner'].sudo().search(domain, order=sort_order, limit=15, offset=pager['offset'])
        sql_query = """
            SELECT er1.partner_id, er2.state FROM (SELECT partner_id, max(id) AS id FROM event_report GROUP BY partner_id) AS er1
            LEFT JOIN event_report AS er2 ON er2.id = er1.id
            WHERE er2.state = 'positive'
        """
        request.env.cr.execute(sql_query)
        partner_covid_result = request.env.cr.fetchall()
        values = {
            'child_contacts': child_partner_recs,
            'page_name': 'child_contact',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'partner_covid_result': dict(partner_covid_result),
            'sortby': sortby,
            'filter_data': filter_data,
            'partner_id': partner.id,
        }
        return http.request.render('covid_appointment.child_employee_list', values)

    @http.route(['/view/covid_reports/<model("res.partner"):partner>'], type='http', auth="user", website=True)
    def display_partner_covid_appointments(self, partner, **kw):
        calendar_event_data = []
        calendar_event = request.env['calendar.event'].sudo()
        calendar_event_recs = calendar_event.search([('partner_ids', 'in', partner.ids)])
        for event_rec in calendar_event_recs:

            user_timezone = self.event_id.user_id.tz
            if not user_timezone:
                user_timezone = "Europe/Amsterdam"
            
            event_datetime = event_rec.start_datetime.astimezone(timezone(user_timezone))
            event_data = {
                'appointment_id': event_rec.event_name,
                'date': event_datetime.strftime('%d-%m-%Y %H:%M'),
                'test_center': event_rec.appointment_type_id.name,
                'partner_name': event_rec.patient_partner_id.name,
                'company_ref': event_rec.patient_partner_id.parent_id.name,
                'appointment_status': dict(event_rec._fields['state'].selection).get(event_rec.state),
                'covid_status': False,
                'link': event_rec.qr_code_string,
            }
            if event_rec.state == 'done' and event_rec.event_report_ids:
                event_data.update({
                    'covid_status': event_rec.event_report_ids[0].state.capitalize()
                })
            calendar_event_data.append(event_data)
        values = {
            'contact': partner,
            'calendar_event_data': calendar_event_data,
            'page_name': 'child_contact',
        }
        return http.request.render('covid_appointment.view_contact_covide_appointment', values)
