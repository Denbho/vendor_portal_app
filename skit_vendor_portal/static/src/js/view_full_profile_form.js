odoo.define('skit_vendor_portal.view_profile', function (require) {
'use strict';

    var core = require('web.core');
    var time = require('web.time');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var Dialog = require('web.Dialog');

    var _t = core._t;
    var qweb = core.qweb;
    
    var profile_product_form_widget; 
    
    // To close Optional Column list when click out side 
    document.addEventListener('mouseup', function(e) {
    	var container = document.getElementById('optional_col_list');
    	if(container != null){
    		if (!container.contains(e.target)) {
        		container.style.display = 'none';
    		}
    	}
    });    
    
    // To uncheck all checkbox while page load
	$(document).ready(function(){
	    $('#optional_col_list input[type=checkbox]').prop('checked',false);
	});
    
    
	    publicWidget.registry.VendorProfile = publicWidget.Widget.extend({
        selector: '.s_website_form_vendor_profile',
        
        events: {
        	'click .save_rfq_line': '_onSaveRfqLine',
            'click .save_rfp_line': '_onSaveRfpLine',
            'click .rfp_delete': '_onDeleteRfpLine',
            'click #pro_file_upload': '_uploadfile',

         	'click #site_save': '_onSiteAddressSave',
         	'click #contact_save': '_onContactPersonSave',
         	'click #affiliated_save': '_onAffiliatedSave',
         	
         	'click .rfq_line_edit_view': '_onEditRFQLine',
            'click .rfp_edit_view': '_onEditRFPLine',

	       	'click .site_edit_view': '_onEditContactPerson',
			'click .site_plus_view': '_onAddSiteOffice',
			'click .site_delete_view': '_onDeletePartner',
			
			'click .contact_edit_view': '_onEditContactPerson',
			'click .contact_plus_view': '_onAddContactPerson',
			'click .contact_delete_view': '_onContactDeletePartner',
			
			'click .affiliated_contact_plus_view': '_onAddAffiliatedCompany',
			'click .company_edit_view': '_onEditAffiliatedContact',
			'click .company_delete_view': '_onDeleteAffiliatedContact',
			
			'click .product_service_plus_view': '_onAddProductService',
			'click .product_edit_view': '_onEditProductService',
			'click .show_attachment_view': '_showAttachPopup',
			'click .prod_file_view': '_showPSDocument',
			'click .product_delete_view': '_onDeleteProductService',
			'click .vproduct_photo_view': '_onView_product_photo',
			'click .product_import_button': '_onProduct_Import',
			
			'click #edit_product_type': '_onEditProductType',
			'click #save_product_type': '_onSaveProductType',
			
			'click #edit_remarks': '_onEditRemark',
			'click #save_remarks': '_onSaveRemark',
			
			'click #edit_phone': '_onEditPhone',
			'click #save_phone': '_onSavePhone',
			
			'click #edit_mobile': '_onEditMobile',
			'click #save_mobile': '_onSaveMobile',
			
			'click #edit_email': '_onEditEmail',
			'click #save_email': '_onSaveEmail',
			
			'click #edit_website': '_onEditWebsite',
			'click #save_website': '_onSaveWebsite',
			
			'click .edit_head_office_address': '_onEditHeadOfficeAddress',

	       	'keypress input.number_field': '_onKeydownNumberField',

			'click #site_close': '_onRemovePopup',
			'click .o_optional_columns_dropdown_toggle': '_onToggleColumnPopup',
			'click #checkbox_gross_price': '_onClickGrossPrice',
			'click #checkbox_payment_terms': '_onClickPaymentTerms',
			'click #checkbox_validity_of_quote': '_onClickValidityOfQuote',
			'click #checkbox_warrenty': '_onClickWarrenty',
			'click #checkbox_delivery_lead_time': '_onClickDeliveryLeadTime',
			'click #checkbox_min_order_quantity': '_onClickMinOrderQuantity',
			'click #checkbox_delivery_cost': '_onClickDeliveryCost',
			
			'click #checkbox_unit_price': '_onClickUnitPrice',
			'click #checkbox_currency': '_onClickCurrency',
			'click #profile_site_close': '_closeAddressPopup'
    	},
    	
    	willStart: function () {
	        var prom;
	        if (!$.fn.datetimepicker) {
	            prom = ajax.loadJS("/web/static/lib/tempusdominus/tempusdominus.js");
	        }
		   	return Promise.all([this._super.apply(this, arguments), prom]);
	    },

        start: function (editable_mode) {
            if (editable_mode) {
                this.stop();
                return;
            }
            var self = this;
            this.templates_loaded = ajax.loadXML('/skit_vendor_portal/static/src/xml/vendor_website_form.xml', qweb);
            profile_product_form_widget = this;
    		this.pro_attach_file_list = [];
            this.save_edit = false;
            this.rfq_line_datas_edited = {};
            this.rfq_edited_vals = {}
            this.rfp_line_data_edited = {};
            // Initialize datetimepickers
            var l10n = _t.database.parameters;
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
            this.$target.find('.o_website_form_datetime').datetimepicker(datepickers_options);

            // Adapt options to date-only pickers
            datepickers_options.format = time.getLangDateFormat();
            this.$target.find('.o_website_form_date').datetimepicker(datepickers_options);

            // Display form values from tag having data-for attribute
            // It's necessary to handle field values generated on server-side
            // Because, using t-att- inside form make it non-editable
            var $values = $('[data-for=' + this.$target.attr('id') + ']');
            if ($values.length) {
                var values = JSON.parse($values.data('values').replace('False', '""').replace('None', '""').replace(/'/g, '"'));
                var fields = _.pluck(this.$target.serializeArray(), 'name');
                _.each(fields, function (field) {
                    if (_.has(values, field)) {
                        var $field = self.$target.find('input[name="' + field + '"], textarea[name="' + field + '"]');
                        if (!$field.val()) {
                            $field.val(values[field]);
                            $field.data('website_form_original_default_value', $field.val());
                        }
                    }
                });
            }
            return this._super.apply(this, arguments);
        },
		_closeAddressPopup: function(){
			$('.site_address_popup').remove();
		},
		/**
         * @private
 		* @param {Object} ev
         * Show Attachment Popup
         */
		_showAttachPopup: function(ev){
			var $form = $('.vreg_container');
			var ps_id = $(ev.currentTarget).attr('ps_id');
			var action = $(ev.currentTarget).attr('action');
			var post = {'ps_id': ps_id}
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
         * Show PS Document
         */
		_showPSDocument: function(ev){
			var $form = $('.vreg_container');
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
        /** Import Products **/
	 _onProduct_Import:function(){
		 	// import product file
		 	$(".product_import").click();
		 	// Read upload file
		    $(".product_import").off().on('change', function(){
		        readFileURL(this);
		    });
		 	/* file import Start*/
		    var readFileURL = function(input) {
		        if (input.files && input.files[0]) {
		        	var file = input.files[0];
		        	var fileTypes = ['xlsx'];
					var extension = file.name.split('.').pop().toLowerCase(),  //file extension from input file
					            isSuccess = fileTypes.indexOf(extension) > -1;
					if (isSuccess) {
			            var reader = new FileReader();

					    reader.onload = function(e) {
					      var data = e.target.result;
					      // Insert in table row
					      ProcessExcel(data);
					    };

					    reader.onerror = function(ex) {
					      console.log(ex);
					    };
					    reader.readAsBinaryString(file);
					}else {
						$(this).val('')
						alertify.alert("Message", "Please upload a valid Excel 'xlsx' format file.")
					}
		        }
		    };
		    // Insert xlsx values in rows
		   var ProcessExcel = function(data) {
		        //Read the Excel File data.

		        var workbook = XLSX.read(data, {
		            type: 'binary'
		        });
		 
		        //Fetch the name of First Sheet.
		        var firstSheet = workbook.SheetNames[0];
		 
		        //Read all rows from First Sheet into an JSON array.
		        var excelRows = XLSX.utils.sheet_to_row_object_array(workbook.Sheets[firstSheet]);
		        var post = {};
				if(excelRows.length == 0){
					alertify.alert('Message','Please make sure to fill out all mandatory fields.');
					return false;
				}else{
					var actual_keys = ['ProductServiceName(Required Field)', 'ProductServiceDescription(Required Field)', 'ProductClassification(Required Field)',
										'Price(Required Field)', 'UOM(Required Field)']
					var excel_keys = []
					$.each(excelRows[0], function(key, value) { 
						excel_keys.push(key)
					});
					
					if(JSON.stringify(actual_keys) != JSON.stringify(excel_keys)){
						alertify.alert('Message','Please choose proper document to import!');
						return false;
					}
				}
		        //Add the data rows from Excel file.
		        for (var i = 0; i < excelRows.length; i++) {
		        	var crow = $('.product_service_ids').find('tbody tr').length
		        	if (i == 0){
		        		post['count'] = crow;
		        	}	
		        	else{
		        		post['count'] = crow+i;
		        	}
					var p_name = excelRows[i]["ProductServiceName(Required Field)"];
					var p_desc = excelRows[i]["ProductServiceDescription(Required Field)"];
					var product_classification = excelRows[i]["ProductClassification(Required Field)"];
					var price = excelRows[i]["Price(Required Field)"];
					var uom = excelRows[i]["UOM(Required Field)"];
		            post['p_name'] = excelRows[i]["ProductServiceName(Required Field)"];
		            post['p_desc'] = excelRows[i]["ProductServiceDescription(Required Field)"];
		            post['product_classification_id']= excelRows[i]["ProductClassification(Required Field)"];
		            post['category_name'] = excelRows[i]["ProductClassification(Required Field)"];
		            post['p_price'] = excelRows[i]["Price(Required Field)"];
		            post['product_uom_id'] = excelRows[i]["UOM(Required Field)"];
		            post['uom_name'] = excelRows[i]["UOM(Required Field)"];
		            
		            post['image_1920'] = '';
					post['img_attached'] = false;
					
					post['product_files'] = [];
					post['file_attached'] = false;
		            post['is_edit_profile'] = true;
					if(p_name == undefined || p_desc == undefined || product_classification == undefined || price == undefined || uom == undefined){
						alertify.alert('Message','Please make sure to fill out all mandatory fields.');
						return false;
					}else{
						ajax.jsonRpc('/new/row/product', 'call', post).then(function (modal) { 
	  		    			$('.product_service_ids tr#product_empty_row').before(modal);
		  		    		var row = $('.product_service_ids tbody tr').length - 1;
	  						if(row >=1){
			  		    		$('.product_service_ids tr#product_empty_row').addClass('v_display_none');
			  		    	}
		  		    	});
					}
		        }
		    };
	 },
        _onToggleColumnPopup: function(){
	    	var x = document.getElementById("optional_col_list");
	  		if (x.style.display === "none") {
	    		x.style.display = "block";
	  		} else {
	    		x.style.display = "none";
	  		}
		},
		
		_onClickDeliveryCost: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_delivery_cost_td').removeClass('d-none');
				$('.checkbox_delivery_cost_th').removeClass('d-none');
	     		var elem = document.getElementsByClassName('scrollit')[0];
	     		var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
	     
	    	} else {
				$('.checkbox_delivery_cost_td').addClass('d-none');
				$('.checkbox_delivery_cost_th').addClass('d-none');
	    	}
		},
		
		_onClickUnitPrice: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_unit_price_td').removeClass('d-none');
				$('.checkbox_unit_price_th').removeClass('d-none');
	     		var elem = document.getElementsByClassName('scrollit')[0];
	     		var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
	    	} else {
				$('.checkbox_unit_price_td').addClass('d-none');
				$('.checkbox_unit_price_th').addClass('d-none');
	    	}
		},
		
		_onClickCurrency: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_currency_td').removeClass('d-none');
				$('.checkbox_currency_th').removeClass('d-none');
	     		var elem = document.getElementsByClassName('scrollit')[0];
	     		var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
	    	} else {
				$('.checkbox_currency_td').addClass('d-none');
				$('.checkbox_currency_th').addClass('d-none');
	    	}
		},	
		
		_onClickMinOrderQuantity: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_min_order_quantity_td').removeClass('d-none');
				$('.checkbox_min_order_quantity_th').removeClass('d-none');
		      	var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
		    } else {
				$('.checkbox_min_order_quantity_td').addClass('d-none');
				$('.checkbox_min_order_quantity_th').addClass('d-none');
		    }
		},
	
		_onClickDeliveryLeadTime: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_delivery_lead_time_td').removeClass('d-none');
				$('.checkbox_delivery_lead_time_th').removeClass('d-none');
		      	var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
		    } else {
				$('.checkbox_delivery_lead_time_td').addClass('d-none');
				$('.checkbox_delivery_lead_time_th').addClass('d-none');
		    }
		},
		
		_onClickWarrenty: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_warrenty_td').removeClass('d-none');
				$('.checkbox_warrenty_th').removeClass('d-none');
				var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
	    	} else {
				$('.checkbox_warrenty_td').addClass('d-none');
				$('.checkbox_warrenty_th').addClass('d-none');
	    	}
		},
		
		_onClickGrossPrice: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_gross_total_td').removeClass('d-none');
				$('.checkbox_gross_total_th').removeClass('d-none');
				var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
	    	} else {
				$('.checkbox_gross_total_td').addClass('d-none');
				$('.checkbox_gross_total_th').addClass('d-none');
	    	}
		},
		
		_onClickPaymentTerms: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_payment_terms_td').removeClass('d-none');
				$('.checkbox_payment_terms_th').removeClass('d-none');
			  	var leftPos = $('.scrollit').scrollLeft();
			    $(".scrollit").animate({
			        scrollLeft: leftPos + 200
			    }, 800);
	    	} else {
				$('.checkbox_payment_terms_td').addClass('d-none');
				$('.checkbox_payment_terms_th').addClass('d-none');
	    	}
		},
		
		_onClickValidityOfQuote: function(ev){
	    	if($(ev.currentTarget).is(':checked')){
				$('.checkbox_validity_of_quote_td').removeClass('d-none');
				$('.checkbox_validity_of_quote_th').removeClass('d-none');
		      	var leftPos = $('.scrollit').scrollLeft();
		        $(".scrollit").animate({
		            scrollLeft: leftPos + 200
		        }, 800);
	    	} else {
				$('.checkbox_validity_of_quote_td').addClass('d-none');
				$('.checkbox_validity_of_quote_th').addClass('d-none');
	    	}
		},
	
		_onRemovePopup: function(){
			$('.modal-backdrop').remove();
            $('.modal').modal('hide');
			$('#modal_rfP_line').remove();
		},

        destroy: function () {
            this._super.apply(this, arguments);
            this.$target.find('button').off('click');
        },
        
        sendFormValues: function (e) {
        	var current_form = $(e.currentTarget).closest('form');
            e.preventDefault();  // Prevent the default submit behavior
            var self = this;

            current_form.find('#o_website_form_result').empty();
            if (!self.check_error_fields({}, e)) {
                self.update_status('invalid', e);
				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
                return false;
            }

            // Prepare form inputs
            this.form_fields = current_form.serializeArray();
            $.each(current_form.find('input[type=file]'), function (outer_index, input) {
                $.each($(input).prop('files'), function (index, file) {
                    // Index field name as ajax won't accept arrays of files
                    // when aggregating multiple files into a single field value
                    self.form_fields.push({
                        name: input.name + '[' + outer_index + '][' + index + ']',
                        value: file
                    });
                });
            });

            // Serialize form inputs into a single object
            // Aggregate multiple values into arrays
            var form_values = {};
            _.each(this.form_fields, function (input) {
                if (input.name in form_values) {
                    // If a value already exists for this field,
                    // we are facing a x2many field, so we store
                    // the values in an array.
                    if (Array.isArray(form_values[input.name])) {
                        form_values[input.name].push(input.value);
                    } else {
                        form_values[input.name] = [form_values[input.name], input.value];
                    }
                } else {
                    if (input.value !== '') {
                        form_values[input.name] = input.value;
                    }
                }
            });

			var act = $(e.currentTarget).closest('form').attr('action');
			var act_model_name = $(e.currentTarget).closest('form').data('model_name');
			var act_force_action = $(e.currentTarget).closest('form').data('force_action');
            // Post form and handle result
            ajax.post(act, form_values)
            .then(function (result_data) {
                result_data = JSON.parse(result_data);
                if (!result_data.id) {
                    // Failure, the server didn't return the created record ID
                    self.update_status('error', e);
                    if (result_data.error_fields) {
                        // If the server return a list of bad fields, show these fields for users
                        self.check_error_fields(result_data.error_fields);
                    }
                } else {
                    // Success, redirect or update status
                    var success_page = current_form.attr('data-success_page');
                    if (success_page) {
                        $(window.location).attr('href', success_page);
                    }
                    else {
							var name = result_data.name;
							var street = result_data.street;
							var street2 = result_data.street2;
							var barangay_id = result_data.barangay_id;
							var city_id = result_data.city_id;
							var province_id = result_data.province_id;
							var state_id = result_data.state_id;
							var zip = result_data.zip;
							var country_id = result_data.country_id;
							var child_id = result_data.id;
							var type = result_data.type;
							
							var phone = result_data.phone;
							var mobile = result_data.mobile;
							var department = result_data.department;
							var position = result_data.position;
							var email = result_data.email;
							
							var saved_partner_id = result_data.id;
							var logged_in_partner_id = result_data.logged_in_partner_id;
							var is_affiliated = result_data.is_affiliated;
							var relationship = result_data.relationship;
							
							var product_service = result_data.product_service;
							var product_category_name = result_data.product_category_name;
							var price = result_data.price;
							var is_product_service = result_data.is_product_service;
						
							var table_name = $(e.currentTarget).closest('form').attr('name');
							var table = document.getElementsByName(table_name);
							var row_id = document.getElementById(child_id);
							if(row_id){
								var rowIndex = row_id.rowIndex;
								if(rowIndex){
									table[0].deleteRow(rowIndex);
								}	
							}
							
							if(logged_in_partner_id == saved_partner_id){
                   				window.location.reload();
                   			}
							else if(type == 'other'){
								var row_id = document.getElementById('site_empty_row');
								if(row_id){
									var rowIndex = row_id.rowIndex;
									if(rowIndex){
										table[0].deleteRow(rowIndex);
									}	
								}
								$('table[name='+table_name+']').find('tbody').append('<tr id='+child_id+'><td>' + name + '</td><td>' + street + '</td><td>' + street2 + '</td><td>' + barangay_id + '</td><td>' + city_id + '</td><td>' + province_id + '</td><td>' + state_id + '</td><td>' + zip + '</td><td>' + country_id + '</td><td align="center"><span id='+child_id+' class="site_edit_view"><i class="fa fa-pencil-square-o span_icon isite_edit"></i></span><span id='+child_id+' class="site_delete_view"><i class="fa fa-trash span_icon isite_delete"></i></span></td></tr>');
                   			}
                   			
                   			else if(type == 'contact'){
	                   			var row_id = document.getElementById('contact_empty_row');
								if(row_id){
									var rowIndex = row_id.rowIndex;
									if(rowIndex){
										table[0].deleteRow(rowIndex);
									}	
								}
								$('table[name='+table_name+']').find('tbody').append('<tr id='+child_id+'><td>' + name + '</td><td>' + department + '</td><td>' + position + '</td><td>' + phone + '</td><td>' + mobile + '</td><td>' + email + '</td><td align="center"><span id='+child_id+' class="contact_edit_view"><i class="fa fa-pencil-square-o span_icon icontact_edit"></i></span><span id='+child_id+' class="contact_delete_view"><i class="fa fa-trash span_icon icontact_delete"></i></span></td></tr>');
                   			}
                   			
                   			else if(is_affiliated == true){
                   				var row_id = document.getElementById('affiliated_empty_row');
								if(row_id){
									var rowIndex = row_id.rowIndex;
									if(rowIndex){
										table[0].deleteRow(rowIndex);
									}	
								}
								$('table[name='+table_name+']').find('tbody').append('<tr id='+child_id+'><td>' + name + '</td><td>' + relationship + '</td><td>' + email + '</td><td align="center"><span id='+child_id+' class="company_edit_view"><i class="fa fa-pencil-square-o span_icon icompany_edit"></i></span><span id='+child_id+' class="company_delete_view"><i class="fa fa-trash span_icon icompany_delete"></i></span></td></tr>');
                   			}
                   			$('.modal-backdrop').remove();
                 			$('.modal').modal('hide');
							$('.site_address_popup').remove();
                    }

                    // Reset the form
                    current_form[0].reset();
                    self.save_edit = false;
                }
            })
            .guardedCatch(function (){
                self.update_status('error', e);
            });
        },

        check_error_fields: function (error_fields, e) {
            var self = this;
            var form_valid = true;
            // Loop on all fields
            var current_form = $(e.currentTarget).closest('form');
            current_form.find('.form-field').each(function (k, field){
                var $field = $(field);
                var field_name = $field.find('.col-form-label').attr('for');
                // Validate inputs for this field
                var inputs = $field.find('.o_website_form_input:not(#editable_select)');
                var invalid_inputs = inputs.toArray().filter(function (input, k, inputs) {
                    // Special check for multiple required checkbox for same
                    // field as it seems checkValidity forces every required
                    // checkbox to be checked, instead of looking at other
                    // checkboxes with the same name and only requiring one
                    // of them to be checked.
                    if (input.required && input.type === 'checkbox') {
                        // Considering we are currently processing a single
                        // field, we can assume that all checkboxes in the
                        // inputs variable have the same name
                        var checkboxes = _.filter(inputs, function (input){
                            return input.required && input.type === 'checkbox';
                        });
                        return !_.any(checkboxes, function (checkbox) { return checkbox.checked; });

                    // Special cases for dates and datetimes
                    } else if ($(input).hasClass('o_website_form_date')) {
                        if (!self.is_datetime_valid(input.value, 'date')) {
                            return true;
                        }
                    } else if ($(input).hasClass('o_website_form_datetime')) {
                        if (!self.is_datetime_valid(input.value, 'datetime')) {
                            return true;
                        }
                    }
                    return !input.checkValidity();
                });

                // Update field color if invalid or erroneous
                $field.removeClass('o_has_error').find('.form-control, .custom-select').removeClass('is-invalid');
                if (invalid_inputs.length || error_fields[field_name]){
                    $field.addClass('o_has_error').find('.form-control, .custom-select').addClass('is-invalid')
                    if (_.isString(error_fields[field_name])){
                        $field.popover({content: error_fields[field_name], trigger: 'hover', container: 'body', placement: 'top'});
                        // update error message and show it.
                        $field.data("bs.popover").config.content = error_fields[field_name];
                        $field.popover('show');
                    }
                    form_valid = false;
                }
            });
            return form_valid;
        },

        is_datetime_valid: function (value, type_of_date) {
            if (value === "") {
                return true;
            } else {
                try {
                    this.parse_date(value, type_of_date);
                    return true;
                } catch (e) {
                    return false;
                }
            }
        },

        // This is a stripped down version of format.js parse_value function
        parse_date: function (value, type_of_date, value_if_empty) {
            var date_pattern = time.getLangDateFormat(),
                time_pattern = time.getLangTimeFormat();
            var date_pattern_wo_zero = date_pattern.replace('MM','M').replace('DD','D'),
                time_pattern_wo_zero = time_pattern.replace('HH','H').replace('mm','m').replace('ss','s');
            switch (type_of_date) {
                case 'datetime':
                    var datetime = moment(value, [date_pattern + ' ' + time_pattern, date_pattern_wo_zero + ' ' + time_pattern_wo_zero], true);
                    if (datetime.isValid())
                        return time.datetime_to_str(datetime.toDate());
                    throw new Error(_.str.sprintf(_t("'%s' is not a correct datetime"), value));
                case 'date':
                    var date = moment(value, [date_pattern, date_pattern_wo_zero], true);
                    if (date.isValid())
                        return time.date_to_str(date.toDate());
                    throw new Error(_.str.sprintf(_t("'%s' is not a correct date"), value));
            }
            return value;
        },

        update_status: function (status, e) {
            var self = this;
            if (status !== 'success') {  // Restore send button behavior if result is an error
            }
            var current_form = $(e.currentTarget).closest('form');
            var $result = current_form.find('#o_website_form_result');
            this.templates_loaded.then(function () {
                $result.replaceWith(qweb.render("website_form.status_" + status));
            });
        },

		_onChange_Site_Address_Field: function(){
			$(".scountry_id").on('change',function(e) {
				var $s_country = $('select[name="country_id"]');
				var country_id =  $s_country.val(); 
				if(country_id){
					var post = {'country_id': country_id,
								'name': 'state_id'}
					ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
						$("#sstate_id").html(modal)
						$("#sprovince_id").html('<option value=""></option>');
						$("#scity_id").html('<option value=""></option>');
						$("#sbarangay_id").html('<option value=""></option>');
					});
				}
			});
			$(".sstate_id").on('change',function(e){
				var $s_state = $('select[name="state_id"]');
				var state_id =  $s_state.val(); 
				if(state_id){
					var post = {'state_id': state_id,
								'name': 'province_id'}
					ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
						$("#sprovince_id").html(modal);
						$("#scity_id").html('<option value=""></option>');
						$("#sbarangay_id").html('<option value=""></option>');
					});
				}
			});
			$(".sprovince_id").on('change',function(e) {
				var $s_province = $('select[name="province_id"]');
				var province_id =  $s_province.val(); 
			    if(province_id){
					var post = {'province_id': province_id,
								'name': 'city_id'}
					ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
						$("#scity_id").html(modal);
						$("#sbarangay_id").html('<option value=""></option>');
					});
				}
			});
			$(".scity_id").on('change',function(e) {
				var $s_city = $('select[name="city_id"]');
				var city_id =  $s_city.val(); 
			    if(city_id){
					var post = {'city_id': city_id,
								'name': 'barangay_id'}
					ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
						$("#sbarangay_id").html(modal)
					});
				}
			});
		 },
        
        _onChange_Site_Address:function(){
			var self = this;
			  var $site_state = $('select[id="sstate_id"]');
		      var $site_stateOptions = $site_state.filter(':enabled').find('option:not(:first)');
		
		      var $site_province = $('select[id="sprovince_id"]');
		      var $site_provinceOptions = $site_province.filter(':enabled').find('option:not(:first)');
		
		      var $site_city = $('select[id="scity_id"]');  
		      var $site_cityOptions = $site_city.filter(':enabled').find('option:not(:first)');
		
		      var $site_barangay = $('select[id="sbarangay_id"]');
		      var $site_barangayOptions = $site_barangay.filter(':enabled').find('option:not(:first)');
		
		      // Display States
		      var $site_country = $('select[id="scountry_id"]');
		      var site_countryID = ($site_country.val() || 0);
		      $site_stateOptions.detach();
		      var $displayedSiteState = $site_stateOptions.filter('[data-country_id=' + site_countryID + ']');
		      var nb = $displayedSiteState.appendTo($site_state).show().length;
		      $site_state.parent().toggle(nb >= 1);
		
		      // Country on change
			  $(".scountry_id").on('change',function(e) {
			  
				  var country_id =  $(".scountry_id option:selected").val(); 
				  if(country_id){
					  $site_stateOptions.detach();
				      var $displayedSiteState = $site_stateOptions.filter('[data-country_id=' + country_id + ']');
				      var nb = $displayedSiteState.appendTo($site_state).show().length;
				      $site_state.parent().toggle(nb >= 1);
				  }
			  });
			  // State on change
			  $(".sstate_id").on('change',function(e) {
				  var state_id =  $(".sstate_id option:selected").val(); 
			      if(state_id){
			    	  $site_provinceOptions.detach();
				      var $displayedSiteProvince = $site_provinceOptions.filter('[data-state_id=' + state_id + ']');
				      var nb = $displayedSiteProvince.appendTo($site_province).show().length;
				      $site_province.parent().toggle(nb >= 1);
			      }
			      
			  });
			  // Province on change
			  $(".sprovince_id").on('change',function(e) {
				  var province_id =  $(".sprovince_id option:selected").val(); 
			      if(province_id){
			    	  $site_cityOptions.detach();
				      var $displayedSiteCity = $site_cityOptions.filter('[data-province_id=' + province_id + ']');
				      var nb = $displayedSiteCity.appendTo($site_city).show().length;
				      $site_city.parent().toggle(nb >= 1);
			      }
			      
			  });
			  
			  //City on change
			  $(".scity_id").on('change',function(e) {
				  var city_id =  $(".scity_id option:selected").val(); 
			      if(city_id){
			    	  $site_barangayOptions.detach();
				      var $displayedSiteBarangay = $site_barangayOptions.filter('[data-city_id=' + city_id + ']');
				      var nb = $displayedSiteBarangay.appendTo($site_barangay).show().length;
				      $site_barangay.parent().toggle(nb >= 1);
			      }
			      
			  });
	  	},
  		/*** Ended Add Site Address ***/ 

        _onKeydownNumberField: function (e) {
        	var code = (e.which) ? e.which : e.keyCode;
    	    if (code > 31 && (code < 48 || code > 57)) {
    	        e.preventDefault();
    	    }    	
	    },
	
		_onEditEmail: function(ev) {
			if (this.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				this.save_edit = true;
				this.$('.email_row_edit').addClass('d-none');
				this.$('.email_row_save').removeClass('d-none');
			}
			
		},
		
		_onSaveEmail: function(e) {
			var self = this;
			var email = $('#email').val();
           	var form_values = {};
           	form_values['email'] = email;
			var inpObjEmail = document.getElementById("email");
			if (!inpObjEmail.checkValidity()) {
                self.update_status('invalid', e);
                return false;
            }
			self._showPopup(e, form_values);
			this.save_edit = false;
		},
		
		_onEditPhone: function(ev) {
			if (this.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				this.save_edit = true;
				this.$('.phone_row_edit').addClass('d-none');
				this.$('.phone_row_save').removeClass('d-none');
			}
			
		},
		
		_onEditRemark: function(ev) {
			if (this.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				this.save_edit = true;
				this.$('#edit_remarks').addClass('d-none');
				this.$('#save_remarks').removeClass('d-none');
				document.getElementById("comment").readOnly = false; 
			}
		},
		
		_onSaveRemark: function(e) {
			var self = this;
			var comment = $('#comment').val();
           	var form_values = {};
           	form_values['comment'] = comment;
           	var inputObjComment = document.getElementById("comment");
			if (!inputObjComment.checkValidity()) {
                self.update_status('invalid', e);
                return false;
            }
			self.updateInlineEditValues(e, form_values);
			this.$('#edit_remarks').removeClass('d-none');
			this.$('#save_remarks').addClass('d-none');
			document.getElementById("comment").readOnly = true; 
			this.save_edit = false;
		},
		
		_onSavePhone: function(e) {
			var self = this;
			var phone = $('#phone').val();
           	var form_values = {};
           	form_values['phone'] = phone;
           	var inpObjPhone = document.getElementById("phone");
			if (!inpObjPhone.checkValidity()) {
                self.update_status('invalid', e);
                return false;
            }
			self._showPopup(e, form_values);
			this.save_edit = false;
		},
		
		_onEditMobile: function(ev) {
			if (this.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				this.save_edit = true;
				this.$('.mobile_row_edit').addClass('d-none');
				this.$('.mobile_row_save').removeClass('d-none');
			}
		},
		
		_onSaveMobile: function(e) {
			var self = this;
			var mobile = $('#mobile').val();
           	var form_values = {};
           	form_values['mobile'] = mobile;
           	var inpObjMobile = document.getElementById("mobile");
			if (!inpObjMobile.checkValidity()) {
                self.update_status('invalid', e);
                return false;
            }
			self._showPopup(e, form_values);
			this.save_edit = false;
		},
		
		_onEditWebsite: function(ev) {
			if (this.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				this.save_edit = true;
				this.$('.website_row_edit').addClass('d-none');
				this.$('.website_row_save').removeClass('d-none');
			}
		},
	
		_onSaveWebsite: function(e) {
			var self = this;
			var website = $('#website').val();
           	var form_values = {};
           	form_values['website'] = website;
           	var inpObjWebsite = document.getElementById("website");
			if (!inpObjWebsite.checkValidity()) {
                self.update_status('invalid', e);
                return false;
            }
			self._showPopup(e, form_values);
			this.save_edit = false;
		},
		
		_showPopup: function(e, form_values) {
			var self = this;
			var $content = ($('<p/>').text(_t('Are you sure you want to do this?')));
			new Dialog(this, {
	            title: _t("Confirmation"),
	            size: 'medium',
	            $content: $content,
	            buttons: [
	                {text: _t("Save"), classes: 'btn-primary',  close: true, click: function () {
	                   self.updateInlineEditValues(e, form_values);
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
		},
		
		_onEditProductType: function(ev) {
			if (this.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				this.save_edit = true;
				this.$('.pc_checkbox_input').prop('disabled', false);
				this.$('.pc_checkbox_other').prop('disabled', false);
				this.$('#other_categories').prop('disabled', false);
				
				this.$('#edit_product_type').addClass('d-none');
				this.$('#save_product_type').removeClass('d-none');
			}
		},
	
		_onSaveProductType: function(ev) {
			var self = this;
			this.$('.pc_checkbox_input').prop('disabled', true);
			this.$('.pc_checkbox_other').prop('disabled', true);
			this.$('#other_categories').prop('disabled', true);
			
			this.$('#edit_product_type').removeClass('d-none');
			this.$('#save_product_type').addClass('d-none');
			var product_classification_ids = [];
			var categ_ids = [];
			$('.product_classification_ids div').each(function() {
				var is_categ_checked = $(this).find('#category_id').is(':checked');
				if (is_categ_checked) {
					var categ_id = $(this).find('#category_id').attr('categ_id')
					categ_ids.push(parseInt(categ_id));
				}
			});

			var post = {}
			post['product_classification_ids'] = categ_ids;
			var other_category = $("#has_other_category").is(':checked');
		   	var other_categories = $("#other_categories").val();
		   	post['other_category'] = other_category
			post['other_categories'] = other_categories
			ajax.jsonRpc('/view_profile/update_product_other_category', 'call', post).then(function(modal) {
				//window.location.reload();
				self.save_edit = false;
			});
		},
	
		// Head office address
		_onEditHeadOfficeAddress: function(ev) {
			ev.preventDefault();
			var self = this;
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			if (self.save_edit){
				var $content = ($('<p/>').text(_t('Please save your changes.')));
				new Dialog(this, {
		            title: _t("Confirmation"),
		            size: 'medium',
		            $content: $content,
		            buttons: [
		                {text: _t("OK"), close: true},
		            ],
		        }).open();
			}
			else{
				self.save_edit = true;
				self.edit_contact_person_popup(post, $form, ev);
			}
		},
	
		// Contact
		
		_onAddContactPerson: function(ev) {
			ev.preventDefault();
			var self = this;
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			self.add_contact_person_popup(post, $form, ev);
		},
		add_contact_person_popup: function(post, $form, e) {
			var self = this;
			ajax.jsonRpc('/view_profile/new_contact_person_popup', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				$modal.on('click', '.is-invalid', function(ev){
					$(this).removeClass('is-invalid');
				});
			});
		},
		
		_product_attach:function(){
		 	/* image attach Start*/
		 	var readURL = function(input) {
		        if (input.files && input.files[0]) {
					var size = parseFloat(input.files[0].size / 1024).toFixed(2)
					if(size <= 5000){
			            var reader = new FileReader();
	
			            reader.onload = function (e) {
			                $('.product-pic').attr('src', e.target.result);
			                $('.product-pic').attr('img_data', e.target.result )
			            }
			    
			            reader.readAsDataURL(input.files[0]);
					}else{
						alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
					}
		        }
		    }
		    $(".pro-pic-upload").off().on('change', function(){
		        readURL(this);
		    });
		    
		    $(".product_attach_icon").off().on('click', function() {
		       $(".pro-pic-upload").click();
		    });
		    /* image attach Start*/
		    /* file attach Start*/
		    var readFileURL = function(input) {
		        if (input.files && input.files[0]) {
					var size = parseFloat(input.files[0].size / 1024).toFixed(2)
					if(size <= 5000){
			        	var file = input.files[0];
			        	$('.product_file').text(file.name);
			        	$('.pro_attach_p').addClass('d-none');
			        	$('.attach_delete').removeClass('d-none');
			            var reader = new FileReader();
			            reader.onload = function (e) {
			            	$('.product_file').attr('file_data', e.target.result)
			            }
			            reader.readAsDataURL(input.files[0]);
					}else{
						alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
					}
		        }
		    }
		   $(".product_file_input").off().on('change', function(){
		        readFileURL(this);
		    });
		    
		    $(".pro_file_upload").off().on('click', function() {
		       $(".product_file_input").click();
		    });
		    
		    // Delete uploaded file
		    $(".attach_delete").off().on('click', function() {
		    	$('.attach_delete').addClass('d-none');
	        	$('.pro_attach_p').removeClass('d-none');
	        	$('.product_file').removeAttr("file_data");
	        	$('.product_file').text('');
	        	$('.product_file_input').val(null);
			});
		    
		    /* file attach end*/
		    
		    /* Allow number value in price */
			$(".vinput_price").on('keydown keyup paste input',function(e) {
			    // between 0 and 9    		
				if(e.which!=8 && e.which!=0)
			    {if (e.which < 48 || e.which > 57) {
			        return(false);  // stop processing
			    }}
			});
	 },
		
		_onEditRFPLine: function(ev){
			var post = this.rfq_line_datas_edited;
			var $form = $(ev.currentTarget).closest('form');
			this.edit_rfp_line_popup(post, $form, ev);
		},
		
		edit_rfp_line_popup: function(post, $form, ev){
			var self = this;
			var rfp_mail_line_id = $(ev.currentTarget).attr('id');
			post['rfp_mail_line_id'] = rfp_mail_line_id;
			$('#myrfp_tables tbody tr#'+rfp_mail_line_id).each(function(){
				$(this).find('td').each(function(){
			    	var $td = $(this).text().trim();
			    	var td_index = $(this).index();
			    	var index = td_index + 1
			      	var $th = $('#myrfp_tables tr').find('th:nth-child(' + index + ')').attr('name');
			      	if($th != undefined){
			      		post[$th] = $td;
			      	}
			    })
			});
			ajax.jsonRpc('/my_rfp_line/edit_view', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				// Calculate Gross Price when open edit form
				var qty = $('#qty').val();
				var unit_price = $('#unit_price').val();
				if(qty != undefined && unit_price != undefined && qty != '' && unit_price != '' && qty != null && unit_price != null){
					var total = parseFloat(qty) * parseFloat(unit_price)
					total = total.toFixed(2)
					$('#gross_total').text(total);
				}else{
					$('#gross_total').text('');
				}
				
				// Onchange qty and unitprice input
				$('#qty, #unit_price').on('input', function(){
					var qty = $('#qty').val();
					var unit_price = $('#unit_price').val();
					if(qty != undefined && unit_price != undefined && qty != '' && unit_price != '' && qty != null && unit_price != null){
						var total = parseFloat(qty) * parseFloat(unit_price)
						total = total.toFixed(2)
						$('#gross_total').text(total);
					}else{
						$('#gross_total').text('');
					}
				});
			});
			
		},
		_onSaveRfpLine: function(e) {
			var self = this;
			self.setRFPLineValues(e)
		},
		
		setRFPLineValues: function (e) {
        	var current_form = $(e.currentTarget).closest('form');
            e.preventDefault();  // Prevent the default submit behavior
            var self = this;
            current_form.find('#o_website_mail_form_result').empty();
            if (!self.check_error_fields({}, e)) {
                self.update_status('invalid', e);
				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
                return false;
            }
             // Prepare form inputs
            this.form_fields = current_form.serializeArray();
            $.each(current_form.find('input[type=file]'), function (outer_index, input) {
                $.each($(input).prop('files'), function (index, file) {
                    // Index field name as ajax won't accept arrays of files
                    // when aggregating multiple files into a single field value
                    self.form_fields.push({
                        name: input.name + '[' + outer_index + '][' + index + ']',
                        value: file
                    });
                });
            });

            // Serialize form inputs into a single object
            // Aggregate multiple values into arrays
            var form_values = {};
            _.each(this.form_fields, function (input) {
                if (input.name in form_values) {
                    // If a value already exists for this field,
                    // we are facing a x2many field, so we store
                    // the values in an array.
                    if (Array.isArray(form_values[input.name])) {
                        form_values[input.name].push(input.value);
                    } else {
                        form_values[input.name] = [form_values[input.name], input.value];
                    }
                } else {
                    if (input.value !== '') {
                        form_values[input.name] = input.value;
                    }
                }
            });
            this.rfp_line_datas_edited = form_values
            var rfp_line_id = e.currentTarget.id;
		var product_name = '';
		var unit_measure = '';
		var description = '';
		var qty = '';
		var unit_price = '';
		var gross_price = $('#gross_total').text();
		if(document.getElementById("product_name") != null && document.getElementById("product_name") != undefined){
			product_name = document.getElementById("product_name").value;
		}
		if(document.getElementById("unit_name") != null && document.getElementById("unit_name") != undefined){
			unit_measure = document.getElementById("unit_name").value;
		}
		if(document.getElementById("name") != null && document.getElementById("name") != undefined){
			description = document.getElementById("name").value;
		}
		if(document.getElementById("qty") != null && document.getElementById("qty") != undefined){
			qty = document.getElementById("qty").value;
		}
		if(document.getElementById("unit_price") != null && document.getElementById("unit_price") != undefined){
			unit_price = document.getElementById("unit_price").value;
		}
		
		$('#myrfp_tables').find('tr#'+rfp_line_id).find('.product').html(product_name);
		$('#myrfp_tables').find('tr#'+rfp_line_id).find('.description').html(description);
		$('#myrfp_tables').find('tr#'+rfp_line_id).find('.uom').html(unit_measure);
	  	$('#myrfp_tables').find('tr#'+rfp_line_id).find('.qty').html(qty);
	  	$('#myrfp_tables').find('tr#'+rfp_line_id).find('.unitprice').html(unit_price);
        $('#myrfp_tables').find('tr#'+rfp_line_id).find('.grossprice').html(gross_price);

		var grand_total = 0;
		$('#myrfp_tables tr.rfp_exist_record').each(function(ev){
			var g_total = $(this).find('.grossprice').text();
			if(g_total != undefined && g_total != null && g_total != ''){
				grand_total = parseFloat(grand_total) + parseFloat(g_total.replace(/,/g, ''))
				grand_total = (grand_total).toFixed(2)
				
			}
		});

        $('#view_rfp_mail_line_form').find('.total').html(grand_total);

		$('.modal-backdrop').remove();
        $('.modal').modal('hide');
		$('#modal_rfP_line').remove();
            
        },
      _onDeleteRfpLine: function(e) {
			var post = {};
			var rfq_mail_line_delete_id = $(e.currentTarget).attr('id');
			post['rfq_mail_line_delete_id'] = rfq_mail_line_delete_id;
			var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			var table_name = $(e.currentTarget).closest('table').attr('name');
			var table = document.getElementsByName(table_name);
			var row_id = document.getElementById(rfq_mail_line_delete_id);
			new Dialog(this, {
	            title: _t("Confirmation"),
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
						ajax.jsonRpc('/my_rfp_line/delete_view', 'call', post).then(function(result) {
							if(row_id){
								var rowIndex = row_id.rowIndex;
								if(rowIndex){
									document.getElementById('myrfp_tables').deleteRow(rowIndex);
									window.location.reload();
								
								}	
							}
						});
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
		},
		
    	_onEditRFQLine: function(ev) {
			var post = this.rfq_line_datas_edited;
			var $form = $(ev.currentTarget).closest('form');
			this.edit_rfq_popup(post, $form, ev);
		},
		
    	edit_rfq_popup: function(post, $form, ev) {
			var self = this;
			var rfq_mail_line_id = $(ev.currentTarget).attr('id');
			post['rfq_mail_line_id'] = rfq_mail_line_id;
			ajax.jsonRpc('/my_rfq_line/edit_view', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				$modal.on('click', '.is-invalid', function(ev){
					$(this).removeClass('is-invalid');
				});
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
	          	$('.validity_from_cls').datetimepicker(datepickers_options);
	          	$('.validity_to_cls').datetimepicker(datepickers_options);
				/**
				* Set Date Format for popup date fields from Odoo Language settings END --> 
				**/
				self._product_attach(ev);
			});
		},
		
		_onSaveRfqLine: function(e) {
			var self = this;
			self.setRFQLineValues(e)
		},
		
		_onEditContactPerson: function(ev) {
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			this.edit_contact_person_popup(post, $form, ev);
		},
		
		edit_contact_person_popup: function(post, $form, ev) {
			var self = this;
			$('#vp_page_loading').show();
			var partner_id = $(ev.currentTarget).attr('id');
			post['partner_id'] = partner_id;
			ajax.jsonRpc('/view_profile/edit_office_address', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				$('#vp_page_loading').hide();
				//self._onChange_Site_Address();
				self._onChange_Site_Address_Field();
				$modal.on('click', '.is-invalid', function(ev){
					$(this).removeClass('is-invalid');
				});
				$modal.on('click', '#head_office_close_btn', function(ev){
	   		    	self.save_edit = false;
	   		    });
			});
		},
		
		// affiliated address
	
		_onAddAffiliatedCompany: function(ev) {
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			this.add_affiliated_compnay_popup(post, $form, ev);
		},
	
		add_affiliated_compnay_popup: function(post, $form, e) {
			var self = this;
			ajax.jsonRpc('/view_profile/new_affiliated_contact_popup', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				$modal.on('click', '.is-invalid', function(ev){
					$(this).removeClass('is-invalid');
				});
			});
		},
	
		_onEditAffiliatedContact: function(ev) {
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			this.edit_affiliated_contact_popup(post, $form, ev);
		},
	
		edit_affiliated_contact_popup: function(post, $form, ev) {
			var self = this;
			var partner_id = $(ev.currentTarget).attr('id');
			post['partner_id'] = partner_id;
			ajax.jsonRpc('/view_profile/edit_affiliated_contact', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				$modal.on('click', '.is-invalid', function(ev){
					$(this).removeClass('is-invalid');
				});
			});
		},
		
		_onAddSiteOffice: function(ev) {
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			this.add_site_address_popup(post, $form, ev);
		},

		add_site_address_popup: function(post, $form, e) {
			var self = this;
			$('#vp_page_loading').show();
			ajax.jsonRpc('/view_profile/new_site_address_popup', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				$modal.on('click', '.is-invalid', function(ev){
					$(this).removeClass('is-invalid');
				});
				$('#vp_page_loading').hide();
				//self._onChange_Site_Address(); // on change Address
				self._onChange_Site_Address_Field();
			});
		},

		_onDeletePartner: function(e) {
			var post = {};
			var partner_id = $(e.currentTarget).attr('id');
			post['partner_id'] = partner_id;
			var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			var table_name = $(e.currentTarget).closest('table').attr('name');
			var table = document.getElementsByName(table_name);
			var row_id = document.getElementById(partner_id);
			new Dialog(this, {
	            title: _t("Confirmation"),
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
						ajax.jsonRpc('/view_profile/delete_partner', 'call', post).then(function(result) {
							if(row_id){
								var rowIndex = row_id.rowIndex;
								if(rowIndex){
									table[0].deleteRow(rowIndex);
									var row_lenth = table[0].rows.length;
									if(row_lenth == 1){
										var td_length = table[0].rows[0].cells.length;
											var tbodyRef = table[0].getElementsByTagName('tbody')[0];
									  		// Insert a row at the end of table
											var newRow = tbodyRef.insertRow();
											newRow.classList.add("empty-row-height");
											newRow.setAttribute("id","site_empty_row");
											for (var i = 0; i < td_length; i++) {
											  	// Insert a cell at the end of the row
												var newCell = newRow.insertCell();
										  	}
								}
								
							}	
						}
					});
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
		},
		
		_onContactDeletePartner: function(e) {
			var post = {};
			var partner_id = $(e.currentTarget).attr('id');
			post['partner_id'] = partner_id;
			var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			var table_name = $(e.currentTarget).closest('table').attr('name');
			var table = document.getElementsByName(table_name);
			var row_id = document.getElementById(partner_id);
			new Dialog(this, {
	            title: _t("Confirmation"),
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
						ajax.jsonRpc('/view_profile/delete_partner', 'call', post).then(function(result) {
							if(row_id){
								var rowIndex = row_id.rowIndex;
								if(rowIndex){
									table[0].deleteRow(rowIndex);
									var row_lenth = table[0].rows.length;
									if(row_lenth == 1){
										var td_length = table[0].rows[0].cells.length;

											var tbodyRef = table[0].getElementsByTagName('tbody')[0];
									  		// Insert a row at the end of table
											var newRow = tbodyRef.insertRow();
											newRow.classList.add("empty-row-height");
											newRow.setAttribute("id","contact_empty_row");
											for (var i = 0; i < td_length; i++) {
											  	// Insert a cell at the end of the row
												var newCell = newRow.insertCell();
										  	}

								}
								
							}	
						}
					});
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
		},
		
		_onDeleteAffiliatedContact: function(e) {
			var post = {};
			var partner_id = $(e.currentTarget).attr('id');
			post['partner_id'] = partner_id;
			var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			var table_name = $(e.currentTarget).closest('table').attr('name');
			var table = document.getElementsByName(table_name);
			var row_id = document.getElementById(partner_id);
			new Dialog(this, {
	            title: _t("Confirmation"),
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
	                   ajax.jsonRpc('/view_profile/delete_affiliated_contact', 'call', post).then(function(result) {
						if(row_id){
							var rowIndex = row_id.rowIndex;
							if(rowIndex){
								table[0].deleteRow(rowIndex);
								var row_lenth = table[0].rows.length;
								if(row_lenth == 1){
									var td_length = table[0].rows[0].cells.length;
									var tbodyRef = table[0].getElementsByTagName('tbody')[0];
							  		// Insert a row at the end of table
									var newRow = tbodyRef.insertRow();
									newRow.classList.add("empty-row-height");
									newRow.setAttribute("id","affiliated_empty_row");
									for (var i = 0; i < td_length; i++) {
									  	// Insert a cell at the end of the row
										var newCell = newRow.insertCell();
								  	}
								}
								
							}	
						}
					});
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
		},
		
		// Product service
	
		_onAddProductService: function(ev) {
			var post = {};
			var $form = $('.vpro_product_service_panel');
			post['id'] = $(ev.currentTarget).attr('id');
			this.add_product_service_popup(post, $form);
		},

		add_product_service_popup: function(post, $form) {
			var self = this;
			ajax.jsonRpc('/view_profile/new_product_service_popup', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				self._product_product_attach();
				profile_product_form_widget.pro_attach_file_list = [];
				$modal.on('click', '.required_style', function(ev){
					$(this).removeClass('required_style');
				});
				$('#product_attach_fileList li').each(function(){
					profile_product_form_widget.pro_attach_file_list.push({
							'file_name': $(this).attr('data'),
							'file_content': $(this).attr('file_data'),
							'att_id': $(this).attr('id')
					});
				});
				$(".remove-list").off().on('click', function(){
					var file_name = $(this).parent('li').attr('data');
					profile_product_form_widget.pro_attach_file_list = profile_product_form_widget.pro_attach_file_list.filter((el) => {
						return el.file_name !== file_name;
					});
				});
				$modal.on('click', '#ps_offered_save', function(ev){
					$('#vp_page_loading').show();
					var self = $(this)
					var values = {}
					var mandatory = false;
					var save_action = $(this).attr('action');
					var file_attch = false;
					$('.new_product_form_popup input').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name'))
							values[$(this).attr('name')] = $(this).val();
								
					});
					$('.new_product_form_popup textarea').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name'))
							values[$(this).attr('name')] = $(this).val();
					});
					
					$('.new_product_form_popup select').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name') == 'product_classification_id' || $(this).attr('name') == 'uom_id'){
							values[$(this).attr('name')] = parseInt($(this).val());
						}
					});
					var price_mandatory = false;
					var price = $('#p_price').val()
					if(price && !mandatory){
						price = parseFloat(price)
						if(price <= 0){
							$('#p_price').addClass('required_style');
							mandatory = true;
							price_mandatory = true;
						}
					}
					/** Get attachment details */
					var file_details = profile_product_form_widget.pro_attach_file_list;
					if (file_details.length >0){
						file_attch = true;
					}
					var img_data = $('.new_product_form_popup').find('.vproducts-pic').attr('img_data');

					if(img_data != undefined){
						var data_jpeg = img_data.replace("data:image/jpeg;base64,", "")
				        var data_png = data_jpeg.replace("data:image/png;base64,", "")
				        var data = data_png.replace("data:image/jpg;base64,", "")
						var image_1920 = data;
						var img_attached = true;
					}
					if(img_data == undefined){
						var image_1920 = '';
						var img_attached = false;
					}
					
					if(!mandatory){
						var save_post = {'datas': values,
										'partner_id': $(this).attr('partner_id'),
										'pro_id': $(this).attr('ps_id'),
										'pro_files': file_details,
										'file_attch': file_attch,
										'image_1920': image_1920,
										'img_attached': img_attached,
										}
						ajax.jsonRpc(save_action, 'call', save_post).then(function (modal){
							if(parseInt(self.attr('ps_id')) > 0){
								$('#pro_line'+self.attr('ps_id')).replaceWith(modal)
							}else{
								$('#product_empty_row').before(modal)
								var row = $('.po_service_table tbody tr').length - 1;
								var last_row = $('.po_service_table tbody tr:last').prev();
								var last_td = last_row.find('td:last').removeClass('v_display_none');
								if(row>=1){
			  		    			$('.po_service_table tr#product_empty_row').addClass('v_display_none');
			  		    		}
							}
							$modal.empty();
						    $modal.modal('hide');
						    $('.product_service_popup').remove();
							$('#vp_page_loading').hide();
						});
					}else{
						$('#vp_page_loading').hide();
						if(price_mandatory){
							price = parseFloat(price)
							if(price <= 0){
								alertify.alert('Message','Price should be greater than 0.'); 
							}
						}else{
							alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
						}
						return false;
					}
				});
				$modal.on('click', '#profile_ps_offered_close', function(ev){
					$modal.empty();
				    $modal.modal('hide');
				    $('.product_service_popup').remove();
				});
			});
		},
		_product_product_attach:function(){
		 	var self = this;
		 	/* image attach Start*/
		 	var readURL = function(input) {
		        if (input.files && input.files[0]) {
					var size = parseFloat(input.files[0].size / 1024).toFixed(2)
					if(size <= 5000){
			            var reader = new FileReader();
	
			            reader.onload = function (e) {
			                $('.vproducts-pic').attr('src', e.target.result);
			                $('.vproducts-pic').attr('img_data', e.target.result )
			            }
			    
			            reader.readAsDataURL(input.files[0]);
					}else{
						alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
					}
		        }
		    }
		    $(".vpro-pic-upload").off().on('change', function(){
		        readURL(this);
		    });
		    
		    $(".vproduct_attach_icon").off().on('click', function() {
		       $(".vpro-pic-upload").click();
		    });
		    /* image attach Start*/

		    /* file attach Start*/
		   $(".product_attach_input").off().on('change', function(){
			   var output = document.getElementById('product_attach_fileList');
     			var children = "";
				_.map($(".product_attach_input")[0].files, function (file) {
						var size = parseFloat(file.size / 1024).toFixed(2)
						if(size <= 5000){
							var reader = new FileReader();
							children +=  '<li id="0" data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
							reader.onload = function (e) {
							self.pro_attach_file_list.push({
								'file_name': file.name,
								'file_content': e.target.result,
								'att_id': 0
							});
							$(".remove-list").off().on('click', function(){
								var file_name = $(this).parent('li').attr('data');
								self.pro_attach_file_list = self.pro_attach_file_list.filter((el) => {
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
		    
		    $(".product_attach_upload").off().on('click', function() {
		       $(".product_attach_input").click();
		    });

		    /* file attach end*/
		},
		_onEditProductService: function(ev) {
			var post = {};
			var $form = $(ev.currentTarget).closest('form');
			this.edit_product_service_popup(post, $form, ev);
		},
	
		edit_product_service_popup: function(post, $form, ev) {
			var self = this;
			var ps_id = $(ev.currentTarget).attr('id');
			post['ps_id'] = ps_id;
			ajax.jsonRpc('/view_profile/edit_product_service', 'call', post).then(function(modal) {
				var $modal = $(modal);
				$modal.appendTo($form).modal();
				self._product_product_attach();
				profile_product_form_widget.pro_attach_file_list = [];
				$modal.on('click', '.required_style', function(ev){
					$(this).removeClass('required_style');
				});
				$('#product_attach_fileList li').each(function(){
					profile_product_form_widget.pro_attach_file_list.push({
							'file_name': $(this).attr('data'),
							'file_content': $(this).attr('file_data'),
							'att_id': $(this).attr('id')
					});
				});
				$(".remove-list").off().on('click', function(){
					var file_name = $(this).parent('li').attr('data');
					profile_product_form_widget.pro_attach_file_list = profile_product_form_widget.pro_attach_file_list.filter((el) => {
						return el.file_name !== file_name;
					});
				});
				$modal.on('click', '#ps_offered_save', function(ev){
					$('#vp_page_loading').show();
					var self = $(this)
					var values = {}
					var mandatory = false;
					var save_action = $(this).attr('action');
					var file_attch = false;
					$('.new_product_form_popup input').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name'))
							if($(this).attr('name') == 'product_classification_id' || $(this).attr('name') == 'uom_id'){
								values[$(this).attr('name')] = parseInt($(this).val());
							}
							else{
								values[$(this).attr('name')] = $(this).val();
							}
								
					});
					$('.new_product_form_popup textarea').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name'))
							values[$(this).attr('name')] = $(this).val();
					});
					
					$('.new_product_form_popup select').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('required_style')
						}
						if($(this).attr('name') == 'product_classification_id' || $(this).attr('name') == 'uom_id'){
							values[$(this).attr('name')] = parseInt($(this).val());
						}
					});
					var price = $('#p_price').val()
					var price_mandatory = false;
					if(price && !mandatory){
						price = parseFloat(price)
						if(price <= 0){
							$('#p_price').addClass('required_style');
							mandatory = true;
							price_mandatory = true;
						}
					}

					/** Get attachment details */
					var file_details = profile_product_form_widget.pro_attach_file_list;
					if (file_details.length >0){
						file_attch = true;
					}
					var img_data = $('.new_product_form_popup').find('.vproducts-pic').attr('img_data');
					if(img_data != undefined){
						var data_jpeg = img_data.replace("data:image/jpeg;base64,", "")
				        var data_png = data_jpeg.replace("data:image/png;base64,", "")
				        var data = data_png.replace("data:image/jpg;base64,", "")
						var image_1920 = data;
						var img_attached = true;
					}
					if(img_data == undefined){
						var image_1920 = '';
						var img_attached = false;
					}
					if(!mandatory){
						var prow_id = $(this).attr('ps_id');
						var save_post = {'datas': values,
										'partner_id': $(this).attr('partner_id'),
										'pro_id': $(this).attr('ps_id'),
										'pro_files': file_details,
										'file_attch': file_attch,
										'image_1920': image_1920,
										'img_attached': img_attached,
										}
						ajax.jsonRpc(save_action, 'call', save_post).then(function (modal){
							if(parseInt(prow_id) > 0){
								$('.po_service_table tbody').find('tr#pro_line'+prow_id).replaceWith(modal)
							}
							$modal.empty();
						    $modal.modal('hide');
						    $('.product_service_popup').remove();
							$('#vp_page_loading').hide();
						});
					}else{
						$('#vp_page_loading').hide();
						var price = $('#p_price').val()
						if(price_mandatory){
							var price = parseFloat(price)
							if(price <= 0){
								alertify.alert('Message','Price should be greater than 0.'); 
							}
						}else{
							alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
						}
						return false;
					}
				});
				$modal.on('click', '#profile_ps_offered_close', function(ev){
					$modal.empty();
				    $modal.modal('hide');
				    $('.product_service_popup').remove();
				});
			});
		},
		/**
		 * @private
		 * @param {Object} ev
         * Delete the PO Delivery Line
		 */
		_onView_product_photo: function(ev){
			var id = $(ev.currentTarget).attr('ps_id');
			var post = {'ps_id': id}
			var $form = $('.vpro_product_service_panel');
			 if(parseInt(id)>0){
				 ajax.jsonRpc('/view/product_photo', 'call', post).then(function (modal) { 
						var $modal = $(modal);			
			  		    $modal.appendTo($form).modal();	
			  		    $modal.on('click', '#ps_photo_close', function(ev){
			   		    	$modal.empty();
					    	$modal.modal('hide');
					    	$('.product_photo_view_popup').remove();
			   		    });
				 });
			 }
		},
		
		/**
		 * @private
		 * @param {Object} ev
         * Delete the PO Delivery Line
		 */
		_onDeleteProductService: function(ev){
			var id = $(ev.currentTarget).attr('id');
			var action = $(ev.currentTarget).attr('action');
			var post = {'id': id}
			var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			var table = $(ev.currentTarget).closest('table');	
			var tr = $(ev.currentTarget).closest('tr');
	  		new Dialog(this, {
	            title: _t("Confirmation"),
	            size: 'medium',
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
	                	ajax.jsonRpc(action, 'call', post).then(function (result){
	  						tr.remove();
	  						var row = $('.product_service_ids tbody tr').length;
	  						if(row==1){
			  		    		$('.product_service_ids tr#empty_product').removeClass('v_display_none');
			  		    	}
	                	});
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
		},

    	_onSiteAddressSave: function (ev) {
			this.sendFormValues(ev);
        },
        
        _onContactPersonSave: function (ev) {
			this.sendFormValues(ev);
        },
        
        _onAffiliatedSave: function (ev) {
			this.sendFormValues(ev);
        },

        updateInlineEditValues: function (e, form_values) {
        	var self = this;
            e.preventDefault();  // Prevent the default submit behavior
			self.postFormValues(e, form_values)
        },
		
		/*Start Header fields save*/
		postFormValues: function (e, form_values) {
         	var self = this;
          	// Post form and handle result
            ajax.post(this.$target.attr('action') + (this.$target.data('force_action')||this.$target.data('model_name')), form_values)
            .then(function (result_data) {
                result_data = JSON.parse(result_data);
                if (!result_data.id) {
                    // Failure, the server didn't return the created record ID
                    self.update_status('error', e);
                    if (result_data.error_fields) {
                        // If the server return a list of bad fields, show these fields for users
                        self.check_error_fields(result_data.error_fields);
                    }
                } else {
                    // Success, redirect or update status
                    var success_page = self.$target.attr('data-success_page');
                    if (success_page) {
                        $(window.location).attr('href', success_page);
                    }
                    else {
                        self.update_status('success', e);
                        if(result_data.comment){
							self.$('#comment').text(result_data.comment)
						}

						self.$('.email_row_edit').removeClass('d-none');
						self.$('.email_row_save').addClass('d-none');
		
						self.$('.mobile_row_edit').removeClass('d-none');
						self.$('.mobile_row_save').addClass('d-none');
						
						self.$('.phone_row_edit').removeClass('d-none');
						self.$('.phone_row_save').addClass('d-none');
						
						self.$('.website_row_edit').removeClass('d-none');
						self.$('.website_row_save').addClass('d-none');
						
						self.$('.email_span').text(result_data.email)
						
						if(result_data.mobile){
							self.$('.mobile_span').text(result_data.mobile)
						}
						
						if(result_data.phone){
							self.$('.phone_span').text(result_data.phone);
						}
						
						if(result_data.website){
							self.$('.website_span').text(result_data.website)
						}
                    }
                }
            })
            .guardedCatch(function (){
                self.update_status('error', e);
            });
		},
        /*End Header fields save*/
        
        setRFQLineValues: function (e) {
        	var current_form = $(e.currentTarget).closest('form');
            e.preventDefault();  // Prevent the default submit behavior
            var self = this;
            current_form.find('#o_website_form_result').empty();
            if (!self.check_error_fields({}, e)) {
                self.update_status('invalid', e);
				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
                return false;
            }
             // Prepare form inputs
            this.form_fields = current_form.serializeArray();
            $.each(current_form.find('input[type=file]'), function (outer_index, input) {
                $.each($(input).prop('files'), function (index, file) {
                    // Index field name as ajax won't accept arrays of files
                    // when aggregating multiple files into a single field value
                    self.form_fields.push({
                        name: input.name + '[' + outer_index + '][' + index + ']',
                        value: file
                    });
                });
            });

            // Serialize form inputs into a single object
            // Aggregate multiple values into arrays
            var form_values = {};
            _.each(this.form_fields, function (input) {
                if (input.name in form_values) {
                    // If a value already exists for this field,
                    // we are facing a x2many field, so we store
                    // the values in an array.
                    if (Array.isArray(form_values[input.name])) {
                        form_values[input.name].push(input.value);
                    } else {
                        form_values[input.name] = [form_values[input.name], input.value];
                    }
                } else {
                    if (input.value !== '') {
                        form_values[input.name] = input.value;
                    }
                }
            });
            this.rfq_edited_vals[form_values.rfq_mail_id] = form_values
            this.rfq_line_datas_edited = this.rfq_edited_vals
	        var rfq_line_id = e.currentTarget.id;
			var unit_price = $(e.currentTarget).closest('form').find("#unit_price").val();
			var gross_total = $(e.currentTarget).closest('form').find("#gross_total").val();
			var delivery_lead_time = $(e.currentTarget).closest('form').find("#delivery_lead_time").val();
			var delivery_cost = $(e.currentTarget).closest('form').find("#delivery_cost").val();
			var warranty = $(e.currentTarget).closest('form').find("#warranty").val();
			var minimum_order_qty = $(e.currentTarget).closest('form').find("#minimum_order_qty").val();
			var terms = $(e.currentTarget).closest('form').find("#terms").val();
			var validity_from = $(e.currentTarget).closest('form').find(".validity_quote_from_cls").val();
			var validity_to = $(e.currentTarget).closest('form').find(".validity_quote_to_cls").val();
			var validity_of_quote = validity_from + " - "+ validity_to
			$('#myRrqTable').find('tr#'+rfq_line_id).find('.unit_price').html(unit_price);
			$('#myRrqTable').find('tr#'+rfq_line_id).find('.gross_total').html(gross_total);
		  	$('#myRrqTable').find('tr#'+rfq_line_id).find('.delivery_lead_time').html(delivery_lead_time);
		  	$('#myRrqTable').find('tr#'+rfq_line_id).find('.delivery_cost').html(delivery_cost);
		  	$('#myRrqTable').find('tr#'+rfq_line_id).find('.minimum_order_qty').html(minimum_order_qty);
		 	$('#myRrqTable').find('tr#'+rfq_line_id).find('.warranty').html(warranty);
		   	$('#myRrqTable').find('tr#'+rfq_line_id).find('.terms').html(terms);
		 	$('#myRrqTable').find('tr#'+rfq_line_id).find('.validity_of_quote').html(validity_of_quote);
			$('#myRrqTable').find('tr#'+rfq_line_id).find('.validity_from').html(validity_from);	
			$('#myRrqTable').find('tr#'+rfq_line_id).find('.validity_to').html(validity_to);	
				$('.modal').empty();
			    $('.modal').modal('hide');
			    $('#modal_rfq_line').remove();
				$('.modal-backdrop').remove();
				// To resolve scroll not added issue after close the popup
				document.body.classList.remove('modal-open');
	        },
  
   		_uploadfile:function(){
		 	/* image attach Start*/
		 	var readURL = function(input) {
		        if (input.files && input.files[0]) {
					var size = parseFloat(input.files[0].size / 1024).toFixed(2)
					if(size <= 5000){
			            var reader = new FileReader();
			            reader.onload = function (e) {
			                $('.product-pic').attr('src', e.target.result);
			                $('.product-pic').attr('img_data', e.target.result )
			            }
			            reader.readAsDataURL(input.files[0]);
					}else{
						alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
					}
		        }
		    }
		    $(".pro-pic-upload").off().on('change', function(){
		        readURL(this);
		    });
		    
		    $(".product_attach_icon").off().on('click', function() {
		       $(".pro-pic-upload").click();
		    });
		    /* image attach Start*/
		    /* file attach Start*/
		    var readFileURL = function(input) {
		        if (input.files && input.files[0]) {
					var size = parseFloat(input.files[0].size / 1024).toFixed(2)
					if(size <= 5000){
			        	var file = input.files[0];
			        	$('.product_file').text(file.name);
			        	$('.pro_attach_p').addClass('d-none');
			        	$('.attach_delete').removeClass('d-none');
			            var reader = new FileReader();
			            reader.onload = function (e) {
			            	$('.product_file').attr('file_data', e.target.result)
			            }
			            reader.readAsDataURL(input.files[0]);
					}else{
						alertify.alert('Message', 'File size exceeds. It should not be more than 5MB.')
					}
		        }
		    }
		   $(".product_file_input").off().on('change', function(){
		        readFileURL(this);
		    });
		    
		    $(".pro_file_upload").off().on('click', function() {
		       $(".product_file_input").click();
		    });
		    
		    // Delete uploaded file
		    $(".attach_delete").off().on('click', function() {
		    	$('.attach_delete').addClass('d-none');
	        	$('.pro_attach_p').removeClass('d-none');
	        	$('.product_file').removeAttr("file_data");
	        	$('.product_file').text('');
	        	$('.product_file_input').val(null);
			});
		    
		    /* file attach end*/
		    
		    /* Allow number value in price */
			$(".vinput_price").on('keydown keyup paste input',function(e) {
			    // between 0 and 9    		
				if(e.which!=8 && e.which!=0)
			    {if (e.which < 48 || e.which > 57) {
			        return(false);  // stop processing
			    }}
			});
	 },
    });
	
	    var pay_attch_file_list = []
		// Upload button click
		$(".pay_file_upload").off().on('click', function() {
			var btn_type = $('.edit_or').attr('btn_type')
			if (btn_type == 'save_or'){
		       $(".payment_attach_input").click();
			}
		});
		$(".payment_attach_input").off().on('change', function(){
			var output = document.getElementById('payment_attach_fileList');
				var children = "";
				_.map($(".payment_attach_input")[0].files, function (file) {
						var size = parseFloat(file.size / 1024).toFixed(2)
						if(size <= 5000){
							var reader = new FileReader();
							children +=  '<li id="0" data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
							reader.onload = function (e) {
								pay_attch_file_list.push({
								'file_name': file.name,
								'file_content': e.target.result,
								'att_id': 0
							});
							$(".remove-list").off().on('click', function(){
								var file_name = $(this).parent('li').attr('data');
								pay_attch_file_list = pay_attch_file_list.filter((el) => {
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
	/** Payment Edit and save action **/
	$('.edit_or').on('click', function(){
	      var details = {}
		  var btn = document.getElementById('payment_edit');
	      btn.enable = true;
	      btn.innerText = 'Save OR'
	      var btn_type = $(this).attr('btn_type')
	      if (btn_type == 'edit_or'){
	    	  $(this).attr('btn_type','save_or');
	    	  $('.pedit_span').addClass('d-none');
	    	  $('.pedit_input').removeClass('d-none');
	    	  $('.payment_uploaddiv').removeClass('d-none');
	    	  /**
				* <!-- START Set Date Format for date fields from Odoo Language settings
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
				$('#or_date').off().on('click', function(){
					$('input[data-target="#or_date"]').each(function(){
						$(this).removeClass('required_style')
					})
			    })
				/**
				* Set Date Format for date fields from Odoo Language settings END --> 
				**/
	      }
	      else{
		    	var payment_id = $('.payment_id_details').attr('paymentid')
		    	var values = {}
		    	$('.my_payment_form input').each(function(){
					if($(this).attr('required') && !$(this).val()){
						mandatory = true;
						$(this).addClass('required_style')
					}
					if($(this).attr('name')){
						if($(this).attr('name') == 'amount'){
							if($(this).val()){
								values[$(this).attr('name')] = parseFloat($(this).val());
							}else{
								values[$(this).attr('name')] = '';
							}
						}else{
							values[$(this).attr('name')] = $(this).val();
						}
					}
						
				});
		    	values['remark'] = $('.pay_remark').val();
		    	/** Get attachment details */
				var file_details = pay_attch_file_list;
		    	var save_post = {'datas': values,
								'pay_id': payment_id,
								'pay_files': file_details,
								}
				ajax.jsonRpc('/save/edit_or', 'call', save_post).then(function (modal){
					window.location.reload();
				});
	      }
	        	
	});
	

});
