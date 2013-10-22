// define additional culture information for a possibly existing culture
Globalize.addCultureInfo( "fedocal", {
    calendars: {
        standard: {
            patterns: {
                t: 'HH:mm'
            }
        }
    }
});
Globalize.culture("fedocal");

$.widget( "ui.timespinner", $.ui.spinner, {
    options: {
        // half an hour
        step: 30 * 60 * 1000,
        // hours
        page: 60
    },

    _parse: function( value ) {
        if ( typeof value === "string" ) {
            // already a timestamp
            if ( Number( value ) == value ) {
                return Number( value );
            }
            return +Globalize.parseDate( value );
        }
        return value;
    },

    _format: function( value ) {
        return Globalize.format( new Date(value), "t" );
    }
});
