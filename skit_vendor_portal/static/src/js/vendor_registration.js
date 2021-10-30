odoo.define('skit_vendor_portal.vendor_registration', function (require) {
'use strict';
var core = require('web.core');
var ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
var Dialog = require('web.Dialog');
var _t = core._t;
var product_form_widget;

publicWidget.registry.VendorRegistrationForm = publicWidget.Widget.extend({
    selector: '.vendor_registration_form',
    events: {
    	'click .site_plus': '_onAddSiteAddress',
    	'click .contact_plus': '_onAdd_ContactPerson',
    	'click .affiliated_contact_plus': '_onAdd_AffiliatedContact',
    	'click .product_service_plus': '_onAdd_Product_Service',
        'change select[name="country_id"]': '_onCountryChange',
        'change select[name="state_id"]': '_onStateChange',
        'change select[name="province_id"]': '_onProvinceChange',
        'change select[name="city_id"]': '_onCityChange',
        'click .vregister_form': '_Vendor_confirmation',
        'click .site_edit': '_onEdit_siteaddress',
        'click .site_delete': '_onDelete_siteaddress',
        'click .contact_edit': '_onEdit_contact',
        'click .contact_delete': '_onDelete_contact',
        'click .company_edit': '_onEdit_affiliated',
        'click .company_delete': '_onDelete_affiliated',
        'click .product_edit': '_onEdit_product',
        'click .product_delete': '_onDelete_product',
        'click .product_photo_view': '_onView_product_photo',
        'click .vinput': '_onClick_input',
        'click .accept_privacy_policy': '_onAcceptPrivacyPolicy',
        'click .accept_terms_and_condition': '_onAcceptTermsCondition',
        'click #agree': '_onClickAgree',
        'click .prod_file_view': '_on_click_file_view',
        'click .show_attachment_view': '_showMultiAttachPopup',
        'click .product_import_button': '_onProduct_Import',
        'click .attachCatalogue': '_onAttachCatalogueButtonClick',
		'click .pc_checkbox_input, .others_category_input': '_removeCheckWarning'

    },

    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        
        this.$state = this.$('select[name="state_id"]');
        this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');
        
        this.$province = this.$('select[name="province_id"]');
        this.$provinceOptions = this.$province.filter(':enabled').find('option:not(:first)');
        
        this.$city = this.$('select[name="city_id"]');
        this.$cityOptions = this.$city.filter(':enabled').find('option:not(:first)');
            
        this.$barangay = this.$('select[name="barangay_id"]');
        this.$barangayOptions = this.$barangay.filter(':enabled').find('option:not(:first)');
        
        //this._adaptAddressForm();
        this._block_aplhabets();
		this.brocher_file_list = []; 
		product_form_widget = this;
		this.product_attch_file_list = [];
        return def;
    },
	_removeCheckWarning: function(){
		$('.vendor_product_category').removeClass('waring');
	},
    /*** Catalogue button on click - Starts ***/
	_onAttachCatalogueButtonClick: function () {
		 	// import product file
			var self = this;
		 	$(".v_cbrochure_file_input").click();
		 	// Read upload file
		    $(".v_cbrochure_file_input").off().on('change', function(){
				var output = document.getElementById('brocherfileList');
      			var children = "";
				console.log($(".v_cbrochure_file_input")[0].files.length)
				_.map($(".v_cbrochure_file_input")[0].files, function (file) {
						var size = parseFloat(file.size / 1024).toFixed(2)
						if(size <= 5000){
							var reader = new FileReader();
							children +=  '<li data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
				            reader.onload = function (e) {
							self.brocher_file_list.push({
								'file_name': file.name,
								'file_content': e.target.result,
							});
							$(".remove-list").off().on('click', function(){
								console.log($(this).parent('li').attr('data'));
								var file_name = $(this).parent('li').attr('data');
								self.brocher_file_list = self.brocher_file_list.filter((el) => {
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

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
    /*** Add SiteAddress  ***/
    _onAddSiteAddress: function(ev){
    	ev.preventDefault();
    	var self = this;
    	var post = {};
    	var $form = $('.vso_address_panel');
    	self.site_address_popup(post, $form);
    },
    site_address_popup: function(post, $form){
		$('#vp_page_loading').show();
    	 var self = this;
    	 post['s_name']= '';
		 post['street']= '';
		 post['street2']= '';
		 post['state_id']= 0;
		 post['province_id']= 0;
		 post['city_id']= 0;
		 post['zip_code']= '';
		 post['barangay_id']= 0;
		 post['country_id']= 0;
	   	 ajax.jsonRpc('/site_address/creation', 'call', post).then(function (modal) { 
					$('#vp_page_loading').hide();
					var $modal = $(modal);
					$modal.appendTo($form).modal();	
					self._block_aplhabets(); // block alphabets		
					//self._onChange_Site_Address(); // on change Address
					self._onChange_Site_Address_Field();
					$modal.on('click', '.waring', function(ev){
						$(this).removeClass('waring');
					});
					$modal.on('click', '#site_save', function(ev){
						var self = $(this)
			  			var mandatory = false
			  			var values = {}
						var crow = $('.site_office_ids tbody tr').length;
						$('.site_form_popup input').each(function(){
							if($(this).attr('required') && !$(this).val()){
								mandatory = true;
								$(this).addClass('waring');
							}
							if($(this).attr('name'))
								values[$(this).attr('name')] = $(this).val();
						});
						
						$('.site_form_popup select').each(function(){
							if($(this).attr('required') && !$(this).val()){
								mandatory = true;
								$(this).addClass('waring');
							}
							if($(this).attr('name') == 'site_country_id' || 
									$(this).attr('name') == 'site_state_id' ||
									$(this).attr('name') == 'site_province_id' ||
									$(this).attr('name') == 'site_city_id' ||
									$(this).attr('name') == 'site_barangay_id'){
								values[$(this).attr('name')] = parseInt($(this).val());
							}
						});
						values['count'] = crow;
						if(!mandatory){
							var datas = {'datas': values}
							ajax.jsonRpc('/new/row/siteaddress', 'call', datas).then(function (modal) { 
			  		    		$('.site_office_ids tr#empty_site').before(modal);
			  		    		var row = $('.site_office_ids tbody tr').length - 1;
			  		    		if(row>=1){
			  		    			$('.site_office_ids tr#empty_site').addClass('v_display_none');
			  		    		}
			  		    	});
			  		    	$modal.empty();
			  				$modal.modal('hide');
			  				$('.site_address_popup').remove();
		  		    	}
						else{
			  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
	     				     return false;
		  		    	}
					});
		   		    $modal.on('click', '#site_close', function(ev){
		   		    	$modal.empty();
				    	$modal.modal('hide');
				    	$('.site_address_popup').remove();
		   		    });
				});
    },
    _onDelete_siteaddress:function(e){
  	 	/** Delete site address row */
	  	var row_id = $(e.currentTarget).closest('tr').attr('id');
	  	if(row_id != 'empty_site'){
	  		var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			new Dialog(this, {
	            title: _t("Confirmation"),
	            size: 'medium',
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
	                	var table = $(e.currentTarget).closest('table');	
  						var tr = $(e.currentTarget).closest('tr');
  						tr.remove();
		  		    	var row = $('.site_office_ids tbody tr').length;
  						if(row==1){
		  		    		$('.site_office_ids tr#empty_site').removeClass('v_display_none');
		  		    	}
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
	  	}
  }, 
  _onEdit_siteaddress:function(e){
	 	/** Delete site address row */
	  	var self = this;
	  	var row_id = $(e.currentTarget).closest('tr').attr('id');
	  	if(row_id != 'empty_site'){
	  		var s_name = $(e.currentTarget).closest('tr').find('.s_name').text();
			var s_street = $(e.currentTarget).closest('tr').find('.s_street').text();
			var s_street2 = $(e.currentTarget).closest('tr').find('.s_street2').text();
			var s_barangay_id = $(e.currentTarget).closest('tr').find('.s_barangay_id').attr('barangay_id');
			var s_city_id = $(e.currentTarget).closest('tr').find('.s_city_id').attr('city_id');
			var s_province_id = $(e.currentTarget).closest('tr').find('.s_province_id').attr('province_id');
			var s_state_id = $(e.currentTarget).closest('tr').find('.s_state_id').attr('state_id');
			var s_country_id = $(e.currentTarget).closest('tr').find('.s_country_id').attr('country');
			var s_zipcode = $(e.currentTarget).closest('tr').find('.s_zipcode').text();
			var siteid = $(e.currentTarget).closest('tr').attr('siteid');
			var post = {};
			post['s_name']= s_name;
			post['street']= s_street;
			post['street2']= s_street2;
			post['state_id']= s_state_id;
			post['province_id']= s_province_id;
			post['city_id']= s_city_id;
			post['zip_code']= s_zipcode;
			post['barangay_id']= s_barangay_id;
			post['country_id']= s_country_id;
			var $form = $('.vso_address_panel');
			var crow = $(e.currentTarget).closest('tr').attr('id');

			ajax.jsonRpc('/site_address/creation', 'call', post).then(function (modal) { 
				var $modal = $(modal);			
	  		    $modal.appendTo($form).modal();	
	  		    self._block_aplhabets(); // block alphabets
	  		   // self._onChange_Site_Address(); // on change Address
				self._onChange_Site_Address_Field();
				$modal.on('click', '.waring', function(ev){
					$(this).removeClass('waring');
				});
	  		    $modal.on('click', '#site_save', function(ev){
	  		    	var self = $(this)
		  			var mandatory = false
		  			var values = {}
					$('.site_form_popup input').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('waring')
						}
						if($(this).attr('name'))
							values[$(this).attr('name')] = $(this).val();
					});
					
					$('.site_form_popup select').each(function(){
						if($(this).attr('required') && !$(this).val()){
							mandatory = true;
							$(this).addClass('waring')
						}
						if($(this).attr('name') == 'site_country_id' || 
								$(this).attr('name') == 'site_state_id' ||
								$(this).attr('name') == 'site_province_id' ||
								$(this).attr('name') == 'site_city_id' ||
								$(this).attr('name') == 'site_barangay_id'){
							values[$(this).attr('name')] = parseInt($(this).val());
						}
					});
					values['count'] = crow;
					if(!mandatory){
							var datas = {'datas': values};
							ajax.jsonRpc('/new/row/siteaddress', 'call', datas).then(function (modal) { 
								$('.site_office_ids tbody').find('tr#'+crow).replaceWith(modal);
								$('.site_office_ids tbody').find('tr#'+crow).attr('siteid', siteid);
			  		    	});
			  		    	$modal.empty();
			  				$modal.modal('hide');
			  				$('.site_address_popup').remove();
	  		    	}
					else{
		  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
     				     return false;
	  		    	}
	  		    	
	  		    });
	  		    //close action
	  		    $modal.on('click', '#site_close', function(ev){
	   		    	$modal.empty();
			    	$modal.modal('hide');
			    	$('.site_address_popup').remove();
	   		    });
			});
	  	}
	  	else{
	  		var post = {};
	    	var $form = $('.vso_address_panel');
	    	self.site_address_popup(post, $form);
	  	}
  },
 _onChange_Site_Address_Field: function(){
	$(".scountry_id").on('change',function(e) {
		var $s_country = $('select[name="site_country_id"]');
		var country_id =  $s_country.val(); 
		if(country_id){
			var post = {'country_id': country_id,
						'name': 'site_state_id'}
			ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
				$("#sstate_id").html(modal)
				$("#sprovince_id").html('<option value=""></option>');
				$("#scity_id").html('<option value=""></option>');
				$("#sbarangay_id").html('<option value=""></option>');
			});
		}
	});
	$(".sstate_id").on('change',function(e){
		var $s_state = $('select[name="site_state_id"]');
		var state_id =  $s_state.val(); 
		if(state_id){
			var post = {'state_id': state_id,
						'name': 'site_province_id'}
			ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
				$("#sprovince_id").html(modal);
				$("#scity_id").html('<option value=""></option>');
				$("#sbarangay_id").html('<option value=""></option>');
			});
		}
	});
	$(".sprovince_id").on('change',function(e) {
		var $s_province = $('select[name="site_province_id"]');
		var province_id =  $s_province.val(); 
	    if(province_id){
			var post = {'province_id': province_id,
						'name': 'site_city_id'}
			ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
				$("#scity_id").html(modal);
				$("#sbarangay_id").html('<option value=""></option>');
			});
		}
	});
	$(".scity_id").on('change',function(e) {
		var $s_city = $('select[name="site_city_id"]');
		var city_id =  $s_city.val(); 
	    if(city_id){
			var post = {'city_id': city_id,
						'name': 'site_barangay_id'}
			ajax.jsonRpc('/onchange/address', 'call', post).then(function (modal){
				$("#sbarangay_id").html(modal)
			});
		}
	});
 },
  _onChange_Site_Address:function(){
	  var self = this;
	  var $site_state = $('select[name="site_state_id"]');
      var $site_stateOptions = $site_state.filter(':enabled').find('option:not(:first)');

      var $site_province = $('select[name="site_province_id"]');
      var $site_provinceOptions = $site_province.filter(':enabled').find('option:not(:first)');

      var $site_city = $('select[name="site_city_id"]');  
      var $site_cityOptions = $site_city.filter(':enabled').find('option:not(:first)');

      var $site_barangay = $('select[name="site_barangay_id"]');
      var $site_barangayOptions = $site_barangay.filter(':enabled').find('option:not(:first)');

      // Display States
      var $site_country = $('select[name="site_country_id"]');
      var site_countryID = ($site_country.val() || 0);
      $site_stateOptions.detach();
      var $displayedSiteState = $site_stateOptions.filter('[data-country_id=' + site_countryID + ']');
      var nb = $displayedSiteState.appendTo($site_state).show().length;
      $site_state.parent().toggle(nb >= 1);
      
      /*Provice filter based on country*/
      $site_provinceOptions.detach();
      var $displayedSiteProvince = $site_provinceOptions.filter('[data-country_id=' + site_countryID + ']');
      var nb = $displayedSiteProvince.appendTo($site_province).show().length;
      $site_province.parent().toggle(nb >= 1);
      
      /*City filter based on country*/
      $site_cityOptions.detach();
      var $displayedSiteCity = $site_cityOptions.filter('[data-country_id=' + site_countryID + ']');
      var nb = $displayedSiteCity.appendTo($site_city).show().length;
      $site_city.parent().toggle(nb >= 1);
      
      /*Barangay filter based on country*/
      $site_barangayOptions.detach();
      var $displayedSiteBarangay = $site_barangayOptions.filter('[data-country_id=' + site_countryID + ']');
      var nb = $displayedSiteBarangay.appendTo($site_barangay).show().length;
      $site_barangay.parent().toggle(nb >= 1);
      

      // Country on change
	  $(".scountry_id").on('change',function(e) {
		  var $s_country = $('select[name="site_country_id"]');
		  var country_id =  $s_country.val(); 
		  if(country_id){
			  $site_stateOptions.detach();
		      var $displayedSiteState = $site_stateOptions.filter('[data-country_id=' + country_id + ']');
		      var nb = $displayedSiteState.appendTo($site_state).show().length;
		      $site_state.parent().toggle(nb >= 1);
		      
		      /*Provice filter based on country*/
		      $site_provinceOptions.detach();
		      var $displayedSiteProvince = $site_provinceOptions.filter('[data-country_id=' + country_id + ']');
		      var nb = $displayedSiteProvince.appendTo($site_province).show().length;
		      $site_province.parent().toggle(nb >= 1);
		      
		      /*City filter based on country*/
		      $site_cityOptions.detach();
		      var $displayedSiteCity = $site_cityOptions.filter('[data-country_id=' + country_id + ']');
		      var nb = $displayedSiteCity.appendTo($site_city).show().length;
		      $site_city.parent().toggle(nb >= 1);
		      
		      /*Barangay filter based on country*/
		      $site_barangayOptions.detach();
		      var $displayedSiteBarangay = $site_barangayOptions.filter('[data-country_id=' + country_id + ']');
		      var nb = $displayedSiteBarangay.appendTo($site_barangay).show().length;
		      $site_barangay.parent().toggle(nb >= 1);
		  }
	  });
	  // State on change
	  $(".sstate_id").on('change',function(e) {
		  var $s_state = $('select[name="site_state_id"]');
		  var state_id =  $s_state.val(); 
	      if(state_id){
	    	  $site_provinceOptions.detach();
		      var $displayedSiteProvince = $site_provinceOptions.filter('[data-state_id=' + state_id + ']');
		      var nb = $displayedSiteProvince.appendTo($site_province).show().length;
		      $site_province.parent().toggle(nb >= 1);
	      }
	      
	  });
	  // Province on change
	  $(".sprovince_id").on('change',function(e) {
		  var $s_province = $('select[name="site_province_id"]');
		  var province_id =  $s_province.val(); 
	      if(province_id){
	    	  $site_cityOptions.detach();
		      var $displayedSiteCity = $site_cityOptions.filter('[data-province_id=' + province_id + ']');
		      var nb = $displayedSiteCity.appendTo($site_city).show().length;
		      $site_city.parent().toggle(nb >= 1);
	      }
	      
	  });
	  
	  //City on change
	  $(".scity_id").on('change',function(e) {
		  var $s_city = $('select[name="site_city_id"]');
		  var city_id =  $s_city.val(); 
	      if(city_id){
	    	  $site_barangayOptions.detach();
		      var $displayedSiteBarangay = $site_barangayOptions.filter('[data-city_id=' + city_id + ']');
		      var nb = $displayedSiteBarangay.appendTo($site_barangay).show().length;
		      $site_barangay.parent().toggle(nb >= 1);
	      }
	      
	  });
  },
  /*** Ended Add Site Address ***/ 

    /*** Start Add ContactPerson  ***/
    _onAdd_ContactPerson: function(ev){
    	ev.preventDefault();
    	var self = this;
    	var post = {};
    	var $form = $('.vcontact_person_panel');
		$('.contact_person_ids tbody tr[id="empty_contact"] td').each(function(){
			$(this).removeClass('waring');
		});
    	self.contact_person_popup(post, $form);
    },
    contact_person_popup: function(post, $form){
    	 var self = this;
    	 post['c_name']= '';
		 post['c_department']= '';
		 post['c_position']= '';
		 post['c_phone']= '';
		 post['c_mobile']= '';
		 post['c_email']= '';
	   	 ajax.jsonRpc('/contact_person/creation', 'call', post).then(function (modal) { 
					var $modal = $(modal);			
					$modal.appendTo($form).modal();	
					self._block_aplhabets(); // block alphabets
					$modal.on('click', '.waring', function(ev){
						$(this).removeClass('waring');
					});
					$modal.on('click', '#contact_save', function(ev){
						var crow = $('.contact_person_ids tbody tr').length;
						var c_name =  $("#office_name").val();
						var c_department = $("#cdepartment").val();
						var c_position = $("#cposition").val();
						var c_phone = $("#cphone").val();
						var c_mobile = $("#cmobile").val();
						var c_email = $("#cemail").val();

						post['count'] = crow;
						post['c_name']= c_name;
						post['c_department']= c_department;
						post['c_position']= c_position;
						post['c_phone']= c_phone;
						post['c_mobile']= c_mobile;
						post['c_email']= c_email;
						$('.registration_contact_person input').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});

						/*** Validation in Email */
					   	var emailvalidation = self._validateEmail(c_email);
						if(c_name && c_mobile && c_email && emailvalidation){
							ajax.jsonRpc('/new/row/contactperson', 'call', post).then(function (modal) { 
								$('.contact_person_ids tr#empty_contact').before(modal);
			  		    		var row = $('.contact_person_ids tbody tr').length - 1;
			  		    		if(row>=1){
			  		    			$('.contact_person_ids tr#empty_contact').addClass('v_display_none');
			  		    		}
			  		    	});
			  		    	$modal.empty();
			  				$modal.modal('hide');
			  				$('.contact_person_popup').remove();
		  		    	}
						else{
							// Check email validation
							if(c_email !="" && !emailvalidation){
								alertify.alert('Message','Please enter valid email.');
								$("#cemail").addClass('waring')
								return false;
							}
							
			  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
	     				     return false;
		  		    	}
					});
		   		    $modal.on('click', '#contact_close', function(ev){
		   		    	$modal.empty();
				    	$modal.modal('hide');
				    	$('.contact_person_popup').remove();
		   		    });
				});
   },
   _onDelete_contact:function(e){
  	 	/** Delete contactperson row */
	  	var row_id = $(e.currentTarget).closest('tr').attr('id');
	  	if(row_id != 'empty_contact'){
	  		var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
			new Dialog(this, {
	            title: _t("Confirmation"),
	            size: 'medium',
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
	                	var table = $(e.currentTarget).closest('table');	
  						var tr = $(e.currentTarget).closest('tr');
  						tr.remove();
  						var row = $('.contact_person_ids tbody tr').length;
  						if(row==1){
		  		    		$('.contact_person_ids tr#empty_contact').removeClass('v_display_none');
		  		    	}
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
	  	}
  }, 
  _onEdit_contact:function(e){
	  /** Edit affiliated row */
	  	var self= this;
  		var row_id = $(e.currentTarget).closest('tr').attr('id');
		$('.contact_person_ids tbody tr[id="empty_contact"] td').each(function(){
			$(this).removeClass('waring');
		})
		if(row_id != 'empty_contact'){
			var c_name = $(e.currentTarget).closest('tr').find('.c_name').text();
			var c_department = $(e.currentTarget).closest('tr').find('.c_department').text();
			var c_position = $(e.currentTarget).closest('tr').find('.c_position').text();
			var c_phone = $(e.currentTarget).closest('tr').find('.c_phone').text();
			var c_mobile = $(e.currentTarget).closest('tr').find('.c_mobile').text();
			var c_email = $(e.currentTarget).closest('tr').find('.c_email').text();
			var contactid = $(e.currentTarget).closest('tr').attr('contactid');
			var post = {};
			
			post['c_name']= c_name;
			post['c_department']= c_department;
			post['c_position']= c_position;
			post['c_phone']= c_phone;
			post['c_mobile']= c_mobile;
			post['c_email']= c_email;
			var $form = $('.vcontact_person_panel');
			
			var crow = $(e.currentTarget).closest('tr').attr('id');

			ajax.jsonRpc('/contact_person/creation', 'call', post).then(function (modal) { 
				var $modal = $(modal);			
	  		    $modal.appendTo($form).modal();	
	  		  self._block_aplhabets(); // block alphabets
			  $modal.on('click', '.waring', function(ev){
				  $(this).removeClass('waring');
			  });
	  		  $modal.on('click', '#contact_save', function(ev){
					var c_name =  $("#office_name").val();
					var c_department = $("#cdepartment").val();
					var c_position = $("#cposition").val();
					var c_phone = $("#cphone").val();
					var c_mobile = $("#cmobile").val();
					var c_email = $("#cemail").val();

					post['count'] = crow;
					post['c_name']= c_name;
					post['c_department']= c_department;
					post['c_position']= c_position;
					post['c_phone']= c_phone;
					post['c_mobile']= c_mobile;
					post['c_email']= c_email;
					$('.registration_contact_person input').each(function(){
						if($(this).attr('required') && !$(this).val()){
							$(this).addClass('waring');
						}
					});
					/*** Validation in Email */
					var emailvalidation = self._validateEmail(c_email);
					if(c_name && c_mobile && c_email && emailvalidation){
						ajax.jsonRpc('/new/row/contactperson', 'call', post).then(function (modal) { 
							$('.contact_person_ids tbody').find('tr#'+crow).replaceWith(modal);
							$('.contact_person_ids tbody').find('tr#'+crow).attr('contactid', contactid);
		  		    	});
		  		    	$modal.empty();
		  				$modal.modal('hide');
		  				$('.contact_person_popup').remove();
	  		    	}
					else{
						// Check email validation
						if(c_email !="" && !emailvalidation){
							alertify.alert('Message','Please enter valid email.');
							$("#cemail").addClass('waring')
							return false;
						}
		  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
     				     return false;
	  		    	}
	  		    	
	  		    });
	  		    //close action
	  		    $modal.on('click', '#contact_close', function(ev){
	   		    	$modal.empty();
			    	$modal.modal('hide');
			    	$('.contact_person_popup').remove();
	   		    });
			});
		}
		else{
			var post = {};
	    	var $form = $('.vcontact_person_panel');
	    	self.contact_person_popup(post, $form);
		}
  },
  /*** End Add ContactPerson  ***/

   /*** Start Add AffiliatedContact  ***/
   _onAdd_AffiliatedContact: function(ev){
    	ev.preventDefault();
    	var self = this;
    	var post = {};
    	var $form = $('.vaffiliated_contact_panel');
    	self.affiliated_contact_popup(post, $form);
    },
    affiliated_contact_popup: function(post, $form){
    	var self= this;
    	post['name'] = '';
		post['relationship'] = '';
		post['email'] = '';
	   	 ajax.jsonRpc('/affiliated_contact/creation', 'call', post).then(function (modal) { 
					var $modal = $(modal);			
					$modal.appendTo($form).modal();	
					$modal.on('click', '.waring', function(ev){
						$(this).removeClass('waring');
					});
					// Save action
					$modal.on('click', '#affiliated_save', function(ev){
						var crow = $('.affiliated_contact_ids tbody tr').length;
						var aff_name =  $("#affiliat_name").val();
						var aff_relationship = $("#affiliat_relationship").val();
						var aff_email = $("#affiliat_email").val();
						post['count'] = crow;
						post['aff_name'] = aff_name;
						post['aff_email'] = aff_email;
						post['aff_relationship'] = aff_relationship;
						$('.affiliated_div input').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						/*** Validation in Email */
						var emailvalidation = self._validateEmail(aff_email);
						if(aff_name && aff_relationship && aff_email && emailvalidation){
							ajax.jsonRpc('/new/row/affiliated', 'call', post).then(function (modal) { 
			  		    		$('.affiliated_contact_ids tr#empty_affiliat').before(modal);
			  		    		var row = $('.affiliated_contact_ids tbody tr').length - 1;
			  		    		if(row>=1){
			  		    			$('.affiliated_contact_ids tr#empty_affiliat').addClass('v_display_none');
			  		    		}
			  		    		
			  		    	});
			  		    	$modal.empty();
			  				$modal.modal('hide');
			  				$('.affiliated_contact_popup').remove();
		  		    	}
						else{
							// Check email validation
							if(aff_email !="" && !emailvalidation){
								alertify.alert('Message','Please enter valid email.');
								$("#affiliat_email").addClass('waring')
								return false;
							}
			  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
	     				     return false;
		  		    	}
						
					});
					//close action
		   		    $modal.on('click', '#affiliated_close', function(ev){
		   		    	$modal.empty();
				    	$modal.modal('hide');
				    	$('.affiliated_contact_popup').remove();
		   		    });
				});
    },
    _onDelete_affiliated:function(e){
    	/** Delete affiliated row */
    		var row_id = $(e.currentTarget).closest('tr').attr('id');
    		if(row_id != 'empty_affiliat'){
    			var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
    			new Dialog(this, {
    	            title: _t("Confirmation"),
    	            size: 'medium',
    	            $content: $content,
    	            buttons: [
    	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
    	                	var table = $(e.currentTarget).closest('table');	
    						var tr = $(e.currentTarget).closest('tr');
    						tr.remove();
    						var row = $('.affiliated_contact_ids tbody tr').length;
	  						if(row==1){
			  		    		$('.affiliated_contact_ids tbody tr').removeClass('v_display_none');
			  		    	}
    	                }},
    	                {text: _t("Discard"), close: true},
    	            ],
    	        }).open();
    		}
    },
    _onEdit_affiliated:function(e){
    	/** Edit affiliated row */
    	var self = this;
    	var row_id = $(e.currentTarget).closest('tr').attr('id');
		if(row_id != 'empty_affiliat'){
			var aff_name = $(e.currentTarget).closest('tr').find('.affiliated_name').text();
			var aff_relationship = $(e.currentTarget).closest('tr').find('.affiliated_relationship').text();
			var aff_email = $(e.currentTarget).closest('tr').find('.affiliated_email').text();
			var affiliat_id = $(e.currentTarget).closest('tr').attr('affiliatid');
			var post = {};
			
			post['name'] = aff_name;
			post['relationship'] = aff_relationship;
			post['email'] = aff_email;
			var $form = $('.vaffiliated_contact_panel');
			
			var crow = $(e.currentTarget).closest('tr').attr('id');

			ajax.jsonRpc('/affiliated_contact/creation', 'call', post).then(function (modal) { 
				var $modal = $(modal);			
	  		    $modal.appendTo($form).modal();	
	  		    $modal.on('click', '.waring', function(ev){
					$(this).removeClass('waring');
				});
	  		    $modal.on('click', '#affiliated_save', function(ev){
	  		    	var aff_name =  $("#affiliat_name").val();
					var aff_relationship = $("#affiliat_relationship").val();
					var aff_email = $("#affiliat_email").val();
					post['count'] = crow;
					post['aff_name'] = aff_name;
					post['aff_email'] = aff_email;
					post['aff_relationship'] = aff_relationship;
	  		    	$('.affiliated_div input').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
					});
					/*** Validation in Email */
					var emailvalidation = self._validateEmail(aff_email);
					if(aff_name && aff_relationship && aff_email && emailvalidation){
	  		    		ajax.jsonRpc('/new/row/affiliated', 'call', post).then(function (modal) { 
	  		    			$('.affiliated_contact_ids tbody').find('tr#'+crow).replaceWith(modal);
	  		    			$('.affiliated_contact_ids tbody').find('tr#'+crow).attr('affiliatid', affiliat_id);
		  		    	});
		  		    	$modal.empty();
		  				$modal.modal('hide');
		  				$('.affiliated_contact_popup').remove();
	  		    	}
	  		    	else{
	  		    	// Check email validation
						if(aff_email !="" && !emailvalidation){
							alertify.alert('Message','Please enter valid email.');
							$("#affiliat_email").addClass('waring')
							return false;
						}
		  				alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
     				     return false;
	  		    	}
	  		    	
	  		    });
	  		    //close action
	   		    $modal.on('click', '#affiliated_close', function(ev){
	   		    	$modal.empty();
			    	$modal.modal('hide');
			    	$('.affiliated_contact_popup').remove();
	   		    });
			});
		}
		else{
			var post = {};
	    	var $form = $('.vaffiliated_contact_panel');
	    	self.affiliated_contact_popup(post, $form);
		}
    },

    /*** Ended Add AffiliatedContact  ***/
    /*** KEY Products service offered Starts  ***/
    /*Product File view*/
    _on_click_file_view:function(ev){
		 /** View product photo row */
		 	var self = this;
			var row_id = $(ev.currentTarget).closest('tr').attr('id');
			if(row_id != 'empty_product'){
			 	var data = $(ev.currentTarget).closest('tr').find('.product_file').attr('file_data');
			 	var attachment_id = $(ev.currentTarget).closest('tr').find('.product_file').attr('attachment');
				 if(data && attachment_id){
					 var post = {};
					 post['src'] = data
					 post['attachment_id'] = attachment_id

					 var $form = $('.vproduct_service_panel');

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
			}
			else{
				 alertify.alert('Message','No records found.'); 
				 return false;
			 }
	 },

    /*** Add Product Service  ***/
    _onAdd_Product_Service: function(ev){
    	ev.preventDefault();
    	var self = this;
    	var post = {};
    	var $form = $('.vproduct_service_panel');
    	self.product_service_popup(post, $form);
    },
    product_service_popup: function(post, $form){
    	var self= this;
    	post['p_name'] = '';
    	post['p_desc'] = '';
    	post['category_id'] = 0;
    	post['p_price'] = '';
    	post['uom_id'] = 0;
    	post['prod_img'] = false;
    	post['file_attached']= false;
		post['att_ids'] = '[0]';
		post['image_1920'] = '';
		post['img_attached'] = false;
	   	ajax.jsonRpc('/product_service/creation', 'call', post).then(function (modal) { 
					var $modal = $(modal);			
					$modal.appendTo($form).modal();	
					//add product img
					self._product_attach();
					var crow = $('.product_service_ids tbody tr').length;
					product_form_widget.product_attch_file_list = [];
					$('#product_attach_fileList li').each(function(){
						product_form_widget.product_attch_file_list.push({
								'file_name': $(this).attr('data'),
								'file_content': $(this).attr('file_data'),
								'att_id': crow,
						});
					});
					$(".remove-list").off().on('click', function(){
						var file_name = $(this).parent('li').attr('data');
						product_form_widget.product_attch_file_list = product_form_widget.product_attch_file_list.filter((el) => {
							return el.file_name !== file_name;
						});
					});
					$modal.on('click', '.waring', function(ev){
						$(this).removeClass('waring');
					});
					//save action
					$modal.on('click', '#ps_offered_save', function(ev){
						$('#vp_page_loading').show();
						var pmandatory = false;
						var crow = $('.product_service_ids tbody tr').length;
						var p_name =  $("#product_service").val();
						var p_desc =  $("#pname").val();
						var p_price =  $("#p_price").val();
						var category_id = $("#product_classification_id option:selected").val();
						var category_name = $("#product_classification_id option:selected").text();
						var uom_id = $("#uom_id option:selected").val();
						var uom_name = $("#uom_id option:selected").text();
						if(p_price != undefined && p_price != null){
							p_price = parseFloat(p_price.replace(/,/g, ''))
						}
						post['count'] = crow;
						post['p_name'] = p_name;
						post['p_desc'] = p_desc;
						post['p_price'] = p_price;
						post['category_id']= category_id;
						post['category_name']= category_name.trim();
						post['uom_id']= uom_id;
						post['uom_name']= uom_name.trim();

						var img_data = $('.product-pic').attr('img_data');
						if(img_data != undefined){
							post['image_1920'] = img_data;
							post['img_attached'] = true;
						}
						if(img_data == undefined){
							post['image_1920'] = '';
							post['img_attached'] = false;
						}

						/** Get attachment details */
						post['file_attached'] = false;
						var file_details = product_form_widget.product_attch_file_list;

						if (file_details.length >0){
							post['file_attached'] = true;
						}
						post['product_files'] = file_details;

						if (p_name && p_desc && category_id && p_price && uom_id){
							pmandatory = true;
						}
						$('.registration_service_offerd input').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						$('.registration_service_offerd textarea').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						$('.registration_service_offerd select').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						if(p_price && pmandatory){
							var price = parseFloat(p_price)
							if(price <= 0){
								$('#p_price').addClass('waring');
								pmandatory = false;
							}
						}
						if(pmandatory){
		  		    		ajax.jsonRpc('/new/row/product', 'call', post).then(function (modal) { 
		  		    			$('.product_service_ids tr#empty_product').before(modal);
			  		    		var row = $('.product_service_ids tbody tr').length - 1;
			  		    		if(row>=1){
			  		    			$('.product_service_ids tr#empty_product').addClass('v_display_none');
			  		    		}
								$('#vp_page_loading').hide();
			  		    	});
		  		    		$modal.empty();
					    	$modal.modal('hide');
							$('.product_service_popup').remove();
		  		    	}
		  		    	else{
							$('#vp_page_loading').hide();
							if(p_price){
								var price = parseFloat(p_price)
								if(price <= 0){
									alertify.alert('Message','Price should be greater than 0.'); 
								}
							}else{
								alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
							}
			  				
	     				     return false;
		  		    	}
						
					});
		   		    $modal.on('click', '#ps_offered_close', function(ev){
		   		    	$modal.empty();
				    	$modal.modal('hide');
				    	$('.product_service_popup').remove();
		   		    });
		});
   },
   _onDelete_product:function(e){
 	 	/** Delete product service row */
	  	var row_id = $(e.currentTarget).closest('tr').attr('id');
	  	if(row_id != 'empty_product'){
	  		var $content = ($('<p/>').text(_t('Are you sure you want to delete?')));
	  		new Dialog(this, {
	            title: _t("Confirmation"),
	            size: 'medium',
	            $content: $content,
	            buttons: [
	                {text: _t("OK"), classes: 'btn-primary',  close: true, click: function () {
	                	var table = $(e.currentTarget).closest('table');	
  						var tr = $(e.currentTarget).closest('tr');
  						tr.remove();
  						var row = $('.product_service_ids tbody tr').length;
  						if(row==1){
		  		    		$('.product_service_ids tr#empty_product').removeClass('v_display_none');
		  		    	}
	                }},
	                {text: _t("Discard"), close: true},
	            ],
	        }).open();
	  	}
	 }, 
	 _onView_product_photo:function(e){
		 /** View product photo row */
		 	 var self = this;
			 var row_id = $(e.currentTarget).closest('tr').attr('id');
			 if(row_id != 'empty_product'){
				 var post = {};
				 var img_attached = $(e.currentTarget).closest('tr').find('.product_photo').attr('imgattach');
				 var img_data = $(e.currentTarget).closest('tr').find('.product_photo').attr('img_data');
				 post['image_1920'] = img_data;
				 post['img_attached'] = img_attached;

				 var $form = $('.vproduct_service_panel');
					
				 if(img_attached && img_data){
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
				 else{
					 alertify.alert('Message','No Product Photo.'); 
					 return false;
				 }
				 
			 }
			 else{
				 alertify.alert('Message','No records found.'); 
				 return false;
			 }
	 },
	 /**
      * @private
		* @param {Object} ev
      * Show Multi Attachment Popup for Product
      */
	 _showMultiAttachPopup: function(ev){
			var $form = $('.vproduct_service_panel');
			var pro_attach_ids = $(ev.currentTarget).attr('attachment');
			var action = $(ev.currentTarget).attr('action');
			var post = {'attach_ids': pro_attach_ids}
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
	 _onEdit_product:function(e){
		 var self =this;
		 /** Edit product servicerow */
	    	var row_id = $(e.currentTarget).closest('tr').attr('id');
			if(row_id != 'empty_product'){
				var p_name = $(e.currentTarget).closest('tr').find('.p_name').text();
				var p_desc = $(e.currentTarget).closest('tr').find('.p_desc').text();
				var p_price = $(e.currentTarget).closest('tr').find('.p_price').text();
				var category_id = $(e.currentTarget).closest('tr').find('.p_category_id').attr('category_id');
				var uom_id = $(e.currentTarget).closest('tr').find('.p_uom_id').attr('uom_id');
				
				var img_attached = $(e.currentTarget).closest('tr').find('.product_photo').attr('imgattach');
				var img_data = $(e.currentTarget).closest('tr').find('.product_photo').attr('img_data');
				
				var file_attached = $(e.currentTarget).closest('tr').find('.product_file').attr('fileattach');
				var att_ids = $(e.currentTarget).closest('tr').find('.product_file').attr('attachment');

				var productid = $(e.currentTarget).closest('tr').attr('productid');
				var post = {};
				
				post['p_name'] = p_name;
				post['p_desc'] = p_desc;
				post['p_price'] = p_price;
				post['category_id']= category_id;
				post['uom_id']= uom_id;
				post['file_attached']= file_attached;
				post['att_ids'] = att_ids;
				post['image_1920'] = img_data;
				post['img_attached'] = img_attached;
				
				var $form = $('.vproduct_service_panel');
				
				var crow = $(e.currentTarget).closest('tr').attr('id');

				ajax.jsonRpc('/product_service/creation', 'call', post).then(function (modal) { 
					var $modal = $(modal);			
		  		    $modal.appendTo($form).modal();	
		  		    //add product img
					self._product_attach();
					product_form_widget.product_attch_file_list = [];
					$('#product_attach_fileList li').each(function(){
						product_form_widget.product_attch_file_list.push({
								'file_name': $(this).attr('data'),
								'file_content': $(this).attr('file_data'),
								'att_id': crow
						});
					});
					$(".remove-list").off().on('click', function(){
						var file_name = $(this).parent('li').attr('data');
						product_form_widget.product_attch_file_list = product_form_widget.product_attch_file_list.filter((el) => {
							return el.file_name !== file_name;
						});
					});
					$modal.on('click', '.waring', function(ev){
						$(this).removeClass('waring');
					});
					//update data
		  		    $modal.on('click', '#ps_offered_save', function(ev){
						$('#vp_page_loading').show();
		  		    	var pmandatory = false;
		  		    	var p_name =  $("#product_service").val();
						var p_desc =  $("#pname").val();
						var p_price =  $("#p_price").val();
						var category_id = $("#product_classification_id option:selected").val();
						var category_name = $("#product_classification_id option:selected").text();
						var uom_id = $("#uom_id option:selected").val();
						var uom_name = $("#uom_id option:selected").text();
						if(p_price != undefined && p_price != null){
							p_price = parseFloat(p_price.replace(/,/g, ''))
						}
						post['count'] = crow;
						post['p_name'] = p_name;
						post['p_desc'] = p_desc;
						post['p_price'] = p_price;
						post['category_id']= category_id;
						post['category_name']= category_name.trim();
						post['uom_id']= uom_id;
						post['uom_name']= uom_name.trim();
						
						var img_data = $('.product-pic').attr('img_data');
						if(img_data != undefined){
							post['image_1920'] = img_data;
							post['img_attached'] = true;
						}
						if(img_data == undefined){
							post['image_1920'] = '';
							post['img_attached'] = false;
						}
						// Set attachments
						post['file_attached'] = false;
						var file_details = product_form_widget.product_attch_file_list;
						if (file_details.length >0){
							post['file_attached'] = true;
						}
						post['product_files'] = file_details;
						if (p_name && p_desc && category_id && p_price && uom_id){
							pmandatory = true;
						}
						$('.registration_service_offerd input').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						$('.registration_service_offerd textarea').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						$('.registration_service_offerd select').each(function(){
							if($(this).attr('required') && !$(this).val()){
								$(this).addClass('waring');
							}
						});
						if(p_price && pmandatory){
							var price = parseFloat(p_price)
							if(price <= 0){
								$('#p_price').addClass('waring');
								pmandatory = false;
							}
						}
						if(pmandatory){
		  		    		ajax.jsonRpc('/new/row/product', 'call', post).then(function (modal) { 
			  		    		$('.product_service_ids tbody').find('tr#'+crow).replaceWith(modal);
			  		    		$('.product_service_ids tbody').find('tr#'+crow).attr('productid', productid);
								$('#vp_page_loading').hide();
			  		    	});
		  		    		$modal.empty();
					    	$modal.modal('hide');
							$('.product_service_popup').remove();
		  		    	}
		  		    	else{
							$('#vp_page_loading').hide();
							if(p_price){
								var price = parseFloat(p_price)
								if(price <= 0){
									alertify.alert('Message','Price should be greater than 0.'); 
								}
							}else{
								alertify.alert('Message','Please make sure to fill out all mandatory fields.'); 
							}
	     				    return false;
		  		    	}
		  		    	
		  		    });
		  		    //close action
		   		    $modal.on('click', '#ps_offered_close', function(ev){
		   		    	$modal.empty();
				    	$modal.modal('hide');
						$('.product_service_popup').remove();
		   		    });
				});
			}
			else{
				// Open new popup
				var post = {};
		    	var $form = $('.vproduct_service_panel');
		    	self.product_service_popup(post, $form);
			}
	 },
	 _product_attach:function(){
		 	var self = this;
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
		   $(".product_file_input").off().on('change', function(){
			   var output = document.getElementById('product_attach_fileList');
     			var children = "";
				_.map($(".product_file_input")[0].files, function (file) {
						var size = parseFloat(file.size / 1024).toFixed(2)
						if(size <= 5000){
							var reader = new FileReader();
							children +=  '<li id="0" data="'+file.name+'">'+ file.name + '<span class="remove-list" onclick="return this.parentNode.remove()"><i class="fa fa-trash span_icon"></i></span>' + '</li>'
							reader.onload = function (e) {
							self.product_attch_file_list.push({
								'file_name': file.name,
								'file_content': e.target.result,
								'att_id': 0
							});
							$(".remove-list").off().on('click', function(){
								var file_name = $(this).parent('li').attr('data');
								self.product_attch_file_list = self.product_attch_file_list.filter((el) => {
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
		    
		    $(".pro_file_upload").off().on('click', function() {
		       $(".product_file_input").click();
		    });

		    /* file attach end*/
		    
		    /* Allow number value in price */
			$(".vinput_price").on('keypress',function(e) {
				var code = (e.which) ? e.which : e.keyCode;
	    	    if (code > 31 && ((code != 46 && code < 48) || code > 57)) {
	    	        e.preventDefault();
	    	    }
			});
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
		        //Add the data rows from Excel file.
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
					if(price != undefined && price != null){
						price = parseFloat(price.replace(/,/g, ''))
					}
		            post['p_name'] = excelRows[i]["ProductServiceName(Required Field)"];
		            post['p_desc'] = excelRows[i]["ProductServiceDescription(Required Field)"];
		            post['product_classification_id']= excelRows[i]["ProductClassification(Required Field)"];
		            post['category_name'] = excelRows[i]["ProductClassification(Required Field)"];
		            post['p_price'] = price;
		            post['product_uom_id'] = excelRows[i]["UOM(Required Field)"];
		            post['uom_name'] = excelRows[i]["UOM(Required Field)"];
		            
		            post['image_1920'] = '';
					post['img_attached'] = false;
					
					post['product_files'] = [];
					post['file_attached'] = false;
					if(p_name == undefined || p_desc == undefined || product_classification == undefined || price == undefined || uom == undefined){
						alertify.alert('Message','Please make sure to fill out all mandatory fields.');
						return false;
					}else{
						 ajax.jsonRpc('/new/row/product', 'call', post).then(function (modal) { 
	  		    			$('.product_service_ids tr#empty_product').before(modal);
		  		    		var row = $('.product_service_ids tbody tr').length - 1;
	  						if(row >=1){
			  		    		$('.product_service_ids tr#empty_product').addClass('v_display_none');
			  		    	}
		  		    	});
					}
		        }
		    };
	 },
	 /*** KEY Products service offered Ended  ***/
	 
	 /*** Input remove warning  ***/
	 _onClick_input:function(e){
		 if($(this).hasClass("waring")){ 
  			$(this).removeClass('waring');
  		}
	 },
	/*** Vendor User Register - Starts ***/
   _Vendor_confirmation:function(ev){
	   var self = this;
	   var vendor_datas = [];
		
	   var vendor_reg_form = $('#vendor_registration').find("form#vendor_registration_form").serializeArray();
	   // read all input type values from post 
	   var indexed_profile_array = {};			   
	   $.map(vendor_reg_form, function(n, i){
		   indexed_profile_array[n['name']] = n['value'];
	   });
	  
	   var isProceed=true;			
	   var post ={};
	    // Checked required field
	   	$('#vendor_registration').find('input[required="required"]').each(
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
	   	$('#vendor_registration').find('select[required="required"]').each(
				function(index, element) {
					if ($(this).val() == 0) {
						$(this).addClass('waring');
						isProceed = false;						
					}else{
						$(this).removeClass('waring');
					}
		}).focus(function() {
			$(this).removeClass('waring');
		});	
	   	var email = $('#vendor_registration').find(".v_email").val();
		var tin_vat = $('#vendor_registration').find("#tin_vat").val();
		
	   	/*** Validation in Email */
	   	var emailvalidation = self._validateEmail(email);	
	   	
	   	/* Site Office Address values */
	   	var child_ids = []

	   	var site_row = $('.site_office_ids tbody tr').length - 1;

	   	if (site_row > 0){
	   		$('.site_office_ids tbody tr[id!="empty_site"]').each(function(){
	   			var s_name = $(this).find('.s_name').text();
				var s_street = $(this).find('.s_street').text();
				var s_street2 = $(this).find('.s_street2').text();
				var s_barangay_id = $(this).find('.s_barangay_id').attr('barangay_id');
				var s_city_id = $(this).find('.s_city_id').attr('city_id');
				var s_province_id = $(this).find('.s_province_id').attr('province_id');
				var s_state_id = $(this).find('.s_state_id').attr('state_id');
				var s_country_id = $(this).find('.s_country_id').attr('country');
				var s_zipcode = $(this).find('.s_zipcode').text();
				if (s_state_id == undefined || s_state_id == ''){
					s_state_id = false;
				}
				else{
					s_state_id = parseInt(s_state_id)
				}
				if (s_province_id == undefined || s_province_id == ''){
					s_province_id = false;
				}
				else{
					s_province_id = parseInt(s_province_id)
				}
				if (s_city_id == undefined || s_city_id == ''){
					s_city_id = false;
				}
				else{
					s_city_id = parseInt(s_city_id)
				}
				if (s_barangay_id == undefined || s_barangay_id == ''){
					s_barangay_id = false;
				}
				else{
					s_barangay_id = parseInt(s_barangay_id)
				}
				if (s_country_id == undefined || s_country_id == ''){
					s_country_id = false;
				}
				else{
					s_country_id = parseInt(s_country_id)
				}
				child_ids.push([0,0,{
									'name': s_name,
									'street': s_street,
									'street2': s_street2,
									'state_id': s_state_id,
									'province_id': s_province_id,
									'city_id': s_city_id,
									'zip': s_zipcode,
									'barangay_id': s_barangay_id,
									'country_id': s_country_id,
						 			'type': 'other',
						 			'supplier_rank': 1,
					 				}
	 			]);
	   		});
	   	}
	   	
	   	/* Contact Person values */
	   	var contact_row = $('.contact_person_ids tbody tr').length - 1;

	   	if (contact_row > 0){
	   		$('.contact_person_ids tbody tr[id!="empty_contact"]').each(function(){
	   			var c_name = $(this).find('.c_name').text();
				var c_department = $(this).find('.c_department').text();
				var c_position = $(this).find('.c_position').text();
				var c_phone = $(this).find('.c_phone').text();
				var c_mobile = $(this).find('.c_mobile').text();
				var c_email = $(this).find('.c_email').text();
				child_ids.push([0,0,{
		 			   			'name': c_name,
		 					 	'department': c_department,
		 					 	'function': c_position,
		 					 	'phone': c_phone,
		 					 	'mobile': c_mobile,
		 					 	'email': c_email,
		 					 	'type': 'contact',
		 					 	'supplier_rank': 1,
	 						}
	 			]);
	   		});
	   	}else{
			$('.contact_person_ids tbody tr[id="empty_contact"] td').each(function(){
				$(this).addClass('waring');
			})
		}
	   	// Site address and contact person in child ids
	   	indexed_profile_array['child_ids'] = child_ids;
	   	
	   	
	   	// Product Categories
	   	var product_classification_ids = [];
	   	var categ_ids = [];
	   	var categ_mandatory = false;
	   	$('.product_classification_ids div').each(function(){
	   		var is_categ_checked = $(this).find('#category_id').is(':checked'); 
	   		if(is_categ_checked){
	   			var categ_id = $(this).find('#category_id').attr('categ_id')
	   			categ_ids.push(parseInt(categ_id));
	   		}
	   	});
	   	// other category
	   	var other_category = $('#vendor_registration').find("#has_other_category").is(':checked');
	   	var other_categories = $('#vendor_registration').find("#other_categories").val();

	   	if(categ_ids.length >0){
	   		product_classification_ids.push([6,0,categ_ids]);
	   	}
	   	else{
	   		if (!other_category){
	   			categ_mandatory = true;
				$('.vendor_product_category').addClass('waring');
	   		}
	   	}
	   	indexed_profile_array['product_classification_ids'] = product_classification_ids;
	   	
	   	/* Affiliated contact values */
	   	var affiliated_contact = [];
	   	var affiliated_row = $('.affiliated_contact_ids tbody tr').length - 1;

	   	if (affiliated_row > 0){
	   		$('.affiliated_contact_ids tbody tr[id!="empty_affiliat"]').each(function(){
	   			var aff_name = $(this).find('.affiliated_name').text();
				var aff_relationship = $(this).find('.affiliated_relationship').text();
				var aff_email = $(this).find('.affiliated_email').text();
				affiliated_contact.push([0,0,{
				   				'name': aff_name,
								'email': aff_email,
								'relationship': aff_relationship
	 							}
	 			]);
	   		});
	   	}
	   	indexed_profile_array['affiliated_contact_ids'] = affiliated_contact;
	   	
	   	/* Product Service values */
	   	var product_service = [];
	   	var product_row = $('.product_service_ids tbody tr').length - 1;

	   	if (product_row > 0){
	   		$('.product_service_ids tbody tr[id!="empty_product"]').each(function(){
	   			var p_name = $(this).find('.p_name').text();
				var p_desc = $(this).find('.p_desc').text();
				var p_price = $(this).find('.p_price').text();
				var category_id = $(this).find('.p_category_id').attr('category_id');
				var uom_id = $(this).find('.p_uom_id').attr('uom_id');
				
				var img_attached = $(this).find('.product_photo').attr('imgattach');
				var img_data = $(this).find('.product_photo').attr('img_data');
				var data_jpeg = img_data.replace("data:image/jpeg;base64,", "")
		        var data_png = data_jpeg.replace("data:image/png;base64,", "")
		        var data = data_png.replace("data:image/jpg;base64,", "")

		        var attachment_ids = []
				var file_attached = $(this).find('.product_file').attr('fileattach');
		        var file_attach_ids = $(this).find('.product_file').attr('attachment');

				if(file_attached && file_attach_ids)
					attachment_ids = file_attach_ids;

				if (category_id == undefined || category_id == '0'){
					category_id = false;
				}
				else{
					category_id = parseInt(category_id)
				}
				if (uom_id == undefined || uom_id == '0'){
					uom_id = false;
				}
				else{
					uom_id = parseInt(uom_id)
				}
				product_service.push([0,0,{
				   				'product_service': p_name,
								'name': p_desc,
								'price': parseFloat(p_price.replace(/,/g, '')),
								'product_classification_id': category_id,
								'uom_id': uom_id,
								'image_1920': data,
								'attachment_ids': attachment_ids,
	 							}
	 			]);
	   		});
	   	}
	   	indexed_profile_array['product_service_offered_line'] = product_service;
	   	
	   	// Catalogue File attach
		indexed_profile_array['catalogue_all_attach'] = self.brocher_file_list;
		
	   	vendor_datas.push(indexed_profile_array);	
	   	post['vendor_datas'] = vendor_datas;
	   	
	   	var agree = $('#vendor_registration').find("input#agree").is(':checked');					
	   	var recaptcha = $("#g-recaptcha-response").val();
		if (!agree){
			$("#agree").addClass('required_warning');
		}
		if(!isProceed)
		{  
			 alertify.alert('Message','Please make sure to fill out all mandatory fields.');
			 ev.preventDefault();
		     return false;
		}
		if(isProceed)
		{	
			// Check email validation
			if(email !="" && !emailvalidation){
				alertify.alert('Message','Please enter valid email.');
				$('#vendor_registration').find(".v_email").addClass('waring');
				return false;
			}
			// Tin number validation
			if(tin_vat !="" && tin_vat.length != 15){
				alertify.alert('Message','Please enter valid TIN number.');
				$('#vendor_registration').find("#tin_vat").addClass('waring');
				return false;
			}
			// Check contact 
			if (contact_row <=0){
		   		alertify.alert('Message','Please add at least one Contact Person.');
				 ev.preventDefault();
			     return false;
		   	}
			// Check Product category
			if(categ_mandatory){
				alertify.alert('Message','Please add at least one Product Classification.');
				ev.preventDefault();
			    return false;
			}
			if(other_category && other_categories==''){
				alertify.alert('Message','Please specify Product Classification.');
				ev.preventDefault();
			    return false;
			}
				
			if (!agree)
		    {
				alertify.alert('Message','You must agree with the Terms and Conditions & the Privacy Policy.');	
				$("#agree").addClass('required_warning');
				ev.preventDefault();
		     	return false;
		    }
			if (recaptcha === "") {
			      ev.preventDefault();
			      alertify.alert('Message', 'Please check the reCAPTCHA');
			      return false;
			}
			// Create vendor user
			ajax.jsonRpc('/vendor_registration/creation', 'call', post).then(function (result) {
				if (result == "/vendor/register_confirm")
					window.location = "/vendor/register_confirm";
			});
		}
   	},
   	
   	_validateEmail: function(email){
    	var val_email = email;
    	if(val_email){
    		/** Valid Email Character ***/
    		var email_pattern = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    		return email_pattern.test(val_email);
    	}
    },
    _block_aplhabets: function () {
    	/** Blocked alphabets in mobile_no field **/
    	$(".vinput_number").on('keypress',function(e) {	
    		var code = (e.which) ? e.which : e.keyCode;
    	    if (code > 31 && (code < 48 || code > 57)) {
    	        e.preventDefault();
    	    }
    	});
    	/** End Blocked alphabets in mobile_no field **/
    	
    	/** TIN format field **/
    	$("#tin_vat").keyup(function (e) {
    		 addHyphen(this);
    	});
    	function addHyphen (element) {
    		if ($(element).val()){
    			let val = $(element).val().split('-').join('');   // Remove dash (-) if mistakenly entered.

                let finalVal = val.match(/.{1,3}/g).join('-');    // Add (-) after 3rd every char.
                $(element).val(finalVal);		// Update the input box.
    		}
        }
    },
    /*** Vendor User Register - end ***/
    /**
     * @private
     */
	_adaptAddressFormField: function () {
			$(".country_id").on('change',function(e) {
				var $s_country = $('select[name="country_id"]');
				var country_id =  $s_country.val(); 
				if(country_id){
					var post = {'country_id': country_id}
					ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
						$("#state_id").html(modal)
						$("#province_id").html('<option value=""></option>');
						$("#city_id").html('<option value=""></option>');
						$("#barangay_id").html('<option value=""></option>');
					});
				}
			});
			$(".state_id").on('change',function(e){
				var $s_state = $('select[name="state_id"]');
				var state_id =  $s_state.val(); 
				if(state_id){
					var post = {'state_id': state_id}
					ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
						$("#province_id").html(modal);
						$("#city_id").html('<option value=""></option>');
						$("#barangay_id").html('<option value=""></option>');
					});
				}
			});
			$(".province_id").on('change',function(e) {
				var $s_province = $('select[name="province_id"]');
				var province_id =  $s_province.val(); 
			    if(province_id){
					var post = {'province_id': province_id}
					ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
						$("#city_id").html(modal);
						$("#barangay_id").html('<option value=""></option>');
					});
				}
			});
			$(".city_id").on('change',function(e) {
				var $s_city = $('select[name="city_id"]');
				var city_id =  $s_city.val(); 
			    if(city_id){
					var post = {'city_id': city_id}
					ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
						$("#barangay_id").html(modal)
					});
				}
			});
	},
    _adaptAddressForm: function () {
        var $country = this.$('select[name="country_id"]');
        var countryID = ($country.val() || 0);
        
        /*State filter based on country*/
        this.$stateOptions.detach();
        var $displayedState = this.$stateOptions.filter('[data-country_id=' + countryID + ']');
        var nb = $displayedState.appendTo(this.$state).show().length;
        this.$state.parent().toggle(nb >= 1);
        
        /*Provice filter based on country*/
        this.$provinceOptions.detach();
        var $displayedProvince = this.$provinceOptions.filter('[data-country_id=' + countryID + ']');
        var nb = $displayedProvince.appendTo(this.$province).show().length;
        this.$province.parent().toggle(nb >= 1);
        
        /*City filter based on country*/
        this.$cityOptions.detach();
        var $displayedCity = this.$cityOptions.filter('[data-country_id=' + countryID + ']');
        var nb = $displayedCity.appendTo(this.$city).show().length;
        this.$city.parent().toggle(nb >= 1);
        
        /*Barangay filter based on country*/
        this.$barangayOptions.detach();
        var $displayedBarangay = this.$barangayOptions.filter('[data-country_id=' + countryID + ']');
        var nb = $displayedBarangay.appendTo(this.$barangay).show().length;
        this.$barangay.parent().toggle(nb >= 1);
        
    },

    _adaptAddressFields: function () {
    	var $state = this.$('select[name="state_id"]');
        var stateID = ($state.val() || 0);
        this.$provinceOptions.detach();
        var $displayedProvince = this.$provinceOptions.filter('[data-state_id=' + stateID + ']');
        var nb = $displayedProvince.appendTo(this.$province).show().length;
        this.$province.parent().toggle(nb >= 1);

        var $province = this.$('select[name="province_id"]');
        var provinceID = ($province.val() || 0);
        this.$cityOptions.detach();
        var $displayedCity = this.$cityOptions.filter('[data-province_id=' + provinceID + ']');
        var nb = $displayedCity.appendTo(this.$city).show().length;
        this.$city.parent().toggle(nb >= 1);
       
        var $city = this.$('select[name="city_id"]');
        var cityID = ($city.val() || 0);
        this.$barangayOptions.detach();
        var $displayedBarangay = this.$barangayOptions.filter('[data-city_id=' + cityID + ']');
        var nb = $displayedBarangay.appendTo(this.$barangay).show().length;
        this.$barangay.parent().toggle(nb >= 1);
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onCountryChange: function () {
        this._adaptAddressFormField();
		var $s_country = $('select[name="country_id"]');
		var country_id =  $s_country.val(); 
		if(country_id){
			var post = {'country_id': country_id}
			ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
				$("#state_id").html(modal)
				$("#province_id").html('<option value="">Province..</option>');
				$("#city_id").html('<option value="">City..</option>');
				$("#barangay_id").html('<option value="">Barangay..</option>');
			});
		}
    },
    /**
     * On State change: adapt Province field
     *
     * @override
     * @param {Event} ev
     */
    _onStateChange: function () {
        this._adaptAddressFormField();
		var $s_state = $('select[name="state_id"]');
		var state_id =  $s_state.val(); 
		if(state_id){
			var post = {'state_id': state_id}
			ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
				$("#province_id").html(modal);
				$("#city_id").html('<option value="">City..</option>');
				$("#barangay_id").html('<option value="">Barangay..</option>');
			});
		}
    },
    /**
     * On Province change: adapt City field
     *
     * @override
     * @param {Event} ev
     */
    _onProvinceChange: function () {
        this._adaptAddressFormField();
		var $s_province = $('select[name="province_id"]');
		var province_id =  $s_province.val(); 
		if(province_id){
			var post = {'province_id': province_id}
			ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
				$("#city_id").html(modal);
				$("#barangay_id").html('<option value="">Barangay..</option>');
			});
		}
    },
    
    /**
     * On City change: adapt Barangay field
     *
     * @override
     * @param {Event} ev
     */
    _onCityChange: function () {
        this._adaptAddressFormField();
		var $s_city = $('select[name="city_id"]');
		var city_id =  $s_city.val(); 
		if(city_id){
			var post = {'city_id': city_id}
			ajax.jsonRpc('/onchange/head_office_address', 'call', post).then(function (modal){
				$("#barangay_id").html(modal)
			});
		}
    },

	/**
   	* @private
   	* @param {Event} ev
   	*/
    _onAcceptPrivacyPolicy: function (ev) {
       $("#check_privacy_policy").prop('checked', true);
       var terms_and_condition = $("#check_terms_and_condition").is(":checked");
       if(terms_and_condition){
    	   if($("#agree").hasClass('required_warning')){
				$("#agree").removeClass('required_warning');
			}
       		$("#agree").prop('checked', true);
       }
       else{
       	$("#agree").prop('checked', false);
       }
    },
    
	/**
   	* @private
   	* @param {Event} ev
    */
    _onAcceptTermsCondition: function (ev) {
       $("#check_terms_and_condition").prop('checked', true);
       var privacy_policy = $("#check_privacy_policy").is(":checked");
       if(privacy_policy){
    	   if($("#agree").hasClass('required_warning')){
				$("#agree").removeClass('required_warning');
			}
       		$("#agree").prop('checked', true);
       }
       else{
       	$("#agree").prop('checked', false);
       }
    },
    
	/**
	* @private
	* @param {Event} ev
	*/
    _onClickAgree: function (ev) {
		var agree = $("#agree").is(":checked");
		if(agree){
			// Remove warning
			if($("#agree").hasClass('required_warning')){
				$("#agree").removeClass('required_warning');
			}
	   		$("#check_terms_and_condition").prop('checked', true);
	       	$("#check_privacy_policy").prop('checked', true);
     	}
       	else{
       		$("#check_terms_and_condition").prop('checked', false);
       		$("#check_privacy_policy").prop('checked', false);
    	}
    },  

});

});
