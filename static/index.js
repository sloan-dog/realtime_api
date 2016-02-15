$(document).ready(function(){
    window.mysocket = null;

    document.getElementById("message-sender").addEventListener("submit", function (e) {
        e.preventDefault();
        var msg = document.getElementById("message-text").value;
        window.mysocket.send(msg);
        var d = new Date();
        var local_message = d.toTimeString().split(" ")[0] + "." + d.getMilliseconds()  + " Command: " + msg;
        append_msg(local_message);
        document.getElementById("message-text").value = "";
    });

    var messageContainer = document.getElementById("messages");
    var openSocketBtn = $.el.a({"href":"","class":"big-link","id":"open-socket-btn"},"Open WebSocket");
    $(openSocketBtn).on("click", function(e){
        e.preventDefault();
        WebSocketTest();
    });
    $(openSocketBtn).insertBefore(messageContainer);

    function append_msg(value) {
        $(messageContainer).append($.el.div({'class': 'tim'}, $.el.h3({'class': 'msg-text'}, value)));
    }

    function gen_random_hashID(salt) {
        var num = Math.floor(Math.random() * 10000000)
        var hashids = new Hashids(salt);
        return hashids.encode(num);
    };

    function WebSocketTest() {
        if ("WebSocket" in window) {
            messageContainer.innerHTML = "WebSocket is supported by your Browser!";
            var hid_str = gen_random_hashID("I love steak and eggs");
            var ws = new WebSocket("ws://localhost:9000/ws?Id=" + hid_str);

            window.mysocket = ws;

            ws.onopen = function () {
//                    ws.send("Nice to meet you server");
            };
            ws.onmessage = function (evt) {
                var received_msg = evt.data;
                append_msg(received_msg);
            };
            ws.onclose = function () {
                messageContainer.innerHTML = "Connection is closed...";
            };
        } else {
            messageContainer.innerHTML = "WebSocket NOT supported by your Browser!";
        }
    }
});