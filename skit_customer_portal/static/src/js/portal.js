odoo.define('skit_customer_portal.portal', function (require) {
    "use strict";
    
    var ajax = require('web.ajax');
    var portalPortal = require('portal.portal');  
    var publicWidget = require('web.public.widget');
    
    /**
     * Extends portalDetails to handle new fields added in the form
     */
    publicWidget.registry.portalDetails.include({
    	events: _.extend({}, publicWidget.registry.portalDetails.prototype.events || {}, {
        	'click .edit_profile': '_onProfileEdit',
            'change .o_forum_file_upload': '_onFileUploadChange', 
            'click .profile_pic_clear': '_onProfilePicClearClick',
            'click .profile_pic_edit': '_onEditProfilePicClick',
            'change select[name="state_id"]': '_onStateChange',
            'change select[name="province_id"]': '_onProvinceChange',
            'change select[name="city_id"]': '_onCityChange',
        }),
        start: function () {
        	var def = this._super.apply(this, arguments);
        	//def.then(function () {
        	this.$state = this.$('select[name="state_id"]');
            this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');
            	
	    	this.$province = this.$('select[name="province_id"]');
	        this.$provinceOptions = this.$province.filter(':enabled').find('option:not(:first)');
	        
	        this.$city = this.$('select[name="city_id"]');
	        this.$cityOptions = this.$city.filter(':enabled').find('option:not(:first)');
                
	        this.$barangay = this.$('select[name="barangay_id"]');
            this.$barangayOptions = this.$barangay.filter(':enabled').find('option:not(:first)');
                
	        this._adaptAddressForm();
            	
	      //  })
	        return def;
        },
        
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /*_adaptAddressForm: function () {
        	var AddressForm = this._super.apply(this, arguments);
        	var selected_name = this.$('select[name="country_id"] option:selected').text() || '';
            var selected_val = this.$('select[name="country_id"] option:selected').val() || '';
            if(selected_name.trim() =='Philippines'){
            	$('.display_depends_country').removeClass('d-none');
            	
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
            }
            else{
            	$('.display_depends_country').addClass('d-none');
            }
            return AddressForm
        },*/
        
        _adaptAddressForm: function () {
        	var AddressForm = this._super.apply(this, arguments);
        	var selected_name = this.$('select[name="country_id"] option:selected').text() || '';
            var selected_val = this.$('select[name="country_id"] option:selected').val() || '';
            if(selected_name.trim() =='Philippines'){
            	$('.display_depends_country').removeClass('d-none');
            }
            else{
            	$('.display_depends_country').addClass('d-none');
            }
            return AddressForm
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

        _onProfileEdit: function () {
        	$('.res_country_dropdown').select2({
    		});
        	$('.res_state_dropdown').select2({
    		});
        	$('.res_nationality_dropdown').select2({
    		});
        	$('.res_emy_cntry').select2({
    		});
        	
        	// Enable the profile image editable
        	$('.avatar-edit').removeClass('display_none');
        	
        	// Disable the Edit icon and enable the Save button
        	$('.edit_profile').addClass('display_none');
        	$('.update_customer').removeClass('display_none');
        	
        	// Disable the Non Editable element and Enable the Editable element
        	$('.non_editable_element').addClass('display_none');
        	$('.non_editable_element').removeClass('display-inline-block');
        	
        	$('.editable_element').removeClass('display_none');
        	$('.editable_element').addClass('display-inline-block');
        	
        	$('.address_editable').removeClass('display_none');
        	$('.address_non_editable').addClass('display_none');
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onEditProfilePicClick: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).closest('form').find('.o_forum_file_upload').trigger('click');
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onFileUploadChange: function (ev) {
            if (!ev.currentTarget.files.length) {
                return;
            }
            var $form = $(ev.currentTarget).closest('form');
            var reader = new window.FileReader();
            reader.readAsDataURL(ev.currentTarget.files[0]);
            reader.onload = function (ev) {
                $form.find('.profile_avatar_img').attr('src', ev.target.result);
            };
          $form.find('#profile_clear_image').remove();
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onProfilePicClearClick: function (ev) {
            var $form = $(ev.currentTarget).closest('form');
            $form.find('.profile_avatar_img').attr('src', '/web/static/src/img/placeholder.png');
            $form.append($('<input/>', {
                name: 'clear_image',
                id: 'profile_clear_image',
                type: 'hidden',
            }));
        }, 
        /**
         * On State change: adapt Province field
         *
         * @override
         * @param {Event} ev
         */
        _onStateChange: function () {
            this._adaptAddressFields();
        },
        /**
         * On Province change: adapt City field
         *
         * @override
         * @param {Event} ev
         */
        _onProvinceChange: function () {
            this._adaptAddressFields();
        },
        
        /**
         * On City change: adapt Barangay field
         *
         * @override
         * @param {Event} ev
         */
        _onCityChange: function () {
            this._adaptAddressFields();
        },
    });
})