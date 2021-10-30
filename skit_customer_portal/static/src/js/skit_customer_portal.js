odoo.define('skit_customer_portal.portal_js', function (require) {
    "use strict";
    var ajax = require('web.ajax');
 
/*	$('#submit_doc').click(function(){
		var post = {}
		ajax.jsonRpc('/send_message/popup', 'call', post).then(function (modal) {
			var $modal = $(modal);	
			var $form = $('.submit_document_form');
		    $modal.appendTo($form).modal();	
		    $modal.on('click', '.send_btn', function (e) {
				var file = document.getElementById('doc_attachment').files[0];
				if(file != undefined){
					var reader = new FileReader();
	                reader.onload = function(event) {
						var file_details = []
						file_details.push({
							'file_name': file.name,
							'file_content': event.target.result,
						});
						var line_vals_post = {}
						line_vals_post['file_details'] = file_details
						ajax.jsonRpc('/required_document/save/action', 'call', line_vals_post).then(function (attachment_id) {
							alertify.alert("Success", "Document saved successfully.")
						});
	                };
	                reader.readAsDataURL(file)
				}
	  		});
		});
	});*/
	
})