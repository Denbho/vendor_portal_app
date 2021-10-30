odoo.define('skit_website_my_invoice.my_invoice', function (require) {
'use strict';

var ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
var time = require('web.time');
var selected_dr_arr = [];
var si_del_form_widget;
var edit_delivery_detail_widget;

publicWidget.registry.websiteSIForm = publicWidget.Widget.extend({
        selector: '.sks_inv_form_outline',
        events: {
				'click .show_si_attach_pdf': '_onViewPdf'
		},
		_onViewPdf: function(ev){
			var $form = $('.sks_inv_form_outline');
			var id = $(ev.currentTarget).attr('att_id');
			var action = $(ev.currentTarget).attr('action');
			var post = {'att_id': id}
			ajax.jsonRpc(action, 'call', post).then(function (modal) { 
				var $modal = $(modal);
				$modal.appendTo($form).modal();	
				$modal.on('click', '.vp_si_pdf_close', function(ev){
					$modal.empty();
					$modal.modal('hide');
					$('.vp_si_file_view_popup').remove();
				});
			})
		},
});

publicWidget.registry.DashboardSendSi = publicWidget.Widget.extend({
    selector: '.send_si_portal, .po_form_details',
    events: {
    	'click .send_si_btn, .po_delivery_send': '_onSendSI',
    },
    start: function () {
    	var self = this;
    	si_del_form_widget = this;
		this.dl_attch_file_list = [];
		this.si_attch_file_list = [];
        return this._super.apply(this, arguments);
    },
    _onSendSI: function (evt) {
    	var $form = $('#wrapwrap');
		var po_id = $(evt.currentTarget).attr('po_id')
		var post = {'po_id': po_id}
		var po_selected_dr_arr = [];
		var linker_dr = [];
		if ($('.po_dr_body_panel').length !== 0){
			 $('.delivery_row').each(function(){
				 var id = $(this).attr('id');
				 if (id != 'delivery_empty'){
					 var dr_selected = $(this).find('.dl_row_check').is(':checked');
					 if(dr_selected){
						var dr_val = $(this).find('.dl_row_check').attr('value');
				    	var dr_no = $(this).find('.dl_row_check').attr('no');
				    	var dr_linked = $(this).find('.dr_linked').text();
				    	// Check DR linked with SI
				    	if(dr_linked.trim() == "is_linked"){
				    		linker_dr.push({'name':dr_no, 'value': dr_val});
				    	}
				    	else{
				    		po_selected_dr_arr.push({'name':dr_no, 'value': dr_val});
				    	}
					 }
				 }
		    		
		    });
		}
		// While select DR and Send SI....if that DR already in SI, need to pop up alert msg.
		if(linker_dr.length >0){
			post['linked_dr'] = linker_dr;
			ajax.jsonRpc('/show/linked_dr_popup', 'call', post).then(function (submodal) {
	    		var $submodal = $(submodal);			
	    		$submodal.appendTo($form).modal();	
	  		    $submodal.on('click', '.close_sdr_warning_popup,.close_sdr_warning', function(ev){
	    			$submodal.empty();
	    			$submodal.modal('hide');
			    	$('#selected_dr_warning_modal').remove();
	    		});
			});
		}
		else{
	    	ajax.jsonRpc('/send_si/popup', 'call', post).then(function (modal) {
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
	              $('#si_date').datetimepicker(datepickers_options);
	              $('#receiving_date').datetimepicker(datepickers_options);
	              $('#dr_date').datetimepicker(datepickers_options);
				$('#si_date').off().on('click', function(){
					$('input[data-target="#si_date"]').each(function(){
						$(this).removeClass('waring')
					})
			    })
				$('#receiving_date').off().on('click', function(){
					$('input[data-target="#receiving_date"]').each(function(){
						$(this).removeClass('waring')
					})
			    })
				$('#dr_date').off().on('click', function(){
					$('input[data-target="#dr_date"]').each(function(){
						$(this).removeClass('waring')
					})
			    })
	              
				/**
				* Set Date Format for popup date fields from Odoo Language settings END --> 
				**/
				if(parseInt(po_id) > 0){
					$(".with_purchase_order").prop('checked', true);
					$(".with_purchase_order").attr('checked', true);
			        $(".child_chkboxes").removeClass('d-none');
			        $(".vendor_po_no_col").removeClass('d-none');
			        $(".without_purchase_order").prop('checked', false);
			        $(".without_purchase_order").attr('checked', false);
			        $(".with_purchase_order,.without_purchase_order").removeClass('required_warning');
			        if (po_selected_dr_arr){
			        	for (var j = 0; j < po_selected_dr_arr.length; j++) {
		  	    	        var ele = document.createElement('div');
		  	    	        ele.className = "dr_list";
		  	    	        ele.textContent = po_selected_dr_arr[j].name;
		  	    	        ele.setAttribute('value', po_selected_dr_arr[j].value)
		  	    	        $modal.find('.dr_numbers').append(ele);
		  	    	    }
			        }
				}
				/** SI attachment arr **/
				si_del_form_widget.si_attch_file_list = [];
				$('#si_attach_fileList li').each(function(){
					si_del_form_widget.si_attch_file_list.push({
							'file_name': $(this).attr('data'),
							'file_content': $(this).attr('file_data'),
							'att_id': $(this).attr('id')
					});
				});
				$(".remove-list").off().on('click', function(){
					var file_name = $(this).parent('li').attr('data');
					si_del_form_widget.si_attch_file_list = si_del_form_widget.si_attch_file_list.filter((el) => {
						return el.file_name !== file_name;
					});
				});

	  		    $modal.on('click', '.close_si_popup', function(ev){
					$modal.empty();
			    	$modal.modal('hide');
			    	$('#sales_invoice_modal').remove();
				});
	  		    $modal.on('change', '.with_purchase_order', function(ev){
					if($('.with_purchase_order').is(":checked")){  
						$(".with_purchase_order").attr('checked', true);
			            $(".child_chkboxes").removeClass('d-none');
			            $(".vendor_po_no_col").removeClass('d-none');
			            $(".service_orderno_col").addClass('d-none');
			            $(".without_purchase_order").prop('checked', false);
			            $(".without_purchase_order").attr('checked', false);
			            $('.si_company_span').text('');
			            $(".with_purchase_order,.without_purchase_order").removeClass('required_warning');
			            if($('.si_company').hasClass('waring')){
			            	$('.si_company').removeClass('waring');
			            }
						$('.dr_number_required').removeClass('d-none');
					}
			        else{
			        	//$(".with_purchase_order").attr('checked', false);
			            $(".child_chkboxes").addClass('d-none');
			            $(".vendor_po_no_col").addClass('d-none');
			        }
				});
	  		    $modal.on('change', '.without_purchase_order', function(ev){
	  		    	if($('.without_purchase_order').is(":checked")){
	  		    		$(".with_purchase_order").attr('checked', false);
	  		    		$(".without_purchase_order").attr('checked', true);
	  		    		$(".with_purchase_order").prop('checked', false);
	  		    		$(".g_service,.child_chkboxes").prop('checked', false);
	  		    		$('.si_company_span').text('*');
	  		    		$('.si_company').val('');
	  		    		$('.si_company').attr('readonly',false);
	  		    		$(".child_chkboxes").addClass('d-none');
	  		    		$(".vendor_po_no_col").addClass('d-none');
	  		    		$(".service_orderno_col").removeClass('d-none');
	  		    		$(".with_purchase_order,.without_purchase_order").removeClass('required_warning');
						$('.dr_number_required').addClass('d-none');
	  		    	}
	  		    });
	  		    $modal.on('change', '.g_service', function(ev){
	  		    	if($('.g_service').is(":checked")){
	  		    		$(".delivery_charge").prop('checked', false);
	  		    		$(".delivery_charge").attr('checked', false);
	  		    		$(".g_service").attr('checked', true);
	  		    		$(".g_service,.delivery_charge").removeClass('required_warning');
	  		    	}
	  		    });
	  		    $modal.on('change', '.delivery_charge', function(ev){
			    	if($('.delivery_charge').is(":checked")){
			    		$(".g_service").prop('checked', false);
			    		$(".g_service").attr('checked', false);
			    		$(".delivery_charge").attr('checked', true);
			    		$(".g_service,.delivery_charge").removeClass('required_warning');
			    		$(".dr_numbers").children().remove();
			    	}
			    });
	  		    $modal.on('click', '.upload_si_invoice', function(ev){
	  		    		$(".si_file_input").click();
					 	// Read upload file
					    $(".si_file_input").off().on('change', function(){
							var output = document.getElementById('si_attach_fileList');
			      			var children = "";
							_.map($(".si_file_input")[0].files, function (file) {
									var size = parseFloat(file.size / 1024).toFixed(2)
									if(size <= 5000){
										var reader = new FileReader();
										children +=  '<li id="0" data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
										reader.onload = function (e) {
											si_del_form_widget.si_attch_file_list.push({
											'file_name': file.name,
											'file_content': e.target.result,
											'att_id': 0
										});
										$(".remove-list").off().on('click', function(){
											var file_name = $(this).parent('li').attr('data');
											si_del_form_widget.si_attch_file_list = si_del_form_widget.si_attch_file_list.filter((el) => {
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
	  		    });
	  		    $modal.on('click', '.send_sales_inv_btn', function(ev){
	  		    	var isProceed = true;	
	  		    	var po_dropdown = $("#vendor_po_no option:selected").val();
	  		    	if($('.with_purchase_order').is(":not(:checked)") && $('.without_purchase_order').is(":not(:checked)")){
	  		    		$(".with_purchase_order,.without_purchase_order").addClass('required_warning');
	  		    		isProceed = false;
	  		    	}
	  		    	if($('.with_purchase_order').is(":checked") && $('.g_service').is(":not(:checked)") && $('.delivery_charge').is(":not(:checked)")){
	  		    		$(".g_service,.delivery_charge").addClass('required_warning');
	  		    		isProceed = false;
	  		    	}
	  		    	if(($('.with_purchase_order').is(":checked") && $('.g_service').is(":checked")) || ($('.with_purchase_order').is(":checked") && $('.delivery_charge').is(":checked"))){
	  		    		if(isNaN(po_dropdown) || po_dropdown <= 0){
	  		    			$('#vendor_po_no').addClass('waring');
							isProceed = false; 
	  		    		}
	  		    		else{
	  		    			$('#vendor_po_no').removeClass('waring');
	  		    		}
	  		    	}
	  		    	if($('.with_purchase_order').is(":checked") && $('.g_service').is(":checked") && po_dropdown && !$('.dr_list').length){
						alertify.alert('Message','Please select DR number.');
	  		    		isProceed = false;
	  		    	}
					if($('.with_purchase_order').is(":checked") && $('.delivery_charge').is(":checked") && po_dropdown && !$('.dr_list').length){
						alertify.alert('Message','Please select DR number.');
	  		    		isProceed = false;
	  		    	}
	  		    	if($('.without_purchase_order').is(":checked") && (!$('.si_company').val())){
	  		    		$('.si_company').addClass('waring');
						isProceed = false;
	  		    	}
	  		    	if($('.si_company').val()){
	  		    		$('.si_company').removeClass('waring');
	  		    	}
	  		    	$('#sales_invoice_form').find('input[required="required"]').each(
	  		    		function(index, element) {
	  		    			var attr = $(this).attr('disabled');										
	  						if (!$(this).val().length > 0) {										
	  							if(!(typeof attr !== typeof undefined && attr !== false)){
	  								$(this).addClass('waring');
	  								isProceed = false;
	  							}else{
	  								$(this).removeClass('waring');
	  							}										
	  						}
	  						else{
	  							$(this).removeClass('waring');
	  						}
	  		    	}).focus(function() {
	  		    			$(this).removeClass('waring');
	  		    	});
	  		    	var post = {};
					var si_amount_val = $('.si_amount').val();
	  		    	post['with_po'] = $('.with_purchase_order').attr('checked');  
	  		    	post['without_po'] = $('.without_purchase_order').attr('checked');
	  		    	post['good_serv'] = $('.g_service').attr('checked');
	  		    	post['delivery_charge'] = $('.delivery_charge').attr('checked');
	  		    	post['si_number'] = $('.si_number').val();
	  		    	post['serv_order_no'] = $('.service_orderno').val();
	  		    	post['si_company'] = $('.si_company').val();
	  		    	post['po_number'] = $("#vendor_po_no option:selected").val();
	  		    	post['vendor_remarks'] = $('.vendor_remarks').val();
	  		    	post['si_amount'] = parseFloat(si_amount_val.replace(/,/g, ''));
	  		    	post['si_date'] = $('.si_date').val();
					if($('.without_purchase_order').is(":checked")){
						post['po_number'] = ""
					}
	  		    	/** Get attachment details */
	  		    	var file_attached = false;
					var file_details = si_del_form_widget.si_attch_file_list;
					if (file_details.length >0){
						file_attached = true;
					}
					post['si_files'] = file_details;
					post['file_attached'] = file_attached;

	  		    	var dr_list = []
	  		    	$('.dr_numbers .dr_list').each(function(){
	  		    		var dr_lst = $(this).attr('value');
	  		    		dr_list.push(parseInt(dr_lst))
	  		    	});
	  		    	post['dr_list'] = dr_list
	  		    	if(isProceed){
		  		    	ajax.jsonRpc('/save/sales_invoice', 'call', post).then(function (sub_modal) {
		  		    		var $submodal = $(sub_modal);			
		  		    		$submodal.appendTo($form).modal();
		  		    		$submodal.on('click', '.close_si_submit_popup,.close_si_submit', function(ev){
		  		    			$submodal.empty();
		  		    			$submodal.modal('hide');
		  				    	$('#si_submit_modal').remove();
		  				    	//close parent popup also
		  				    	$modal.empty();
			  			    	$modal.modal('hide');
			  			    	$('#sales_invoice_modal').remove();
								if(parseInt(po_id) > 0){
									window.location.reload();
								}
		  		    		});
		  		    		$submodal.on('click', '.close_amt_warning_popup,.close_amt_warning', function(ev){
		  		    			$submodal.empty();
		  		    			$submodal.modal('hide');
		  				    	$('#si_submit_modal').remove();
		  		    		});
		  		    	});
	  		    	}
	  		    	else{
		  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
	  		    	}
	  		    	return false;
	  		    });
	  		    $modal.on('click', '#vendor_po_no', function(ev){
	  		    	$(this).removeClass('waring');
	  		    });
	  		    $modal.on('change', '#vendor_po_no', function(ev){
	  		    	$(".dr_numbers").children().remove();
	  		    	var post_val = {};
	  		    	post_val['po'] = $("#vendor_po_no option:selected").val();
	  		    	ajax.jsonRpc('/get/po_company', 'call', post_val).then(function (data) {
	  		    		if(data){
	  		    			$('.si_company').val(data);
	  		    			$('.si_company').attr('readonly',true);
	  		    		}
	  		    		else{
	  		    			$('.si_company').val('');
	  		    			$('.si_company').attr('readonly',false);
	  		    		}
	  		    	});
			    });
	  		    $modal.on('click', '.add_dr_no', function(ev){
	  		    	var post_data = {};
	  		    	var selected_po = $("#vendor_po_no option:selected").val();
	  		    	var with_po = $(".with_purchase_order").is(':checked');
	  		    	var without_po = $(".without_purchase_order").is(':checked');
	  		    	var proceed_dr = true;
	  		    	post_data['selected_po'] = selected_po;
	  		    	post_data['with_po'] = with_po;
	  		    	post_data['without_po'] = without_po;
	  		    	// When with_po checked - check PO to select
	  		    	if (selected_po == "" && with_po){
	  		    		proceed_dr = false;
	  		    	}
	  		    	var exist_drs = []
  			    	$('.dr_numbers .dr_list').each(function(){
	  		    		var dr_items = $(this).attr('value');
	  		    		exist_drs.push(parseInt(dr_items))
	  		    	});
	  		    	post_data['added_drs'] = exist_drs;
	  		    	if(proceed_dr){
			  		    ajax.jsonRpc('/show/dr_number_popup', 'call', post_data).then(function (dr_modal) {
			  		    		var $drmodal = $(dr_modal);
			  		  		    $drmodal.appendTo($form).modal();	
			  		  		    $drmodal.on('click', '.close_dr_no_popup', function(ev){
			  		  		    	$drmodal.empty();
			  		  		    	$drmodal.modal('hide');
				  			    	$('#dr_number_modal').remove();
				  				});
			  		  		    $drmodal.on('click', '.dr_no_span', function(ev){
			  		  		    	if($(this).hasClass("selected_dr")){
			  		  		    		$(ev.currentTarget).parent('div').css('background','#ffffff');
			  		  		    		$(ev.currentTarget).removeClass('selected_dr');
			  		  		    	}
			  		  		    	else{
			  		  		    		$(ev.currentTarget).parent('div').css('background','#e8f4f8');
			  		  		    		$(ev.currentTarget).addClass('selected_dr');
			  		  		    	}
			  		  		    });
								$drmodal.on('click', '.dr_no_plus', function(ev){
									$(ev.currentTarget).parent('div').find('.dr_no_span').trigger('click')
								});
			  		  		    $drmodal.on('click', '.dr_no_confirm', function(ev){
			  		  		    	selected_dr_arr = [];
					  		    	$('.dr_no_panel').each(function(){
					  		    		var dr_val = $(this).find('.selected_dr').attr('value');
					  		    		if(dr_val){
					  		    			selected_dr_arr.push({'name':$(this).find('.selected_dr').attr('no'), 'value': dr_val});
					  		    		}
					  		    	});
					  		    	$drmodal.empty();
			  		  		    	$drmodal.modal('hide');
				  			    	$('#dr_number_modal').remove();
					  	    		for (var i = 0; i < selected_dr_arr.length; i++) {
					  	    	        var ele = document.createElement('div');
					  	    	        ele.className = "dr_list";
					  	    	        ele.textContent = selected_dr_arr[i].name;
					  	    	        ele.setAttribute('value', selected_dr_arr[i].value)
										ele.innerHTML = selected_dr_arr[i].name+'<i class="fa fa-trash-o po_dr_delete" ></i>';
					  	    	        $modal.find('.dr_numbers').append(ele);
					  	    	    }
									
					  		    });
								$modal.on('click', '.po_dr_delete', function(ev){
									$(this).parent('div').remove()
								})
			  		  		    // DR popup Click here action
			  		  		    $drmodal.on('click', '.delivery_info_create', function(ev){
			  		  		    	var post = {}
			  		  		    	var po_id = $('.delivery_info_create').attr('po_id');
			  		  		    	post['datas'] = {};
			  		  		    	post['po_id']= po_id;
			  		  		    	post['id']= '0';
				  		  		    ajax.jsonRpc('/create/po_delivery', 'call', post).then(function (pod_modal) { 
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
						              $('#si_date').datetimepicker(datepickers_options);
						              $('#receiving_date').datetimepicker(datepickers_options);
						              $('#dr_date').datetimepicker(datepickers_options);
										$('#si_date').off().on('click', function(){
											$('input[data-target="#si_date"]').each(function(){
												$(this).removeClass('required_style')
											})
									    })
										$('#receiving_date').off().on('click', function(){
											$('input[data-target="#receiving_date"]').each(function(){
												$(this).removeClass('required_style')
											})
									    })
										$('#dr_date').off().on('click', function(){
											$('input[data-target="#dr_date"]').each(function(){
												$(this).removeClass('required_style')
											})
									    })
						              
									/**
									* Set Date Format for popup date fields from Odoo Language settings END --> 
									**/
				  						si_del_form_widget.dl_attch_file_list = [];
				  						$('#dl_attach_fileList li').each(function(){
				  							si_del_form_widget.dl_attch_file_list.push({
				  									'file_name': $(this).attr('data'),
				  									'file_content': $(this).attr('file_data'),
				  									'att_id': $(this).attr('id')
				  							});
				  						});
				  						$(".remove-list").off().on('click', function(){
				  							var file_name = $(this).parent('li').attr('data');
				  							si_del_form_widget.dl_attch_file_list = si_del_form_widget.dl_attch_file_list.filter((el) => {
				  								return el.file_name !== file_name;
				  							});
				  						});
				  						$pod_modal.on('click', '#po_delivery_save', function(ev){
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
				  							var file_details = si_del_form_widget.dl_attch_file_list;
				  							if(!mandatory){
				  								var save_post = {'datas': values,
				  												'po_id': $(this).attr('po_id'),
				  												'dl_id': $(this).attr('dl_id'),
				  												'dl_files': file_details,
				  												'file_attch': file_attch,
				  												}
				  								ajax.jsonRpc(save_action, 'call', save_post).then(function (modal){
													$pod_modal.empty();
				  								    $pod_modal.modal('hide');
				  								    $('.po_delivery_popup').remove();
				  								    //
					  								$drmodal.empty();
					  		  		  		    	$drmodal.modal('hide');
					  			  			    	$('#dr_number_popup').remove();
					  			  			    	// Trigger
					  			  			    	$modal.find('.add_dr_no').click();
													$('#vp_page_loading').hide();
				  								});
				  								
				  							}else{
												$('#vp_page_loading').hide();
												alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
                								return false;
											}
				  						});
				  						$pod_modal.on('click', '#po_delivery_close', function(ev){
				  							$pod_modal.empty();
		  								    $pod_modal.modal('hide');
				  						    $('.po_delivery_popup').remove();
				  						});
				  						// Attachment click action
				  						$pod_modal.on('click', '.dl_file_upload', function(ev){
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
					  											si_del_form_widget.dl_attch_file_list.push({
					  											'file_name': file.name,
					  											'file_content': e.target.result,
					  											'att_id': 0
					  										});
					  										$(".remove-list").off().on('click', function(){
					  											var file_name = $(this).parent('li').attr('data');
					  											si_del_form_widget.dl_attch_file_list = si_del_form_widget.dl_attch_file_list.filter((el) => {
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
				  						});
				  					});
			  		  		    });
			  		    });
	  		    	}
	  		    	else{
	  		    		$("#vendor_po_no").addClass('waring');
	  		    	}
	  		    });
	    	});
	    }
    },

});

publicWidget.registry.SiDrDetails = publicWidget.Widget.extend({
    selector: '.si_delivery_receipt_sec',
    events: {
    	'click .my_invf_pr_dr_acc_arrow': '_onEditDRDetails',
    },
    start: function () {
    	var self = this;
    	edit_delivery_detail_widget = this;
		this.edit_dl_attch_file_list = [];
        return this._super.apply(this, arguments);
    },
    _onEditDRDetails: function (evt) {
    	var post = {}
    	var $form = $('#wrapwrap');
	    var po_id = $('.dr_po_id').attr('dr_po_id');
	    post['datas'] = {};
	    post['po_id']= po_id;
	    post['id']= $(evt.currentTarget).attr('dr_id');
	    ajax.jsonRpc('/create/po_delivery', 'call', post).then(function (pod_modal) { 
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
			$('#receiving_date').datetimepicker(datepickers_options);
			$('#dr_date').datetimepicker(datepickers_options);
			
			$('#receiving_date').off().on('click', function(){
				$('input[data-target="#receiving_date"]').each(function(){
					$(this).removeClass('required_style')
				})
			})
			$('#dr_date').off().on('click', function(){
				$('input[data-target="#dr_date"]').each(function(){
					$(this).removeClass('required_style')
				})
			})
			/**
			* Set Date Format for popup date fields from Odoo Language settings END --> 
			**/
			edit_delivery_detail_widget.edit_dl_attch_file_list = [];
			$('#dl_attach_fileList li').each(function(){
				edit_delivery_detail_widget.edit_dl_attch_file_list.push({
						'file_name': $(this).attr('data'),
						'file_content': $(this).attr('file_data'),
						'att_id': $(this).attr('id')
				});
			});
			$(".remove-list").off().on('click', function(){
				var file_name = $(this).parent('li').attr('data');
				edit_delivery_detail_widget.edit_dl_attch_file_list = edit_delivery_detail_widget.edit_dl_attch_file_list.filter((el) => {
					return el.file_name !== file_name;
				});
			});
			$pod_modal.on('click', '#po_delivery_save', function(ev){
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
				var file_details = edit_delivery_detail_widget.edit_dl_attch_file_list;
				if(!mandatory){
					var save_post = {'datas': values,
									'po_id': $(this).attr('po_id'),
									'dl_id': $(this).attr('dl_id'),
									'dl_files': file_details,
									'file_attch': file_attch,
									}
					ajax.jsonRpc(save_action, 'call', save_post).then(function (modal){
						$pod_modal.empty();
					    $pod_modal.modal('hide');
					    $('.po_delivery_popup').remove();
					    location.reload();
						$('#vp_page_loading').hide();
					});
					
				}else{
					$('#vp_page_loading').hide();
					alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
                	return false;
				}
			});
			$pod_modal.on('click', '#po_delivery_close', function(ev){
				$pod_modal.empty();
			    $pod_modal.modal('hide');
			    $('.po_delivery_popup').remove();
			});
			// Attachment click action
			$pod_modal.on('click', '.dl_file_upload', function(ev){
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
									edit_delivery_detail_widget.edit_dl_attch_file_list.push({
									'file_name': file.name,
									'file_content': e.target.result,
									'att_id': 0
								});
								$(".remove-list").off().on('click', function(){
									var file_name = $(this).parent('li').attr('data');
									edit_delivery_detail_widget.edit_dl_attch_file_list = edit_delivery_detail_widget.edit_dl_attch_file_list.filter((el) => {
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
				});
		});
    },
    
});
    
});