odoo.define('covid_appointment.website_calendar_form', function (require) {
"use strict";

    var publicWidget = require('web.public.widget');
    var websiteCalendarForm = publicWidget.registry.websiteCalendarForm;

    return websiteCalendarForm.include({
        events: _.extend({}, websiteCalendarForm.events, {
            'click button[type="submit"]': '_check_form_data'
        }),
        _check_form_data: function(ev){
            var phone_val = $('#phone_field').val();
            var filter = /^((\+[1-9]{1,4}[ \-]*)|(\([0-9]{2,3}\)[ \-]*)|([0-9]{2,4})[ \-]*)*?[0-9]{3,4}?[ \-]*[0-9]{3,4}?$/;
            if (filter.test(phone_val)) {
                if(phone_val.length==14){
                   var validate = true;
                }
                else {
                    var validate = false;
                    $('#phone_error_msg').remove();
                    $("<p id='phone_error_msg' style='color:red;'>Please put 10 digit mobile number.</p>").insertAfter("#phone_field");
                    ev.preventDefault();
                }
            }
            else {
                var validate = false;
                $('#phone_error_msg').remove();
                $("<p id='phone_error_msg' style='color:red;'>Please Add valid phone number.</p>").insertAfter("#phone_field");
                ev.preventDefault();
            }
            if (validate){
                $('#phone_error_msg').remove();
            }
            if (!$('#flexCheckChecked').prop('checked')){
                $('#term_error_msg').remove();
                $("<p id='term_error_msg' style='color:red;'>Accept terms and conditions to proceed.</p>").appendTo("#term_condition_div");
                ev.preventDefault();   
            }

        },
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