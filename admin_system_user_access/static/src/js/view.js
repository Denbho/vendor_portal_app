odoo.define('admin_system_user_access.BasicView', function (require) {
"use strict";

var session = require('web.session');
var BasicView = require('web.BasicView');
BasicView.include({
        init: function(viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            var model = self.controllerParams.modelName;
            if (model == 'property.detail' || model == 'property.subdivision.phase') {
                self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
//                session.user_has_group('admin_system_user_access.group_archive').then(function(has_group) {
//                    if(!has_group) {
//                        self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
//                    }
//                });
            }
        },
});
});