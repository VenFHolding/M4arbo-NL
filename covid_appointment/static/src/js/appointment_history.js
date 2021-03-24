odoo.define('covid_appointment.view_covid_appointment_history', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.websiteViewHistory = publicWidget.Widget.extend({
    selector: '.view_covid_appoitment_history',
    events: {
        'click button[id="search_history"]': '_onSearchAppointments'
    },

    _onSearchAppointments: function (ev) {
        var company_ref_val = $('#company_ref').val();
        var email_val = $('#email').val();
        if (!company_ref_val){
            $('#company_ref').css('border-color', 'red');
            ev.preventDefault()
        }
        if (!email_val){
            $('#email').css('border-color', 'red');
            ev.preventDefault()
        }
    },
});
});
