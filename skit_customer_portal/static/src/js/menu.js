odoo.define('website.systray.ActivityMenu', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var session = require('web.session');
var core = require('web.core');
var QWeb = core.qweb;

/**
 * Menu item appended in the systray part of the navbar
 */
publicWidget.registry.NotificationMenu = publicWidget.Widget.extend({
    selector: '.notification_menu',
    xmlDependencies: ['/mail/static/src/xml/systray.xml'],
    events: {
        'show.bs.dropdown': '_onActivityMenuShow',
    },

    /**
     * @override
     */
    start: function () {
        this._$activitiesPreview = this.$('.o_mail_systray_dropdown_items');
        this._updateCounter();
        this._updateActivityPreview();
        return this._super();
    },
    //--------------------------------------------------
    // Private
    //--------------------------------------------------
    /**
     * Make RPC and get current user's activity details
     * @private
     */
    _getActivityData: function () {
        var self = this;
        return self._rpc({
            model: 'res.users',
            method: 'systray_get_activities',
            args: [],
            kwargs: {context: session.user_context},
        }).then(function (data) {
            self._activities = data;
            self.activityCounter = _.reduce(data, function (total_count, p_data) { return total_count + p_data.total_count || 0; }, 0);
            self.$('.o_notification_counter').text(self.activityCounter);
            self.$el.toggleClass('o_no_notification', !self.activityCounter);
        });
    },
	/**
	 * Update(render) activity system tray view on activity updation.
	 * @private
	 */
     _updateActivityPreview: function () {
         var self = this;
         self._getActivityData().then(function (){
            self._$activitiesPreview.html(QWeb.render('mail.systray.ActivityMenu.Previews', {
                widget: self
            }));
         });
     },
     
     /**
      * update counter based on activity status(created or Done)
      * @private
      * @param {Object} [data] key, value to decide activity created or deleted
      * @param {String} [data.type] notification type
      * @param {Boolean} [data.activity_deleted] when activity deleted
      * @param {Boolean} [data.activity_created] when activity created
      */
     _updateCounter: function (data) {
         if (data) {
             if (data.activity_created) {
                 this.activityCounter ++;
             }
             if (data.activity_deleted && this.activityCounter > 0) {
                 this.activityCounter --;
             }
             this.$('.o_notification_counter').text(this.activityCounter);
             this.$el.toggleClass('o_no_notification', !this.activityCounter);
         }
     },
     //------------------------------------------------------------
     // Handlers
     //------------------------------------------------------------
     /**
      * @private
      */
     _onActivityMenuShow: function () {
         document.body.classList.add('modal-open');
          this._updateActivityPreview();
     },
});

});
