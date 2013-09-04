$(document).ready(function() {
    adjustContentsHeight();
});

$(window).resize(function() {
    adjustContentsHeight();
});
function adjustContentsHeight() {
    //	var pageheight = $(window).height() - 100;
    //	var pagewidth = $(window).width() - 2;
    //	$(".page").css("height", pageheight);
    //	$(".page").css("width", pagewidth);

    //	var r = Math.sqrt(Math.pow(pageheight, 2) + Math.pow(pagewidth, 2));
    //	$(".mask").css("width", r).css("height", r);

}

//$("#bfpage").live('mousemove', pageflip);
$("#maskarea").live('mousemove', pageflip);

function pageflip(evt) {
    var boundY = $(".page").height() + 50;
    var boundX = $(".page").width();
    var maskY = $('.mask').height();
    var maskX = $('.mask').width();
    var radval = Math.atan((boundY - evt.pageY) / (boundX - evt.pageX));

    $("#T0").css("top", (boundY + evt.pageY) / 2).css("left", (boundX + evt.pageX) / 2);

    $("#T1").css("top", boundY).css("left", (boundX + evt.pageX) / 2);

    var t2x = (boundX + evt.pageX) / 2 - (boundY - evt.pageY) / (boundX - evt.pageX) * ((boundY - evt.pageY) / 2);
    if(t2x < 0)
        t2x = 0;

    $("#T2").css("top", boundY).css("left", t2x);

    var toriY = (boundY - 50) - (Math.cos(radval) * (maskY - boundX) + Math.sin(radval) * maskX);
    var toriX = Math.sin(radval) * (maskY - boundX) - Math.cos(radval) * maskX + t2x;

    $("#deg1").attr("value", toriY);
    $("#deg2").attr("value", toriX);

    $("#C0").css("top", toriY).css("left", toriX);

    var sorigin = toriX + "px " + toriY + "px";
    var srotate = "translate(" + toriX + "px, " + toriY + "px) rotate(" + radval + "rad)";
    $(".mask").css("-webkit-transform", srotate);
}