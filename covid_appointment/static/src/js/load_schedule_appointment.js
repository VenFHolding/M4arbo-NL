odoo.define('covid_appointment.appointmentjs', function (require) {
"use strict";
    
    var publicWidget = require('web.public.widget');
    var websiteCalendarSelect = publicWidget.registry.websiteCalendarSelect;


    return websiteCalendarSelect.include({
        events: _.extend({
            'change #company_ref': 'update_test_centers',
            'click button[type="submit"]': 'check_input_values'
        }, websiteCalendarSelect.prototype.events),

        start: function (parent) {
            this._super.apply(this, arguments);
            $("#calendarType option").prop("selected", false);
            $("#calendarType").prop("disabled", false);
            $('#calendarType').empty();
            $('.o_calendar_intro').html('');
            $('#error_message_section').css('display', 'none');
        },

        check_input_values: function(ev){
            var self = this;
            var company_ref = self.$el.find('#company_ref').val();
            var calendarType = self.$el.find('#calendarType').children("option:selected").val();
            if (!company_ref){
                $('#company_ref').css('border-color', 'red');
                ev.preventDefault()
            }
            if (!calendarType){
                $('#calendarType').css('border-color', 'red');
                ev.preventDefault()
            }
        },

        _onAppointmentTypeChange_duplicate: function (ev) {
            var appointmentID = ev.children("option:selected").val();
            var previousSelectedEmployeeID = $(".o_website_appoinment_form select[name='employee_id']").val();
            var postURL = '/website/calendar/' + appointmentID + '/appointment';
            $(".o_website_appoinment_form").attr('action', postURL);
            this._rpc({
                route: "/website/calendar/get_appointment_info",
                params: {
                    appointment_id: appointmentID,
                    prev_emp: previousSelectedEmployeeID,
                },
            }).then(function (data) {
                if (data) {
                    $('.o_calendar_intro').html(data.message_intro);
                    if (data.assignation_method === 'chosen') {
                        $(".o_website_appoinment_form div[name='employee_select']").replaceWith(data.employee_selection_html);
                    } else {
                        $(".o_website_appoinment_form div[name='employee_select']").addClass('o_hidden');
                        $(".o_website_appoinment_form select[name='employee_id']").children().remove();
                    }
                }
            });
        },


        update_test_centers: function(){
            var self = this;
            var value = self.$el.find('#company_ref').val();
            value = value.trim()
            this._rpc({
                route: "/get_company_appointments",
                params: {
                    data: {'company_ref': value},
                },
            }).then(function (data) {
                if (data){
                    self.$el.find('#error_message_section').css('display', 'none');
                    var appointments = data;
                    $("#calendarType option").prop("selected", false);
                    $('#calendarType').empty();
                    for (var i = 0; i < appointments.length; i++) {
                        var appointment = appointments[i];
                        var option_html = '<option value=' + appointment['id']
                        if (i == 0){
                            option_html += ' selected="selected"'
                        }
                        option_html += '>' + appointment['name']+'</option>'
                        $('#calendarType').append(option_html);
                    }
                    self._onAppointmentTypeChange_duplicate(self.$el.find('#calendarType'))
                }
                else {
                    self.$el.find('#error_message_section').css('display', 'block');
                    $("#calendarType option").prop("selected", false);
                    $('#calendarType').empty();
                }
            });
        },

    });
});
