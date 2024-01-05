document.addEventListener('DOMContentLoaded', function(){
    //socketname = prompt("WebSocketURL no http://")
    socketname = "67cb-108-31-158-123.ngrok-free.app"
    username = prompt("Username:")
    //username = "jason"
    const websocketClient = new WebSocket("wss://"+socketname+"/"+username);
    //const websocketClient = new WebSocket("ws://localhost:12345/");
    const messagesContainer = document.querySelector("#messages_container");
    const situationsContainer = document.querySelector("#situations_container");
    const plansContainer = document.querySelector("#plans_container");
    const victoriesContainer = document.querySelector("#victories_container");
    const cardsContainer = document.querySelector("#cards_container");
    const timerContainer = document.querySelector("#timer_container");
    var time = 0;
    var running = false;
    var timer = setInterval(function(){
        timerContainer.innerHTML = time;
        if(running){
            time = Math.max(time - 1,0);
        }
    }, 1000);
    function removeAllChildNodes(parent) {
        while (parent.firstChild) {
            parent.removeChild(parent.firstChild);
        }
    }
    websocketClient.onopen = function(){
        console.log("Client connected!");

        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            console.log(JSON.stringify(messageJson));
            if("reset" in messageJson){
                reset = messageJson["reset"];
                if (reset){
                    removeAllChildNodes(cardsContainer);
                }
            }

            if("time" in messageJson){
                time = messageJson["time"];
            }
            if("running" in messageJson){
                running = messageJson["running"];
            }

            if("text" in messageJson){
                messageText = messageJson["text"];
                const messageDiv = document.createElement("div");
                messageDiv.innerHTML = messageText;
                messagesContainer.innerHTML = "";
                messagesContainer.appendChild(messageDiv);
            }

            if("state" in messageJson){
                state = messageJson["state"];
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
                cards = messageJson["cards"];
                cards.forEach((card) => {
                    cardButton = document.createElement("button");
                    cardButton.textContent = card["card"]["title"];
                    cardButton.onclick = function(){
                        websocketClient.send(card["id"]);
                        this.parentNode.removeChild(this);
                        running = true;
                    };
                    cardsContainer.appendChild(cardButton);
                });
            }
        };
    };
}, false);
