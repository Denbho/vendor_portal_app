odoo.define('skit_website_my_po.my_po_decline', function (require) {
'use strict';

var ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
var time = require('web.time');
var po_del_form_widget;
    
    
publicWidget.registry.websitePOForm = publicWidget.Widget.extend({
        selector: '.po_form_details',
        events: {
        	'click #po_decline': '_clickDecline_po',
        	'click #po_accept': '_clickAccept_po',
            'click #po_col_expand': '_changeCollapseText',
			'click .po_deli_new': '_newPODelivery',
			'click .po_deli_edit': '_newPODelivery',
			'click .po_deli_delete': '_deleteDL',
			'click input': 'removeRequired',
			'click .dl_file_upload': '_clickAttach',
			'click .dl_file_view': '_showDLDocument',
			'click .dl_all_check': '_selectAll',
			'click .show_attachment_view': '_showAttachPopup',
			'click .po_or_number_edit': '_editORNumber',
			'click .po_or_number_save': '_saveORNumber',
			'click .po_or_attachment': '_uploadPayAttach'
        },
        
        /**
	     * @constructor
	     */
	    init: function () {
	        this._super.apply(this, arguments);
	    },
        
        /**
         * @override
         */
        start: function () {
            var self = this;
			po_del_form_widget = this;
			this.dl_attch_file_list = [];
            return this._super.apply(this, arguments);
        },
        /**
		 * @private
		 * @param {Object} ev
         * Decline POPUP
		 */
        _clickDecline_po: function (ev) {
        	var post = {};
        	var $form = $('.po_decline_panel');
        	var order_id = $(ev.currentTarget).attr('orderid');
    		ajax.jsonRpc('/po/decline_popup', 'call', post).then(function (modal) {
    			var $modal = $(modal);			
    			$modal.appendTo($form).modal();	
    			//update status
    			$modal.on('click', '#decline_confirm', function(ev){
    				var po_status =  $("#po_status").text();
    				var declined_note =  $("#declined_note").val();
    				var declined_reason_id = $("#declined_reason_id option:selected").val();
    				post['order_id'] = order_id;
    				post['po_status'] = po_status;
    				post['declined_note'] = declined_note;
    				post['reason_id'] = declined_reason_id;
    				if(declined_note && declined_reason_id){
      		    		ajax.jsonRpc('/update/po/declined_status', 'call', post).then(function (modal) { 
      		    			alertify.alert('Confimation','Purchase Order Declined.');
      		    			$('.po_status_head').text('Declined');
      		    			$('.po_status_head').attr('class','po_status_head po_declined');
      		    			$('.po_decline_panel').css({'display':'none'})
    	  		    	});
      		    		$modal.empty();
    			    	$modal.modal('hide');
    					$('.po_decline_popup').remove();
      		    	}
      		    	else{
    	  				alertify.alert('Message','Please enter remarks reason.'); 
     				     return false;
      		    	}
    			});
    			$modal.on('click', '#decline_cancel', function(ev){
    				$modal.empty();
    		    	$modal.modal('hide');
    		    	$('.po_decline_popup').remove();
    			});
    		});
        },
        /**
		 * @private
		 * @param {Object} ev
         * Accept PO
		 */
        _clickAccept_po: function (ev) {
        	var post = {};
        	var order_id = $(ev.currentTarget).attr('orderid');
        	post['order_id'] = order_id;
    		ajax.jsonRpc('/update/po/accept_status', 'call', post).then(function (modal) {
    			 alertify.alert('Confimation','Purchase Order Accepted.').set('onok', function(closeEvent){ window.location.reload();} ); 
    			$('.po_status_head').text('Accepted');
      			$('.po_status_head').attr('class','po_status_head po_accepted');
    			$('.po_decline_panel').css({'display':'none'})
    		});
        },
		/**
         * @private
         * @param {Object} ev
         * Remove Required Class
         */
		removeRequired(ev){
			$(ev.currentTarget).removeClass('required_style');
		},
		/**
         * @private
         * @param {Object} ev
         * Change the Expand and Collapse Text
         */
		_changeCollapseText(ev){
			if($('#po_instruction').hasClass('show')){
				$(ev.currentTarget).html('<i class="fa fa-angle-down po_collapse_icon" data-toggle="collapse" data-target="#po_instruction" />Expand this PO');
			}else{
				$(ev.currentTarget).html('<i class="fa fa-angle-up po_collapse_icon" data-toggle="collapse" data-target="#po_instruction" />Collapse this PO');
			}
		},
		/**
		 * @private
		 * @param {Object} ev
         * Select and De-Select the all PO Delivery
		 */
		_selectAll: function(ev){
			if($(ev.currentTarget).is(':checked')){
				$('.dl_row_check').each(function(){
					$(this).prop( "checked", true );
				});
			}else{
				$('.dl_row_check').each(function(){
					$(this).prop( "checked", false );
				});
			}
		},

		/**
		 * @private
		 * @param {Object} ev
         * Delete the PO Delivery Line
		 */
		_deleteDL: function(ev){
			var id = $(ev.currentTarget).attr('id');
			var action = $(ev.currentTarget).attr('action');
			var post = {'id': id}
			alertify.confirm('Confirm','Are you sure you want to delete?',
	  		    function(){
					ajax.jsonRpc(action, 'call', post).then(function (result){
						var tr = $(ev.currentTarget).closest('tr');
	  					tr.remove();
						var last_row = $('.po_del_table tbody tr:last').prev();
						var last_td = last_row.find('td:last').removeClass('v_display_none');
						var row = $('.po_del_table tbody tr').length;
	  					if(row==1){
			  		    	$('.po_del_table tr#delivery_empty').removeClass('v_display_none');
			  		    }
					});
	  			},
	  			function(){
	  			})
		},
		/**
		 * @private
		 * @param {Object} ev
         * Create a new PO Delivery
		 */
		_newPODelivery: function(ev){
			ev.preventDefault();
	    	var self = this;
	    	var post = {};
	    	var $form = $('.po_delivery_form');
			var values = {};
			var deli_row = "";
			var deli_class = $(ev.currentTarget).attr('class');  
			if(deli_class == 'fa fa-plus po_deli_new'){
				deli_row = $(ev.currentTarget).closest('tr#delivery_empty');
			}else{
				deli_row=$(ev.currentTarget).closest('tr.delivery_row');
			}
			deli_row.each(function(){
				$(this).find('td').each(function(){
					if($(this).attr('name')){
						values[$(this).attr('name')] = $(this).text();
					}
				})
			});
			post['datas'] = values;
			post['id'] = $(ev.currentTarget).attr('id');
			post['po_id'] = $(ev.currentTarget).attr('po_id');
			var action = $(ev.currentTarget).attr('action')
	    	self.create_delivery_popup(action, post, $form);
		},
		
		create_delivery_popup: function(action, post, $form){
			ajax.jsonRpc(action, 'call', post).then(function (modal) { 
				var $modal = $(modal);
				$modal.appendTo($form).modal();	
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
              $('#receiving_date').datetimepicker(datepickers_options);
              $('#dr_date').datetimepicker(datepickers_options);
			  $('#dr_date').off().on('click', function(){
					$('input[data-target="#dr_date"]').each(function(){
						$(this).removeClass('required_style')
					})
			  })
			  $('#receiving_date').off().on('click', function(){
					$('input[data-target="#receiving_date"]').each(function(){
						$(this).removeClass('required_style')
					})
			  })
			/**
			* Set Date Format for popup date fields from Odoo Language settings END --> 
			**/
				
				po_del_form_widget.dl_attch_file_list = [];
				$('#dl_attach_fileList li').each(function(){
					po_del_form_widget.dl_attch_file_list.push({
							'file_name': $(this).attr('data'),
							'file_content': $(this).attr('file_data'),
							'att_id': $(this).attr('id')
					});
				});
				$(".remove-list").off().on('click', function(){
					var file_name = $(this).parent('li').attr('data');
					po_del_form_widget.dl_attch_file_list = po_del_form_widget.dl_attch_file_list.filter((el) => {
						return el.file_name !== file_name;
					});
				});
				$modal.on('click', '#po_delivery_save', function(ev){
					$('#vp_page_loading').show();
					var self = $(this)
					var values = {}
					var mandatory = false;
					var save_action = $(this).attr('action');
					var file_attch = $(this).attr('file_attch');
					$('.new_form_popup input').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name'))
							values[$(this).attr('name')] = $(this).val();
					});
					/** Get attachment details */
					var file_details = po_del_form_widget.dl_attch_file_list;
					if(!mandatory){
						var save_post = {'datas': values,
										'po_id': $(this).attr('po_id'),
										'dl_id': $(this).attr('dl_id'),
										'dl_files': file_details,
										'file_attch': file_attch,
										}
						ajax.jsonRpc(save_action, 'call', save_post).then(function (modal){
							if(parseInt(self.attr('dl_id')) > 0){
								$('#dl_line'+self.attr('dl_id')).replaceWith(modal)
							}else{
								$('#delivery_empty').before(modal)
								var row = $('.po_del_table tbody tr').length - 1;
								$('.new_del_record').each(function(){
									$('.new_del_record').addClass('v_display_none');
								});
								var last_row = $('.po_del_table tbody tr:last').prev();
								var last_td = last_row.find('td:last').removeClass('v_display_none');
								if(row>=1){
			  		    			$('.po_del_table tr#delivery_empty').addClass('v_display_none');
			  		    		}
							}
							$modal.empty();
						    $modal.modal('hide');
						    $('.po_delivery_popup').remove();
							$('#vp_page_loading').hide();
						});
					}else{
						$('#vp_page_loading').hide();
						alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
                		return false;
					}
				});
				$modal.on('click', '#po_delivery_close', function(ev){
					$modal.empty();
				    $modal.modal('hide');
				    $('.po_delivery_popup').remove();
				});
			});
		},

		/**
         * @private
         * click action for file attach
         */
		_clickAttach: function(){
			var self = this;
		 	$(".dl_file_input").click();
		 	// Read upload file
		    $(".dl_file_input").off().on('change', function(){
				var output = document.getElementById('dl_attach_fileList');
      			var children = "";
				_.map($(".dl_file_input")[0].files, function (file) {
						var size = parseFloat(file.size / 1024).toFixed(2)
						if(size <= 5000){
							var reader = new FileReader();
							children +=  '<li id="0" data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
							reader.onload = function (e) {
							self.dl_attch_file_list.push({
								'file_name': file.name,
								'file_content': e.target.result,
								'att_id': 0
							});
							$(".remove-list").off().on('click', function(){
								var file_name = $(this).parent('li').attr('data');
								self.dl_attch_file_list = self.dl_attch_file_list.filter((el) => {
									return el.file_name !== file_name;
								});
							});
				            }			    
				            reader.readAsDataURL(file);
						}else{
							alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
						}
					});
					output.innerHTML += children;
		    });
		},

		/**
         * @private
 		* @param {Object} ev
         * Show Delivery Document
         */
		_showDLDocument: function(ev){
			var $form = $('.po_delivery_form');
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
         * Show Attachment Popup
         */
		_showAttachPopup: function(ev){
			var $form = $('.po_delivery_form');
			var po_del_id = $(ev.currentTarget).attr('po_del_id');
			var action = $(ev.currentTarget).attr('action');
			var post = {'po_del_id': po_del_id}
			ajax.jsonRpc(action, 'call', post).then(function (modal) { 
				var $modal = $(modal);
				$modal.appendTo($form).modal();	
				$modal.on('click', '.multi_attach_close', function(ev){
					$modal.empty();
					$modal.modal('hide');
					$('.multi_attach_view_popup').remove();
				});
			})
		},
		
		/**
         * @private
 		* @param {Object} ev
         * Edit the Payment OR Number
         */
		_editORNumber: function(ev){
			$(ev.currentTarget).addClass('po_pay_dn');
			$(ev.currentTarget).closest('td').find('.or_number').addClass('po_pay_dn');
			$(ev.currentTarget).closest('td').find('.or_number_input').removeClass('po_pay_dn');
			$(ev.currentTarget).closest('td').find('.po_or_number_save').removeClass('po_pay_dn');
		},
		
		/**
         * @private
 		* @param {Object} ev
         * Save the Payment OR Number
         */
		_saveORNumber: function(ev){
			var id = $(ev.currentTarget).attr('id');
			var action = $(ev.currentTarget).attr('action');
			var or_number = $(ev.currentTarget).closest('td').find('.or_number_input').val();
			var post = {'id': id,
						'or_number': or_number}
			ajax.jsonRpc(action, 'call', post).then(function (result){
				$(ev.currentTarget).addClass('po_pay_dn');
				$(ev.currentTarget).closest('td').find('.or_number').text(or_number);
				$(ev.currentTarget).closest('td').find('.or_number').removeClass('po_pay_dn');
				$(ev.currentTarget).closest('td').find('.or_number_input').addClass('po_pay_dn');
				$(ev.currentTarget).closest('td').find('.po_or_number_edit').removeClass('po_pay_dn');
			});
		},
		
		/**
         * @private
         * click action for payment file attach
         */
		_uploadPayAttach: function(ev){
			var id = $(ev.currentTarget).attr('id');
		 	$(ev.currentTarget).closest('td').find(".po_pay_file_input").click();
		 	// Read upload file
		    $(ev.currentTarget).closest('td').find(".po_pay_file_input").off().on('change', function(){
				_.map($(".po_pay_file_input")[0].files, function (file) {
						var size = parseFloat(file.size / 1024).toFixed(2)
						if(size <= 5000){
							var reader = new FileReader();
							reader.onload = function (e) {
								var po_pay_attch_file_list = [];
								po_pay_attch_file_list.push({
									'file_name': file.name,
									'file_content': e.target.result,
									'att_id': 0
								});
								var post = {'po_pay_attch_file_list': po_pay_attch_file_list,
										'id': id}
								ajax.jsonRpc('/upload/payment/attachment', 'call', post).then(function (result){
									
								});
				            }			    
				            reader.readAsDataURL(file);
						}else{
							alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
						}
					});
		    });
		},
		
});

$(document).ready(function () {
	
	var acc = document.getElementsByClassName("accordion_noti");
	var i;

	for (i = 0; i < acc.length; i++) {
	  acc[i].addEventListener("click", function() {
	    this.classList.toggle("po_noti_active");
	    var panel = this.nextElementSibling;
	    if (panel.style.display === "block") {
	        panel.style.display = "none";
			panel.className = "panel_noti"
			$(this).find('i').attr('class', 'fa fa-angle-down po_noti_icon')
	    } else {
	      panel.style.display = "block";
		  panel.className = "panel_noti panel_bt"
		  $(this).find('i').attr('class', 'fa fa-angle-up po_noti_icon');
	    }
	  });
	}
	var url = window.location.href;
	var url_length = url.split('/');
	if((url.indexOf("/my/purchase") > 0) && url_length.length == 5){
		var $form = $('#wrapwrap');
		ajax.jsonRpc('/po/reminder', 'call', {}).then(function (modal) {
			if(modal != 'no_record') {
				var $modal = $(modal);			
	  		    $modal.appendTo($form).modal();	
				$modal.on('click', '.close_reminer_popup', function(ev){
					$modal.empty();
			    	$modal.modal('hide');
			    	$('#reminder_popup_modal').remove();
				});
			}
		});
	}

});

});