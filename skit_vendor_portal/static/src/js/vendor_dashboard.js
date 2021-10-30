odoo.define('website.vendor.dashboard', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var session = require('web.session');
var core = require('web.core');
var QWeb = core.qweb;
var ajax = require('web.ajax');

publicWidget.registry.VendorDashboard = publicWidget.Widget.extend({
    selector: '.rfq_order_portal',
    events: {
		'click #save_rfq_draft': '_onSaveRfqDraft',
        'click .submit_quote': '_onSubmitQuote',
        'input .unit_price_cls': '_onChangeUnitPrice', 
        'input .delivery_cost_cls': '_onChangeDeliveryCost', 
      	'click .accept_rfq_mail': '_onAccept',
      	'click .decline_rfq_mail': '_onDecline',
      	'keypress input.decimal_field': '_ValidateNumberAndDecimalField',
		'click .vp_rfq_paperclip': '_rfqAttach',
		'click .show_vp_rfq_attach_pdf': 'viewRFQPdf',
		'click .remove-list': '_removeAttach',
    },
    
    start: function () {
		var self = this;
		this.dl_attch_file_list = []
		$('#vp_rfq_attach_fileList li').each(function(){
			self.dl_attch_file_list.push({
				'file_name': $(this).attr('data'),
				'file_content': $(this).attr('file_data'),
				'att_id': $(this).attr('id')
			});
		});
        return this._super();
    },

	/**
     * @private
     * click action for file attach
     */
	_clickAttach: function(){
		$(".dl_file_input").click();
	},
	/**
     * @private
     * @param {Object} ev
     * Attach File
     */
	_uploadFile: function(ev){
		var self = this;
		self.readFileURL(ev.target);
	},
	viewRFQPdf: function(ev){
		var attachment_id = $(ev.currentTarget).attr('att_id');
		var action = $(ev.currentTarget).attr('action');
		var post = {};
		post['attachment_id'] = attachment_id
		var $form = $('.po_form_details');
		ajax.jsonRpc(action, 'call', post).then(function (modal) { 
			var $modal = $(modal);			
			$modal.appendTo($form).modal();	
			$modal.on('click', '#ps_photo_close', function(ev){
				$modal.empty();
				$modal.modal('hide');
				$('.product_file_view_popup').remove();
			});
		});
	},
	_removeAttach: function(ev){
		var self = this
		var attach_id = $(ev.currentTarget).attr('id');
		var post = {'id': attach_id}
		var file_name = $(ev.currentTarget).parent('li').attr('data');
		self.dl_attch_file_list = self.dl_attch_file_list.filter((el) => {
			return el.file_name !== file_name;
		});
		$(ev.currentTarget).parent('li').remove()
		ajax.jsonRpc('/delete/accreditation/attachment', 'call', post).then(function (result){
			if((self.dl_attch_file_list).length	== 0){
				$('.pro_attach_p').removeClass('d-none');
				$('.vp_rfq_attachments').removeClass('vp_rfq_mt2')
			}				
		});
	},
	_rfqAttach: function(ev){
		var self = this;
		$(".vp_rfq_file_input").click();
		$(".vp_rfq_file_input").off().on('change', function(){
			var id = $(this).attr('rfq_id')
			var output = document.getElementById('vp_rfq_attach_fileList');
      		var children = "";
			_.map($(".vp_rfq_file_input")[0].files, function (file) {
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
							var post = {'dl_attch_file_list': self.dl_attch_file_list,
										'id': id,
										'modal_name': 'admin.vendor.rfq'}
								$('.pro_attach_p').addClass('d-none');
								ajax.jsonRpc('/upload/accreditation/attachment', 'call', post).then(function (result){
									window.location.reload();
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
     * delete attached file
     */
	_deleteAttach: function(){
		$('.attach_delete').addClass('d-none');
        $('.pro_attach_p').removeClass('d-none');
        $('.dl_file').removeAttr("file_data");
        $('.dl_file').text('');
		$('#po_delivery_save').attr('file_attch', true)
	},

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

    _onDecline: function (evt) {
    	var post = {};
    	var $form = $('.rfq_decline_panel');
    	var rfq_id = $(evt.currentTarget).attr('rfq_id');
		ajax.jsonRpc('/rfq/decline_popup', 'call', post).then(function (modal) {
			var $modal = $(modal);			
			$modal.appendTo($form).modal();	
			$modal.on('click', '#decline_confirm', function(ev){
				$('#vp_page_loading').show();
				var po_status =  $("#po_status").text();
				var declined_note =  $("#declined_note").val();
				var declined_reason_id = $("#declined_reason_id option:selected").val();
				post['rfq_mail_id'] = rfq_id;
				post['po_status'] = po_status;
				post['declined_note'] = declined_note;
				post['reason_id'] = declined_reason_id;
				if(declined_note && declined_reason_id){
  		    		ajax.jsonRpc('/update/rfq/declined_status', 'call', post).then(function (modal) { 
						$('#vp_page_loading').hide();
  		    			alertify.alert('Confimation','RFQ Declined.');
  		    			window.location.reload();
	  		    	});
  		    	}
  		    	else{
					$('#vp_page_loading').hide();
	  				alertify.alert('Message','Please enter remarks reason.'); 
 				    return false;
  		    	}
			});
			$modal.on('click', '#decline_cancel', function(ev){
				$modal.empty();
		    	$modal.modal('hide');
		    	$('.rfq_decline_popup').remove();
			});
		});
    },
    
    _onAccept: function (evt) {
    	var self = this;
    	var id = $(evt.currentTarget).attr('id');
		var post = {'rfq_mail_id': id}
    	this._rpc({
            route: '/rfq_mail/accept_state/',
            params: {post},
        }).then(function (data) {
			window.location.reload();
        });
    },
    
    _onChangeUnitPrice: function (evt) {
    	this.computeGrossPrice(evt);
    },

    _onChangeDeliveryCost: function (evt) {
    	this.computeGrossPrice(evt);
    },

	computeGrossPrice: function (evt) {
		var price = $(evt.currentTarget).closest('form').find('.unit_price_cls').val();
	   	var delivery_cost = $(evt.currentTarget).closest('form').find('.delivery_cost_cls').val();
	    var prod_qty = $(evt.currentTarget).closest('form').find('.prod_qty').text();
	    var grossPrice = price * prod_qty;
	    var grossTotal = parseFloat(grossPrice);
	    if(delivery_cost){
	    	grossTotal = grossTotal + parseFloat(delivery_cost)
	  	}
		grossTotal = grossTotal.toFixed(2)
	    $(evt.currentTarget).closest('form').find('#gross_total').val(grossTotal);
   },
   
	getRfqValues: function (evt) {
   		var post_all_vals = {}
		var post_rfq_mail_lines = {}
  		$('#myRrqTable tbody tr').each(function(){
  		 	var rfq_line_id = $(this).attr('id');
		   	var post_rfq_mail_line = {}
		   	var currency_symbol = $(this).attr('currency_symbol');
		    $(this).find('td').each(function(){
		       	var $td = $(this).text().trim();
		    	var td_index = $(this).index();
		    	var index = td_index + 1
		      	var $th = $('#myRrqTable tr').find('th:nth-child(' + index + ')').attr('name');
		      	if($th != undefined){
			      	if( $(this).hasClass("price")){//.match("/"+currency_symbol+"/g")){
				      	$td = $td.replace(currency_symbol, '')
				      	$td = parseFloat($td.replace(/,/g, ''))
				      }
		      		post_rfq_mail_line[$th] = $td;
		      	}
		    })
		    post_rfq_mail_lines[rfq_line_id] = post_rfq_mail_line;
		    post_all_vals['rfq_mail_line_vals'] = post_rfq_mail_lines
		})
   		return post_all_vals;
	},
   
	_onSaveRfqDraft: function (evt) {
    	var RfqValues = this.getRfqValues(evt);
    	var post_rfq_mail_vals = {}
     	var other_info = $('textarea').val();
		post_rfq_mail_vals['other_info'] = other_info;
		post_rfq_mail_vals['state'] = 'accepted';
    	RfqValues['rfq_mail_vals'] = post_rfq_mail_vals
    	this._rpc({
            route: '/save/rfq_mail',
            params: {RfqValues},
        }).then(function (data) {
            window.location.reload();
        });
    },
   
   	_onSubmitQuote: function (evt) {
		var RfqValues = this.getRfqValues(evt);
    	var post_rfq_mail_vals = {}
     	var other_info = $('textarea').val();
		post_rfq_mail_vals['other_info'] = other_info;
		post_rfq_mail_vals['state'] = 'submitted';
    	RfqValues['rfq_mail_vals'] = post_rfq_mail_vals
		this._rpc({
            route: '/save/rfq_mail',
            params: {RfqValues},
        }).then(function (data) {
            window.location.reload();
        });
     },
 
 	 _ValidateNumberAndDecimalField: function (e) {
    	var code = (e.which) ? e.which : e.keyCode;
	    if (code > 31 && ((code != 46 && code < 48) || code > 57)) {
	        e.preventDefault();
	    }    	
	},
});

publicWidget.registry.DashboardAccreditation = publicWidget.Widget.extend({
    selector: '.accreditation_portal',
    events: {
    	'change .rqmt_checkbox': '_onRqmtCheckbox',
    	'click .requirement_submit': '_onSaveRequirement',
		'click .remove-list': '_removeAttach',
		'click .accre_file_view': '_on_click_file_view'
    },
    start: function () {
		var self = this;
		this.dl_attch_file_list = []
		$('#dl_attach_fileList li').each(function(){
			self.dl_attch_file_list.push({
				'file_name': $(this).attr('data'),
				'file_content': $(this).attr('file_data'),
				'att_id': $(this).attr('id')
			});
		});
        return this._super();
    },
    _onRqmtCheckbox: function(ev){
        if($(ev.currentTarget).prop('checked')) {
        	$(ev.currentTarget).prop('checked', true)
        	$(ev.currentTarget).attr('checked', true);
    	}else {
    		$(ev.currentTarget).prop('checked', false)
    		$(ev.currentTarget).attr('checked', false);
    	}
    },
    _onSaveRequirement: function (evt) {
    	var accr_doc_ids = []
		var acc_id = $(evt.currentTarget).attr('acc_id')
		$('.accred_req_doc:checked').each(function(){
			accr_doc_ids.push(parseInt($(this).attr('id')))
		})
		var acc_post = {'acc_id': acc_id,
						'accr_doc_ids': accr_doc_ids
						}
		ajax.jsonRpc('/save/accredit/requirement', 'call', acc_post).then(function (result){
			
		});
		var self = this;
		 	$(".dl_file_input").click();
		 	// Read upload file
		    $(".dl_file_input").off().on('change', function(){
				var id = $(this).attr('acc_id')
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
								var post = {'dl_attch_file_list': self.dl_attch_file_list,
										'id': id,
										'modal_name': 'partner.evaluation'}
								$('.pro_attach_p').addClass('d-none');
								ajax.jsonRpc('/upload/accreditation/attachment', 'call', post).then(function (result){
									window.location.reload();
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
	_removeAttach: function(ev){
		var self = this
		var attach_id = $(ev.currentTarget).attr('id');
		var post = {'id': attach_id}
		var file_name = $(ev.currentTarget).parent('li').attr('data');
		self.dl_attch_file_list = self.dl_attch_file_list.filter((el) => {
			return el.file_name !== file_name;
		});
		$(ev.currentTarget).parent('li').remove()
		ajax.jsonRpc('/delete/accreditation/attachment', 'call', post).then(function (result){
			if((self.dl_attch_file_list).length	== 0){
				$('.pro_attach_p').removeClass('d-none');
			}				
		});
	},
	_on_click_file_view: function(ev){
		var data = $(ev.currentTarget).parent('li').attr('file_data');
		var attachment_id = $(ev.currentTarget).parent('li').attr('id');
		if(data && attachment_id){
			var post = {};
			post['src'] = data
			post['attachment_id'] = attachment_id

			var $form = $('.accreditation_portal');

			ajax.jsonRpc('/show_product/attachment', 'call', post).then(function (modal) { 
				var $modal = $(modal);			
				$modal.appendTo($form).modal();	
				$modal.on('click', '#ps_photo_close', function(ev){
					$modal.empty();
					$modal.modal('hide');
					$('.product_file_view_popup').remove();
				});
			});
		}
		else{
			alertify.alert('Message','No file found.'); 
			return false;
		}
		
	 },

});

publicWidget.registry.RFIOrder = publicWidget.Widget.extend({
	selector: '.rfi_decline_panel',
    events: {
        'click #rfi_decline': '_onDecline',
        'click #rfi_accept': '_onAccept',
    },
    start: function () {
        return this._super();
    },
    _onDecline: function (evt) {
    	var post = {};
    	var $form = $('.rfi_decline_panel');
    	var rfi_id = $(evt.currentTarget).attr('rfiid');
		ajax.jsonRpc('/rfi/decline_popup', 'call', post).then(function (modal) {
			var $modal = $(modal);			
			$modal.appendTo($form).modal();	
			//update status
			$modal.on('click', '#decline_confirm', function(ev){
				var po_status =  $("#po_status").text();
				var declined_note =  $("#declined_note").val();
				var declined_reason_id = $("#declined_reason_id option:selected").val();
				post['rfi_id'] = rfi_id;
				post['po_status'] = po_status;
				post['declined_note'] = declined_note;
				post['reason_id'] = declined_reason_id;
				if(declined_note && declined_reason_id){
  		    		ajax.jsonRpc('/update/rfi/declined_status', 'call', post).then(function (modal) { 
  		    			alertify.alert('Confimation','RFI Declined.');
  		    			$('.rfi_status_head').text('Declined');
  		    			$('.rfi_status_head').attr('class','rfi_status_head rfi_declined');
  		    			$('.rfi_decline_panel').css({'display':'none'})
	  		    	});
  		    		$modal.empty();
			    	$modal.modal('hide');
					$('.rfi_decline_popup').remove();
  		    	}
  		    	else{
	  				alertify.alert('Message','Please enter remarks reason.'); 
 				     return false;
  		    	}
			});
			$modal.on('click', '#decline_cancel', function(ev){
				$modal.empty();
		    	$modal.modal('hide');
		    	$('.rfi_decline_popup').remove();
			});
		});
    },
    
     _onAccept: function (evt) {
     	var post = {};
    	var rfi_id = $(evt.currentTarget).attr('rfiid');
    	post['rfi_id'] = rfi_id;
		ajax.jsonRpc('/update/rfi/accept_status', 'call', post).then(function (modal) {
			alertify.alert('Confimation','RFI Accepted.'); 
			$('.rfi_status_head').text('Accepted');
  			$('.rfi_status_head').attr('class','rfi_status_head rfi_accepted');
			$('.rfi_decline_panel').css({'display':'none'})
		});
     },
});

publicWidget.registry.RFPOrder = publicWidget.Widget.extend({
	selector: '.rfp_order_portal',
    events: {
        'click .decline_rfp_mail': '_onDecline',
        'click .accept_rfp_mail': '_onAccept',
        'click #save_rfp_draft': '_onSaveRfpDraft',
        'click .submit_proposal': '_onSubmitProposal',
		'click .rfp_add_note': '_addNote',
		'click .rfp_add_section': '_addSection',
		'click .rfp_add_product': '_addProduct',
		'click .rfp_del_section, .rfp_del_note, .rfp_del_product': '_deleteNewRow',
		'click input': 'removeRequired',
		'input .unitprice, .qty': '_updateGrossPrice'
        
    },
    start: function () {
        return this._super();
    },

	removeRequired(ev){
		$(ev.currentTarget).removeClass('required_style');
	},
	
	_addSection: function(ev){
		var rfp_id = $(ev.currentTarget).attr('rfp_id');
		var row_html = '<tr class="rfp_new_record" display_type="line_section" rfp_id='+rfp_id+'> <td colspan="6" ><input class="line_section form-control" name="name" type="text" required="required" /></td><td><div class="rfp_del_section"><i class="fa fa-trash span_icon" /></div></td></tr>'
		if($('.vendor_rfp_table tbody tr').length > 0){
			$('.vendor_rfp_table tbody tr:last').after(row_html);
		}else{
			$('.vendor_rfp_table tbody').append(row_html);
		}
	},
	
	_addNote: function(ev){
		var rfp_id = $(ev.currentTarget).attr('rfp_id');
		var row_html = '<tr class="rfp_new_record" display_type="line_note" rfp_id='+rfp_id+'> <td colspan="6" ><input class="line_note form-control" name="name" type="text" required="required" /></td><td><div class="rfp_del_note"><i class="fa fa-trash span_icon" /></div></td></tr>'
		if($('.vendor_rfp_table tbody tr').length > 0){
			$('.vendor_rfp_table tbody tr:last').after(row_html);
		}else{
			$('.vendor_rfp_table tbody').append(row_html);
		}
	},
	
	_addProduct: function(ev){
		var rfp_id = $(ev.currentTarget).attr('rfp_id');
		var row_html = '<tr class="rfp_new_record" display_type="" rfp_id='+rfp_id+'>'
			row_html += '<td><input type="text" class="form-control" name="product_name" required="required"/> </td>';
			row_html += '<td><input type="text" class="form-control" name="name" required="required"/> </td>';
			row_html += '<td><input type="text" class="form-control" name="unit_name" required="required"/> </td>';
			row_html += '<td class="text-right"><input type="number" class="form-control qty" name="qty" required="required" /> </td>';
			row_html += '<td class="text-right"><input type="number" class="form-control unitprice" name="price" required="required"/> </td>'
			row_html += '<td class="grossprice text-right"></td>'
			row_html += '<td><div class="rfp_del_product"><i class="fa fa-trash span_icon" /></div></td>'
			row_html += '</tr>'
		if($('.vendor_rfp_table tbody tr').length > 0){
			$('.vendor_rfp_table tbody tr:last').after(row_html);
		}else{
			$('.vendor_rfp_table tbody').append(row_html);
		}
	},
	
	_updateGrossPrice: function(ev){
		
		var qty = $(ev.currentTarget).closest('tr').find('.qty').val();
		var unit_price = $(ev.currentTarget).closest('tr').find('.unitprice').val();
		if(qty != undefined && unit_price != undefined && qty != '' && unit_price != '' && qty != null && unit_price != null){
			var total = parseFloat(qty) * parseFloat(unit_price)
			total = total.toFixed(2)
			$(ev.currentTarget).closest('tr').find('.grossprice').text(total);
		}else{
			$(ev.currentTarget).closest('tr').find('.grossprice').text('');
		}
		var grand_total = 0;
		$('#myrfp_tables tr.rfp_exist_record').each(function(ev){
			var g_total = $(this).find('.grossprice').text();
			if(g_total != undefined && g_total != null && g_total != ''){
				grand_total = parseFloat(grand_total) + parseFloat(g_total.replace(/,/g, ''))
				grand_total = (grand_total).toFixed(2)
			}
				
		});
		$('#myrfp_tables tr.rfp_new_record').each(function(ev){
			var g_total = $(this).find('.grossprice').text();
			if(g_total != undefined && g_total != null && g_total != ''){
				grand_total = parseFloat(grand_total) + parseFloat(g_total.replace(/,/g, ''))
				grand_total = (grand_total).toFixed(2)
			}
				
		});
        $('#view_rfp_mail_line_form').find('.total').html(grand_total);
	},
	
	_deleteNewRow: function(ev){
		var tr = $(ev.currentTarget).closest('tr');
	  	tr.remove();
	  	var grand_total = 0;
		$('#myrfp_tables tr.rfp_exist_record').each(function(ev){
			var g_total = $(this).find('.grossprice').text();
			if(g_total != undefined && g_total != null && g_total != ''){
				grand_total = parseFloat(grand_total) + parseFloat(g_total.replace(/,/g, ''))
				grand_total = (grand_total).toFixed(2)
			}
				
		});
		$('#myrfp_tables tr.rfp_new_record').each(function(ev){
			var g_total = $(this).find('.grossprice').text();
			if(g_total != undefined && g_total != null && g_total != ''){
				grand_total = parseFloat(grand_total) + parseFloat(g_total.replace(/,/g, ''))
				grand_total = (grand_total).toFixed(2)
			}
				
		});
        $('#view_rfp_mail_line_form').find('.total').html(grand_total);
	},

     _onDecline: function (evt) {
    	var post = {};
    	var $form = $('.rfp_decline_panel');
    	var rfp_id = $(evt.currentTarget).attr('rfp_id');
		ajax.jsonRpc('/rfp/decline_popup', 'call', post).then(function (modal) {
			var $modal = $(modal);			
			$modal.appendTo($form).modal();	
			//update status
			$modal.on('click', '#decline_confirm', function(ev){
				var po_status =  $("#po_status").text();
				var declined_note =  $("#declined_note").val();
				var declined_reason_id = $("#declined_reason_id option:selected").val();
				post['rfp_mail_id'] = rfp_id;
				post['po_status'] = po_status;
				post['declined_note'] = declined_note;
				post['reason_id'] = declined_reason_id;
				if(declined_note && declined_reason_id){
  		    		ajax.jsonRpc('/update/rfp/declined_status', 'call', post).then(function (modal) { 
  		    			alertify.alert('Confimation','RFP Declined.');
  		    			window.location.reload();
	  		    	});
  		    	}
  		    	else{
	  				alertify.alert('Message','Please enter remarks reason.'); 
 				     return false;
  		    	}
			});
			$modal.on('click', '#decline_cancel', function(ev){
				$modal.empty();
		    	$modal.modal('hide');
		    	$('.rfp_decline_popup').remove();
			});
		});
    },
    _onAccept: function (evt) {
    	var self = this;
    	var id = $(evt.currentTarget).attr('id');
			var post = {'rfp_mail_id': id}
    	//post_all['state'] = 'accepted';
    	this._rpc({
            route: '/rfp_mail/accept_state/',
            params: {post},
        }).then(function (data) {
			window.location.reload();
           
        });
    	
    },
    _onSaveRfpDraft: function (evt) {
		var mandatory = false;
		var new_rfp_line = [];
     	var post_all = {}
		var new_rfp_id = 0;
		var rfp_other_info = $('.rfp_other_info').text();
		var rfp_id = $('.save_rfp_draft').attr('rfp_id');
  		$('#myrfp_tables tbody tr.rfp_exist_record').each(function(test){
  		 	var rfp_line_id = $(this).attr('id');
		   	var post = {}
		    $(this).find('td').each(function(){
		    	var $td = $(this).text().trim();
		    	var td_index = $(this).index();
		    	var index = td_index + 1

		      	var $th = $('#myrfp_tables tr').find('th:nth-child(' + index + ')').attr('name');
		      	if($th != undefined){
		      		if($(this).hasClass("price")){
				      	$td = parseFloat($td.replace(/,/g, ''))
				      }
		      		post[$th] = $td;
		      	}
		    })
		    post_all[rfp_line_id]= post;
		})
		
		$('#myrfp_tables tbody tr.rfp_new_record').each(function(ev){
			new_rfp_id = $(this).attr('rfp_id');
			var values = {}
			if($(this).attr('display_type') != '')
				values['display_type'] = $(this).attr('display_type')
			$(this).find('input').each(function(){
				if($(this).attr('required') && !$(this).val()){
					mandatory = true;
					$(this).addClass('required_style')
				}
				if($(this).attr('name')){
					if($(this).attr('name') == 'qty' || $(this).attr('name') == 'price'){
						values[$(this).attr('name')] = parseFloat($(this).val());
					}else{
						values[$(this).attr('name')] = $(this).val();
					}
				}
			});
			new_rfp_line.push(values)
		});
		
		if(!mandatory){
			var rfp_post = {}
			rfp_post['post_all'] = post_all;
			rfp_post['new_rfp_line'] = new_rfp_line;
			rfp_post['new_rfp_id'] = new_rfp_id;
			rfp_post['other_info'] = rfp_other_info;
			rfp_post['rfp_id'] = rfp_id;
			this._rpc({
	            route: '/rfp_mail_line/save/',
	            params: rfp_post,
	        }).then(function (data) {
	            window.location.reload();
	        });
		}else{
			alertify.alert('Message','Please make sure to fill out all mandatory fields.');
		}
     },
     _onSubmitProposal: function (evt) {
     
     	document.getElementsByClassName('rfp_edit_view').readOnly = true;
     	var mandatory = false;
		var new_rfp_line = [];
     	var post_all = {}
		var new_rfp_id = 0
		var rfp_id = $('.submit_proposal').attr('rfp_id');
		var rfp_other_info = $('.rfp_other_info').text();
  		$('#myrfp_tables tbody tr.rfp_exist_record').each(function(test){
  		 	var rfp_line_id = $(this).attr('id');
		   	var post = {}
		    $(this).find('td').each(function(){
		    	var $td = $(this).text().trim();
		    	var td_index = $(this).index();
		    	var index = td_index + 1
		      	var $th = $('#myrfp_tables tr').find('th:nth-child(' + index + ')').attr('name');
		      	if($th != undefined){
		      		if($(this).hasClass("price")){
				      	$td = parseFloat($td.replace(/,/g, ''))
				      }
		      		post[$th] = $td;
		      	}
		    })
		    post_all[rfp_line_id]= post;
		})
		
		$('#myrfp_tables tbody tr.rfp_new_record').each(function(ev){
			new_rfp_id = $(this).attr('rfp_id');
			var values = {}
			if($(this).attr('display_type') != '')
				values['display_type'] = $(this).attr('display_type')
			$(this).find('input').each(function(){
				if($(this).attr('required') && !$(this).val()){
					mandatory = true;
					$(this).addClass('required_style')
				}
				if($(this).attr('name')){
					if($(this).attr('name') == 'qty' || $(this).attr('name') == 'price'){
						values[$(this).attr('name')] = parseFloat($(this).val());
					}else{
						values[$(this).attr('name')] = $(this).val();
					}
				}
			});
			new_rfp_line.push(values)
		});
		if(!mandatory){
			var rfp_post = {}
			rfp_post['post_all'] = post_all;
			rfp_post['new_rfp_line'] = new_rfp_line;
			rfp_post['new_rfp_id'] = new_rfp_id;
			rfp_post['other_info'] = rfp_other_info;
			rfp_post['rfp_id'] = rfp_id;
			this._rpc({
	            route: '/rfp_mail_line/submit_as_proposal/',
	            params: rfp_post,
	        }).then(function (data) {
	            window.location.reload();
	        });
		}else{
			alertify.alert('Message','Please make sure to fill out all mandatory fields.');
		}
		
     },
});

publicWidget.registry.BidOrders = publicWidget.Widget.extend({
    selector: '.bid_order_portal',
    events: {
        'click .bid_decline': '_onDecline',
        'click .bid_accept': '_onAccept',
		'click .requirement_submit': '_onSubmit'
    },
    start: function () {
        return this._super();
    },

	_onSubmit: function (evt) {
		var required_ids = []
		var bidder_id = $(evt.currentTarget).attr('bidder_id');
		$('.bid_vendor_requirement:checked').each(function(){
			required_ids.push(parseInt($(this).val()))
		})
		$('.checked_b_data').each(function(){
			required_ids.push(parseInt($(this).attr('doc_id')))
		});
		var post = {'required_ids': required_ids,
					'bidder_id': bidder_id}
		ajax.jsonRpc('/save/bidder/requirement', 'call', post).then(function (result){
			
		});
			
	},
     
     _onDecline: function (evt) {
     	var id = $(evt.currentTarget).attr('id');
		var action  = $(evt.currentTarget).attr('action');
		var post = {'id': id}
		alertify.confirm('Confirm','Are you sure you want to decline?',
	  		function(){
					ajax.jsonRpc(action, 'call', post).then(function (result){
						$('.bid_status').text('Declined');
						$('.bidder_state').css({'display': 'none'});
					});
	  		},
	  		function(){
	  	});
     },
    
	_onAccept: function (evt) {
		var bidder_id = $(evt.currentTarget).attr('id');
		var action  = $(evt.currentTarget).attr('action');
		$('.o_portal_sign_controls').prepend('<div class="mt16 small">By clicking Confirm, I agree that the chosen signature/initiate will be a valid electronic representation of my handwritten signature/initials'+
										'of all purposes when it is used on documents,including legally binding contracts.</div>'+
										'<div class="mt8 small">Hardcopy of the signed Non-disclosure Agreement(NDA) shall still be submitted as part of the Pre-bid Requirements.</div>')
			
		$('.o_portal_sign_controls').find('.text-right').removeClass('text-right').addClass('text-center');						
		$('.o_portal_sign_submit').prop("type", "button");
		$('.o_portal_sign_submit').removeClass('o_portal_sign_submit').addClass('vendor_o_portal_sign_submit btn-success')
		$('.vendor_o_portal_sign_submit').text('Confirm');
		$('.vendor_o_portal_sign_submit').attr('id', bidder_id);
		$('.vendor_o_portal_sign_submit').attr('action', '/bid/accept');
		var $form = $('.bid_order_portal');
		var url_path = window.location.pathname;
		var bid_id = url_path.replace('/my/bid/','');
		var show_post = {}
		show_post['bid_id'] = bid_id
		ajax.jsonRpc('/show/nda', 'call', show_post).then(function (modal){
			if(modal != 'no_record') {
				var $modal = $(modal);			
	  		    $modal.appendTo($form).modal();	
				$modal.on('click', '.close_nda', function(ev){
					$modal.empty();
			    	$modal.modal('hide');
			    	$('#bid_nda_popup_modal').remove();
				});
				$modal.on('click', '.nda_accept', function(ev){
					$('#modalaccept').modal('show');
					$('.vendor_o_portal_sign_submit').click(function(){
							$('#modalaccept').modal('hide');
							$('.modal-backdrop').remove();
							$('.bid_status').text('Bidding In-Progress');
							$('.bidder_state').css({'display': 'none'});
							$('.bid_waiting_for_acceptance').addClass('ws_bid_dn');
							$('.bid_pre_bidding').removeClass('ws_bid_dn');
							$modal.empty();
					    	$modal.modal('hide');
					    	$('#bid_nda_popup_modal').remove();
					});
				});
			}
		});
		
	},
});

});
