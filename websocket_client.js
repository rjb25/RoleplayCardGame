document.addEventListener('DOMContentLoaded', function(){
    //socketname = prompt("WebSocketURL no http://")
    socketname = "cc6e-108-31-158-123.ngrok-free.app"
    username = prompt("Username:")
    //username = "jason"
    const websocketClient = new WebSocket("wss://"+socketname+"/"+username);
    //const websocketClient = new WebSocket("ws://localhost:12345/");
    const messagesContainer = document.querySelector("#messages_container");
    const situationsContainer = document.querySelector("#situations_container");
    const plansContainer = document.querySelector("#plans_container");
    const victoriesContainer = document.querySelector("#victories_container");
    const card1 = document.querySelector("[name=card1]");
    const card2 = document.querySelector("[name=card2]");
    const card3 = document.querySelector("[name=card3]");
    const card4 = document.querySelector("[name=card4]");
    const card5 = document.querySelector("[name=card5]");
    cardButtons = [card1,card2,card3,card4,card5];
    websocketClient.onopen = function(){
        console.log("Client connected!");
        card1.onclick = function(){
            websocketClient.send(0);
            cardButtons[0].value = "fog";
        };
        card2.onclick = function(){
            websocketClient.send(1);
            cardButtons[1].value = "fog";
        };
        card3.onclick = function(){
            websocketClient.send(2);
            cardButtons[2].value = "fog";
        };
        card4.onclick = function(){
            websocketClient.send(3);
            cardButtons[3].value = "fog";
        };
        card5.onclick = function(){
            websocketClient.send(4);
            cardButtons[4].value = "fog";
        };

        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            messageText = messageJson["text"];
            state = messageJson["state"];

            const messageDiv = document.createElement("div");
            messageDiv.innerHTML = messageText;

            if(messageText){
                messagesContainer.innerHTML = "";
                messagesContainer.appendChild(messageDiv);
            }

            if(state){
                situations = state["situations"];
                plans = state["plans"];
                victories = state["victory"];

                if(victories){
                    victoriesContainer.innerHTML = "";
                    const victoryDiv = document.createElement("div");
                    victoryDiv.innerHTML = victories;
                    victoriesContainer.appendChild(victoryDiv);
                }

                if(situations){
                    situationsContainer.innerHTML = "";
                    situations.forEach((situation) => {
                        const situationDiv = document.createElement("div");
                        situationDiv.innerHTML = JSON.stringify(situation);
                        situationsContainer.appendChild(situationDiv);

                    });
                }

                if(plans){
                    plansContainer.innerHTML = "";
                    plans.forEach((plan) => {
                        const planDiv = document.createElement("div");
                        planDiv.innerHTML = JSON.stringify(plan);
                        plansContainer.appendChild(planDiv);

                    });
                }
            }

            messageJson["hand"].forEach((card, index) => {
                cardButtons[index].value = card;
            });
        };
    };
}, false);
