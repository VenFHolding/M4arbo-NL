odoo.define('covid_appointment.website_calendar_form', function (require) {
"use strict";

    var publicWidget = require('web.public.widget');
    var websiteCalendarForm = publicWidget.registry.websiteCalendarForm;

    return websiteCalendarForm.include({
        start: function(parent){
            this._super.apply(this, arguments);
            var dtToday = new Date();
            var month = dtToday.getMonth() + 1;
            var day = dtToday.getDate();
            var year = dtToday.getFullYear();
            if(month < 10)
                month = '0' + month.toString();
            if(day < 10)
                day = '0' + day.toString();
            
            var maxDate = year + '-' + month + '-' + day;
            $('#dob_datepicker_calendar_form').prop('max', maxDate);

            this._onCountryChange(this);
            var country_length = $('#country_field option').length;
            if (country_length == 1){
                $("#country_field").val($("#country_field option:first").val());
                $('#country_field').attr("disabled", true);
            }
        },
    });
});