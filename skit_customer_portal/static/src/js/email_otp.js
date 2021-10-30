odoo.define('skit_customer_portal.email_otp', function (require) {
"use strict";

var core = require('web.core');
var _t = core._t;
var ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
var Dialog = require('web.Dialog');

publicWidget.registry.LoginForm = publicWidget.Widget.extend({
    selector: '.oe_login_form',
    events: {
        'submit': '_onSubmit',
        'click #resend_otp': '_onResendOTP',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onSubmit: function () {
        var $btn = this.$('.oe_login_buttons > button[type="submit"]');
        $btn.attr('disabled', 'disabled');
        $btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
    },
    
    _onResendOTP: function () {
    	var self = this;
    	var login = $('#login').val();
		var post = {}
		post['login'] = login;
		ajax.jsonRpc('/resend/otp', 'call', post).then(function (modal) { 
    		Dialog.alert(this, _t('OTP has been resend to your email address.'), {
                title: _t('Success'),
            });
    	});
    },
});
	
});