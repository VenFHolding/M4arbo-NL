# -*- coding: utf-8 -*-
{
    'name': "Covid Appointments",
    'summary': """
        Online Covid Appointments
    """,
    'description': """
        This app  adds the feature of handling booking of an Online Covid Test 
        of Odoo users.Everything happens through Odoo. It is completely secure.

    """,
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'http://www.pragtech.co.in',
    'license': 'OPL-1',
    'category': 'Appointment',
    'version': '13.0.3.18.0',
    'depends': ['website_calendar', 'contacts'],
    'data': [
        'security/appointment_security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence_data.xml',
        'data/mail_template.xml',
        'data/cancel_event_template.xml',
        'data/achieved_event_template.xml',
        'data/appointment_results_template.xml',
        'data/cron_job.xml',
        'reports/calendar_event_report_paperformat.xml',
        'reports/calendar_event_report_template.xml',
        'reports/calendar_event_report.xml',
        'wizard/archived_reason_wizard_views.xml',
        'wizard/cancel_reason_wizard_views.xml',
        'wizard/appointment_slots_wizard_view.xml',
        'views/assets.xml',
        'views/res_partner_views.xml',
        'views/calendar_event_views.xml',
        'views/hr_employee_views.xml',
        'views/event_report_views.xml',
        'views/upload_document_template.xml',
        'views/website_calendar_templates.xml',
        'views/schedule_appointment_template.xml',
        'views/appointment_report_views.xml',
        'views/appointment_history_template.xml',
        'views/policy_terms_template.xml',
        'views/website_policy_config_view.xml',
        'views/calendar_appointment_views.xml',
        'views/covid_portal_template.xml',
        'views/menus.xml',
    ],
}
