document.addEventListener('DOMContentLoaded', function(){
    //socketname = prompt("WebSocketURL no http://")
    socketname = "50c3-108-31-158-123.ngrok-free.app"
    username = prompt("Username:")
    //username = "jason"
    const websocketClient = new WebSocket("wss://"+socketname+"/"+username);
    //const websocketClient = new WebSocket("ws://localhost:12345/");
    const messagesContainer = document.querySelector("#messages_container");
    const situationsContainer = document.querySelector("#situations_container");
    const plansContainer = document.querySelector("#plans_container");
    const victoriesContainer = document.querySelector("#victories_container");
    const cardsContainer = document.querySelector("#cards_container");
    const card1 = document.querySelector("[name=card1]");
    const card2 = document.querySelector("[name=card2]");
    const card3 = document.querySelector("[name=card3]");
    const card4 = document.querySelector("[name=card4]");
    const card5 = document.querySelector("[name=card5]");
    cardButtons = [card1,card2,card3,card4,card5];
    websocketClient.onopen = function(){
        console.log("Client connected!");

        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            console.log(messageJson);
            messageText = messageJson["text"];
            state = messageJson["state"];
            cards = messageJson["cards"];

            const messageDiv = document.createElement("div");
            messageDiv.innerHTML = messageText;

            if("text" in messageJson){
                messagesContainer.innerHTML = "";
                messagesContainer.appendChild(messageDiv);
            }

            if("state" in messageJson){
                if("victory" in state){
                    victories = state["victory"];
                    victoriesContainer.innerHTML = "";
                    const victoryDiv = document.createElement("div");
                    victoryDiv.innerHTML = victories;
                    victoriesContainer.appendChild(victoryDiv);
                }

                if("situations" in state){
                    situations = state["situations"];
                    situationsContainer.innerHTML = "";
                    situations.forEach((situation) => {
                        const situationDiv = document.createElement("div");
                        situationDiv.innerHTML = JSON.stringify(situation);
                        situationsContainer.appendChild(situationDiv);

                    });
                }

                if("plans" in state){
                    plans = state["plans"];
                    plansContainer.innerHTML = "";
                    plans.forEach((plan) => {
                        const planDiv = document.createElement("div");
                        planDiv.innerHTML = JSON.stringify(plan);
                        plansContainer.appendChild(planDiv);

                    });
                }
            }

            if("cards" in messageJson){
                cards.forEach((card) => {
                    console.log(card);
                    cardButton = document.createElement("button");
                    cardButton.textContent = card["card"]["title"];
                    cardButton.onclick = function(){
                        websocketClient.send(card["id"]);
                        this.parentNode.removeChild(this);
                    };
                    cardsContainer.appendChild(cardButton);
                });
            }
        };
    };
}, false);
