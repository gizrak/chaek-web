/**
 * Toast Message
 */
function toast(type, text) {
    var ui_state = 'ui-state-highlight';
    var ui_icon = 'ui-icon-info';
    var animation = 'pulsate';
    if(type == 'error') {
        ui_state = 'ui-state-error';
        ui_icon = 'ui-icon-alert';
        animation = 'bounce';
    }

    var message = '<div class="' + ui_state + ' ui-corner-all" style="padding: 0 .7em;">';
    message += '  <p><span class="ui-icon ' + ui_icon + '" style="float: left; margin-right: .3em;"></span>' + text + '</p>';
    message += '</div>';
    $('#message').html(message).show(animation);
}