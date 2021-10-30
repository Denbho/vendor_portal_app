odoo.define('skit_vendor_portal.vendor_signature_form', function (require) {
'use strict';

var core = require('web.core');
var SignatureForm = require('portal.signature_form').SignatureForm;
var qweb = core.qweb;
var _t = core._t;
var ajax = require('web.ajax');

SignatureForm.include({
	events: _.extend({}, SignatureForm.prototype.events, {
        'click .vendor_o_portal_sign_submit': 'async _onClickVendorSubmit'
    }),
	
	init: function (parent, options) {
        this._super.apply(this, arguments);
	},

	/**
     * Handles click on the submit button.
     *
     * This will get the current name and signature and validate them.
     * If they are valid, they are sent to the server, and the reponse is
     * handled. If they are invalid, it will display the errors to the user.
     *
     * @private
     * @param {Event} ev
     * @returns {Deferred}
     */
    _onClickVendorSubmit: function (ev){
		var bidder_id = $(ev.currentTarget).attr('id');
		var action = $(ev.currentTarget).attr('action');
		var name = this.nameAndSignature.getName();
	   	var signature = this.nameAndSignature.getSignatureImage()[1];
		var post = {'id': bidder_id,
					'name': name,
					'signature': signature}
		ajax.jsonRpc(action, 'call', post).then(function (result){
			
		});
	}
});

});