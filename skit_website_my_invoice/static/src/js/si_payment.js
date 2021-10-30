odoo.define('skit_website_my_invoice.si_payment', function (require) {
'use strict';

var ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
var time = require('web.time');

var si_payment_form_widget;

publicWidget.registry.SiPaymentDetails = publicWidget.Widget.extend({
    selector: '.si_payment_table',
    events: {
    	'click .edit_si_payment': '_onEditPayDetails',
    	'click .sipay_file_view': '_showPayDocument',
    	'click .show_attachment_view': '_showMultiAttachPopup',
    },
    start: function () {
    	var self = this;
    	si_payment_form_widget = this;
		this.edit_pay_attach_file_list = [];
        return this._super.apply(this, arguments);
    },
    _onEditPayDetails: function (evt) {
    	var post = {}
    	var $form = $('.si_payment_table');
	    var pay_id = $(evt.currentTarget).attr('pay_id');
	    var action = $(evt.currentTarget).attr('action');
	    var si_id = $(evt.currentTarget).attr('si_id');
	    post['pay_id']= pay_id;
	    post['si_id']= si_id;
	    ajax.jsonRpc(action, 'call', post).then(function (pod_modal) { 
			var $pod_modal = $(pod_modal);
			$pod_modal.appendTo($form).modal();
			/**
			* <!-- START Set Date Format for popup date fields from Odoo Language settings
			**/
			var datepickers_options = {
    			minDate: moment({ y: 1900 }),
    			maxDate: moment({ y: 9999, M: 11, d: 31 }),
    			calendarWeeks: true,
                icons : {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    next: 'fa fa-chevron-right',
                    previous: 'fa fa-chevron-left',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down',
              	},
                locale : moment.locale(),
                format : time.getLangDatetimeFormat(),
      	  	};
			datepickers_options.format = time.getLangDateFormat();            
			$('#or_date').datetimepicker(datepickers_options);
			$('#release_date').datetimepicker(datepickers_options);
			/**
			* Set Date Format for popup date fields from Odoo Language settings END --> 
			**/
			si_payment_form_widget.edit_pay_attach_file_list = [];
			$('#sipay_attach_fileList li').each(function(){
				si_payment_form_widget.edit_pay_attach_file_list.push({
						'file_name': $(this).attr('data'),
						'file_content': $(this).attr('file_data'),
						'att_id': $(this).attr('id')
				});
			});
			$(".remove-list").off().on('click', function(){
				var file_name = $(this).parent('li').attr('data');
				si_payment_form_widget.edit_pay_attach_file_list = si_payment_form_widget.edit_pay_attach_file_list.filter((el) => {
					return el.file_name !== file_name;
				});
			});
			$pod_modal.on('click', '#si_payment_save', function(ev){
				var self = $(this)
				var values = {}
				var mandatory = false;
				var save_action = $(this).attr('action');
				var file_attach = false;
				$('.new_form_popup input').each(function(){
					if($(this).attr('required') && !$(this).val()){
						mandatory = true;
						$(this).addClass('required_style')
					}
					if($(this).attr('name'))
						values[$(this).attr('name')] = $(this).val();
				});
				values['remark'] = $('.pay_remark').val();
				/** Get attachment details */
				var file_details = si_payment_form_widget.edit_pay_attach_file_list;
				if (file_details.length >0){
					file_attach = true;
				}
				if(!mandatory){
					var save_post = {'datas': values,
									'pay_id': $(this).attr('pay_id'),
									'si_id': $(this).attr('si_id'),
									'pay_files': file_details,
									'file_attach': file_attach
									}
					ajax.jsonRpc(save_action, 'call', save_post).then(function (modal){
						$pod_modal.empty();
					    $pod_modal.modal('hide');
					    $('.si_payment_edit_popup').remove();
					    location.reload();
					});
					
				}
			});
			$pod_modal.on('click', '#si_payment_close', function(ev){
				$pod_modal.empty();
			    $pod_modal.modal('hide');
			    $('.si_payment_edit_popup').remove();
			});
			// Attachment click action
			$pod_modal.on('click', '.sipay_file_upload', function(ev){
				$(".pay_file_input").click();
				// Read upload file
				$(".pay_file_input").off().on('change', function(){
					var output = document.getElementById('sipay_attach_fileList');
		      		var children = "";
					_.map($(".pay_file_input")[0].files, function (file) {
							var reader = new FileReader();
							children +=  '<li id="0" data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
							reader.onload = function (e) {
								si_payment_form_widget.edit_pay_attach_file_list.push({
								'file_name': file.name,
								'file_content': e.target.result,
								'att_id': 0
							});
							$(".remove-list").off().on('click', function(){
								var file_name = $(this).parent('li').attr('data');
								si_payment_form_widget.edit_pay_attach_file_list = si_payment_form_widget.edit_pay_attach_file_list.filter((el) => {
									return el.file_name !== file_name;
								});
							});
					        }			    
					        reader.readAsDataURL(file);
						});
						output.innerHTML += children;
				    });
				});
		});
    },
    /**
     * @private
		* @param {Object} ev
     * Show Delivery Document
     */
	_showPayDocument: function(ev){
		var $form = $('.si_payment_table');
		var id = $(ev.currentTarget).attr('id');
		var action = $(ev.currentTarget).attr('action');
		var post = {'att_id': id}
		ajax.jsonRpc(action, 'call', post).then(function (modal) { 
			var $modal = $(modal);
			$modal.appendTo($form).modal();	
			$modal.on('click', '.dl_pdf_close', function(ev){
				$modal.empty();
				$modal.modal('hide');
				$('.dl_file_view_popup').remove();
			});
		})
	},
    /**
     * @private
		* @param {Object} ev
     * Show Multiple Attachment Popup
     */
	_showMultiAttachPopup: function(ev){
		var $form = $('.si_payment_table');
		var pay_id = $(ev.currentTarget).attr('pay_id');
		var action = $(ev.currentTarget).attr('action');
		var post = {'pay_id': pay_id}
		ajax.jsonRpc(action, 'call', post).then(function (modal) { 
			var $modal = $(modal);
			$modal.appendTo($form).modal();	
			$modal.on('click', '.multi_attach_close', function(ev){
				$modal.empty();
				$modal.modal('hide');
				$('.multi_attach_view_popup').remove();
			});
			// Open PDf document
			$modal.on('click', '.dl_file_view', function(ev){
				var id = $(ev.currentTarget).attr('id');
				var action = $(ev.currentTarget).attr('action');
				var post = {'att_id': id}
				ajax.jsonRpc(action, 'call', post).then(function (modal) { 
					var $modal = $(modal);
					$modal.appendTo($form).modal();	
					$modal.on('click', '.dl_pdf_close', function(ev){
						$modal.empty();
						$modal.modal('hide');
						$('.dl_file_view_popup').remove();
					});
				})
			});
		})
	},
	
    
});

});