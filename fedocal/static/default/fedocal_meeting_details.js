$(function(){
    var _date = FEDOCAL.NEXT_MEETING.startDate;
    $('#countdown').countdown(
        new Date(_date),
        function(event) {
            $(this).html(
              event.strftime(
                FEDOCAL.MESSAGES.NEXT_MEETING_IN
              )
            );
        }
    ).on('finish.countdown', function(event){
        var _end_date = FEDOCAL.NEXT_MEETING.endDate;
        var _current_date = new Date();
        _current_date = Date.UTC(
            _current_date.getUTCFullYear(),
            _current_date.getUTCMonth(),
            _current_date.getUTCDate(),
            _current_date.getUTCHours(),
            _current_date.getUTCMinutes(),
            0
        );

        if ( _end_date > _current_date ) {
            $(this).html('<p>' + FEDOCAL.MESSAGES.MEETING_IN_PROGRESS + '</p>');
        } else {
            $(this).html('<p>' + FEDOCAL.MESSAGES.MEETING_IS_OVER + '</p>');
        }
    });

    // Handle iCal meeting export with reminder toggle
    $('#ical-meeting-export-reminder-toggle').on('change', function (e) {
        var $icalExportLink = $('#ical-meeting-export');
        var $icalReminderOptions = $('#ical-meeting-export-reminder-at');
        if (this.checked) {
            $icalReminderOptions.removeAttr('disabled');
            $icalExportLink.attr(
                'href', $icalExportLink.attr('href') + '?reminder_delta=' +
                $icalReminderOptions.val());
        } else {
           $icalReminderOptions.attr('disabled', 'disabled');
           $icalExportLink.attr(
                'href', $icalExportLink.attr('href').split('?')[0]);
        }
    });

    // Handle change event in reminder options dropdown in iCal export
    $('#ical-meeting-export-reminder-at').on('change', function (e) {
        var $this = $(this);
        var $icalExportLink = $('#ical-meeting-export');
        $icalExportLink.attr(
            'href',
            $icalExportLink.attr('href').split('?')[0] +
            '?reminder_delta=' + $this.val());
    });
});
