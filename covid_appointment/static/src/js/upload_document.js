odoo.define('covid_appointment.upload_document_form', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.website_fill_covid_data = publicWidget.Widget.extend({
        selector: '.view_update_covid_status',
        events: {
        'click input[id="is_test_achived_yes"]': '_onClick_is_test_achived_yes',
        'click input[id="is_test_achived_no"]': '_onClick_is_test_achived_no',
        'click input[name="is_positive"]': '_onClick_is_positive',
        },

        start: function(parent){
            this._super.apply(this, arguments);
            $('.check_postive').css('display', 'none');
            $('.not_achived_reason').css('display', 'none');
            $('.test_failed_reason').css('display', 'none');
        },
        _onClick_is_test_achived_yes: function(ev){
            $('.check_postive').css('display', 'table-row');
            $('input[name="is_positive"]').prop('checked', false);
            $('.not_achived_reason').css('display', 'none');
            $('.test_failed_reason').css('display', 'none');
        },

        _onClick_is_test_achived_no: function(ev){
            $('.check_postive').css('display', 'none');
            $('.not_achived_reason').css('display', 'table-row');
            $('.test_failed_reason').css('display', 'none');
        },

        _onClick_is_positive: function(ev){
            if (ev.currentTarget.value == 'failed'){
                $('.test_failed_reason').css('display', 'table-row');
            }
            else{
                $('.test_failed_reason').css('display', 'none');   
            }
        },

    })
});