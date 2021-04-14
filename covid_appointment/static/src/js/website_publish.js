odoo.define('website.backend.button.inherited', function (require) {
'use strict';

    var BackendButton = require('website.backend.button');
    var field_registry = require('web.field_registry');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var _t = core._t;

    return field_registry.get('website_redirect_button').include({
        _onClick: function(){
            if (this.record.model == 'calendar.appointment.type'){
                if (this.record.data.employee_ids.count == 0){
                    var $content = $('<p/>').text(_t('Please add Medical Staff before publish.'));
                    return new Dialog(this, {
                        title: 'Validation Error',
                        size: 'medium',
                        $content: $content,
                        buttons: [{
                            text: _t('Cancel'),
                            close: true
                        }]
                    }).open();
                }
            }
            this._super.apply(this);
        }
    })
})
