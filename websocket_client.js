document.addEventListener('DOMContentLoaded', function(){
    socketname = prompt()
    const websocketClient = new WebSocket("wss://"+socketname);
    //const websocketClient = new WebSocket("ws://localhost:12345/");
    const messagesContainer = document.querySelector("#message_container");
    const messageInput = document.querySelector("[name=message_input]");
    const sendMessageButton = document.querySelector("[name=send_message_button]");
    websocketClient.onopen = function(){
        console.log("Client connected!");
        sendMessageButton.onclick = function(){
            websocketClient.send(messageInput.value);
        };

        websocketClient.onmessage = function(message){
            const newMessage = document.createElement("div");
            newMessage.innerHTML = message.data;
            messagesContainer.appendChild(newMessage);
        };
    };
}, false);
