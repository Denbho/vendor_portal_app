odoo.define('website.vendor.view_full_profile', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var session = require('web.session');
var core = require('web.core');
var QWeb = core.qweb;

publicWidget.registry.ViewFullProfile = publicWidget.Widget.extend({
    selector: '.view_full_profile_form',
    events: {
        'click .tablinks': '_onClickTablink',
    },
    start: function () {
        return this._super();
    },
     
	_onClickTablink: function (evt) {
		var i, tabcontent, tablinks;
		tabcontent = document.getElementsByClassName("tabcontent");
		for (i = 0; i < tabcontent.length; i++) {
			tabcontent[i].style.display = "none";
		}
		tablinks = document.getElementsByClassName("tablinks");
		for (i = 0; i < tablinks.length; i++) {
			tablinks[i].className = tablinks[i].className.replace(" active", "");
		}
		var current_id = evt.currentTarget.id;
		var current_tabcontent = current_id.concat("_tabcontent");
		
		var elems = document.getElementsByClassName(current_tabcontent);
		for (var i=0;i<elems.length;i+=1){
		  elems[i].style.display = 'block';
		}
		evt.currentTarget.className += " active";
	},
});
});
