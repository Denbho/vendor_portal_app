odoo.define('skit_customer_portal.portal.chatter', function (require) {
'use strict';

var portalChatter = require('portal.chatter');
var core = require('web.core');
var qweb = core.qweb;
/**
 * Extends Frontend Chatter to handle submit document
 */
portalChatter.PortalChatter.include({
    
	/*events: _.extend({}, portalChatter.PortalChatter.prototype.events, {
        'click .tablinks': '_onClickTablink',
    }),*/
   
	xmlDependencies: (portalChatter.PortalChatter.prototype.xmlDependencies || [])
		.concat(['/skit_customer_portal/static/src/xml/portal_chatter.xml']),
     
/*	_onClickTablink: function (evt) {
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
		if(evt.currentTarget.id == 'log_note' && window.location.pathname.indexOf("/helpdesk/ticket/") == 0){
			$(".chatter_msg_div").css("display", "none");
		}
		else if(evt.currentTarget.id == 'send_msg' && window.location.pathname.indexOf("/helpdesk/ticket/") == 0){
			$(".chatter_msg_div").css("display", "block");
		}
		this.$('.o_portal_chatter_messages').html(qweb.render("portal.chatter_messages", {widget: this}));
	},*/
});
});
