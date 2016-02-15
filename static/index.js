$(document).ready(function(){
    window.mysocket = null;

    var header_text_val = "Real Time Command-Line API"
    var page_header = $.el.div({"class":"page-header"}, $.el.h2({"class":"header-text"}, header_text_val ));
    $("html").prepend(page_header);

    document.getElementById("message-sender").addEventListener("submit", function (e) {
        e.preventDefault();
        var msg = document.getElementById("message-text").value;
        if (!window.mysocket) {
            var re = new RegExp("\/(connect(?=$))","i");
            match = re.exec(msg);
            if (match) {
                WebSocketTest();
            } else {
                append_msg(local_message(msg))
            }
        } else if (window.mysocket) {
            window.mysocket.send(msg);
            append_msg(local_message(msg));
        }

        document.getElementById("message-text").value = "";
    });

    var messageContainer = document.getElementById("messages");

    function doScroll() {
        var height = 0;
        var msg_div = $('#messages');
        msg_div.find(".msg-text").each(function(i, value){
            height += parseInt($(this).height());
            height += parseInt($(this).css("margin-top")) * 2;
        });

        msg_div.animate({scrollTop: String(height)});
    }


    var local_message = function(msg) {
        var d = new Date();
        return d.toTimeString().split(" ")[0] + "." + d.getMilliseconds()  + " Command: " + msg;
    };

    function append_msg(value) {
        $(messageContainer).append($.el.div({'class': 'tim'}, $.el.h3({'class': 'msg-text'}, value)));
        doScroll();
    }

    function gen_random_hashID(salt) {
        var num = Math.floor(Math.random() * 10000000)
        var hashids = new Hashids(salt);
        return hashids.encode(num);
    };

    function WebSocketTest() {
        if ("WebSocket" in window) {
            append_msg("WebSocket is supported by your Browser!");
            var hid_str = gen_random_hashID("I love steak and eggs");
            var ws = new WebSocket("ws://" + window.location.host + "/ws?Id=" + hid_str);

            window.mysocket = ws;

            ws.onopen = function () {
//                    ws.send("Nice to meet you server");
            };
            ws.onmessage = function (evt) {
                var received_msg = evt.data;
                append_msg(received_msg);
            };
            ws.onclose = function () {
                append_msg("Connection is closed...");
                delete window.mysocket;
                ws = undefined;
            };
        } else {
            messageContainer.innerHTML = "WebSocket NOT supported by your Browser!";
        }
    }
});