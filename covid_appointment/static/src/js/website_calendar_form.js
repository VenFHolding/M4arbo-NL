odoo.define('covid_appointment.website_calendar_form', function (require) {
"use strict";

    var publicWidget = require('web.public.widget');
    var websiteCalendarForm = publicWidget.registry.websiteCalendarForm;

    return websiteCalendarForm.include({
        events: {
            'click button[type="submit"]': '_check_form_data',
            'change .appointment_submit_form select[name="country_id"]': '_onCountryChange',
        },
        _check_form_data: function(ev){
            var validate = true;
            var phone_val = $('#phone_field').val();
            var gender_val = $('#gender_calendar_form').val();
            var partner_email = $('#partner_email').val();
            var dob_val = $('#dob_datepicker_calendar_form').val();
            var partner_name = $('#partner_name').val();
            var phone_pattern = /^((\+[1-9]{1,4}[ \-]*)|(\([0-9]{2,3}\)[ \-]*)|([0-9]{2,4})[ \-]*)*?[0-9]{3,4}?[ \-]*[0-9]{3,4}?$/;
            var email_pattern = /^([\w-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([\w-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/;
            if (phone_pattern.test(phone_val)) {
                if(phone_val.length==14){
                   var validate = true;
                   $('#phone_error_msg').remove();
                }
                else {
                    var validate = false;
                    $('#phone_error_msg').remove();
                    $("<p id='phone_error_msg' style='color:red;'>Please put 10 digit mobile number.</p>").insertAfter("#phone_field");
                }
            }
            else {
                var validate = false;
                $('#phone_error_msg').remove();
                $("<p id='phone_error_msg' style='color:red;'>Please Add valid phone number.</p>").insertAfter("#phone_field");
            }
            if (!$('#flexCheckChecked').prop('checked')){
                var validate = false;
                $('#term_error_msg').remove();
                $("<p id='term_error_msg' style='color:red;'>Accept terms and conditions to proceed.</p>").appendTo("#term_condition_div");
            }
            else{
                $('#term_error_msg').remove();
            }
            if (!dob_val){
                var validate = false;
                $('#dob_error_msg').remove();
                $("<p id='dob_error_msg' style='color:red;'>Please enter your Date of Birth.</p>").insertAfter("#dob_datepicker_calendar_form");
            }
            else{
                $('#dob_error_msg').remove();
            }
            if (!partner_name){
                var validate = false;
                $('#partner_name_error_msg').remove();
                $("<p id='partner_name_error_msg' style='color:red;'>Please enter your name.</p>").insertAfter("#partner_name");
            }
            else{
                $('#partner_name_error_msg').remove();
            }
            if (!partner_email){
                var validate = false;
                $('#partner_email_error_msg').remove();
                $("<p id='partner_email_error_msg' style='color:red;'>Please enter email address.</p>").insertAfter("#partner_email");
            }
            else{
                if (!email_pattern.test(partner_email)) {
                    validate = false;
                    $('#partner_email_error_msg').remove();
                    $("<p id='partner_email_error_msg' style='color:red;'>Please enter valid email address.</p>").insertAfter("#partner_email");
                }
                else{
                    $('#partner_email_error_msg').remove();
                }              
            }
            if (!gender_val){
                validate = false;
                $('#partner_gender_error_msg').remove();
                $("<p id='partner_gender_error_msg' style='color:red;'>Please select gender.</p>").insertAfter("#gender_calendar_form");

            }
            else{
                $('#partner_gender_error_msg').remove();
            }
            if (!validate){
                ev.preventDefault();
            }
            else {
                $('#phone_error_msg').remove();
                $('#term_error_msg').remove();
                $('#phone_error_msg').remove();
                $('#dob_error_msg').remove();
                $('#partner_gender_error_msg').remove();
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
                $('#country_field').attr("readonly", true);
            }
        },
    });
});