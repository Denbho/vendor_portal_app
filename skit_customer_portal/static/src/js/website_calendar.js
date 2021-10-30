odoo.define('skit_customer_portal.appointment_table', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

/**
 * Extends websiteCalendarSelect to display Appointment table
 */
publicWidget.registry.websiteCalendarSelect.include({
    /**
     * On appointment type change: adapt appointment table
     *
     * @override
     * @param {Event} ev
     */
    _onAppointmentTypeChange: function (ev) {
    	var def = this._super.apply(this, arguments);
    	var appointmentID = $(ev.target).val();
        var previousSelectedEmployeeID = $(".o_website_appoinment_form select[name='employee_id']").val();
        var postURL = '/website/calendar/' + appointmentID + '/appointment';
        $(".o_website_appoinment_form").attr('action', postURL);
        this._rpc({
            route: "/website/calendar/get_appointment_info",
            params: {
                appointment_id: appointmentID,
                prev_emp: previousSelectedEmployeeID,
            },
        }).then(function (data) {
            if (data) {
                // $('.o_calendar_intro').html(data.message_intro);
                $(".o_website_calendar_appointment div[name='scheduled_appointment']").replaceWith(data.calendar_event_table_html);
                if (data.assignation_method === 'chosen') {
                    $(".o_website_appoinment_form div[name='employee_select']").replaceWith(data.employee_selection_html);
                } else {
                    $(".o_website_appoinment_form div[name='employee_select']").addClass('o_hidden');
                    $(".o_website_appoinment_form select[name='employee_id']").children().remove();
                }
            }
        });
    },
});
});


