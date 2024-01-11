document.addEventListener('DOMContentLoaded', function(){
    //socketname = prompt("WebSocketURL no http://")
    socketname = "fda0-108-45-153-120.ngrok-free.app"
    username = prompt("Username:")
    team = "evil"
    enemy_team = "good"
    if(confirm("Join good team? Otherwise join evil.")){
        team = "good"
        enemy_team = "evil"
    }
    //username = "jason"
    const websocketClient = new WebSocket("wss://"+socketname+"/"+username+"/"+team);
    //const websocketClient = new WebSocket("ws://localhost:12345/");
    const messagesContainer = document.querySelector("#messages_container");
    const situationsContainer = document.querySelector("#situations_container");
    const plansContainer = document.querySelector("#plans_container");
    const victoriesContainer = document.querySelector("#victories_container");
    const cardsContainer = document.querySelector("#cards_container");
    const timerContainer = document.querySelector("#timer_container");
    cardButtons = {};
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
            if("played" in messageJson){
                played = messageJson["played"];
                console.log(played);
                if (played in cardButtons){
                    button = cardButtons[played];
                    button.parentNode.removeChild(button);
                }
            }

            if("cards" in messageJson){
                cards = messageJson["cards"];
                cards.forEach((card) => {
                    cardButton = document.createElement("div");
                    cardButton.classList.add("card");
                    cardButton.onclick = function(){
                        websocketClient.send(card["id"]);
                    };
                    cardTitle = document.createTextNode(card["card"]["title"]);
                    cardBase = document.createTextNode(JSON.stringify(card["card"]["base"]));
                    cardButton.appendChild(cardTitle);
                    cardButton.appendChild(cardBase);
                    cardsContainer.appendChild(cardButton);
                    cardButtons[card["id"]] = cardButton;
                });
            }


            if("teams_table" in messageJson){
                team_state = messageJson["teams_table"][team];
                enemy_state = messageJson["teams_table"][enemy_team];
                
                if("plans" in enemy_state){
                    situations = enemy_state["plans"];
                    situationsContainer.innerHTML = "";
                    situations.forEach((situation) => {
                        const situationDiv = document.createElement("div");
                        situationDiv.innerHTML = JSON.stringify(situation);
                        situationsContainer.appendChild(situationDiv);
                    });
                }
                if("text" in team_state){
                    messageText = team_state["text"];
                    const messageDiv = document.createElement("div");
                    messageDiv.innerHTML = messageText;
                    messagesContainer.innerHTML = "";
                    messagesContainer.appendChild(messageDiv);
                }
                if("time" in team_state){
                    time = team_state["time"];
                }
                if("running" in team_state){
                    running = team_state["running"];
                }
                if("victory" in team_state){
                    victories = team_state["victory"];
                    victoriesContainer.innerHTML = "";
                    const victoryDiv = document.createElement("div");
                    victoryDiv.innerHTML = victories;
                    victoriesContainer.appendChild(victoryDiv);
                }


                if("plans" in team_state){
                    plans = team_state["plans"];
                    plansContainer.innerHTML = "";
                    plans.forEach((plan) => {
                        const planDiv = document.createElement("div");
                        planDiv.innerHTML = JSON.stringify(plan);
                        plansContainer.appendChild(planDiv);

                    });
                }
            }

        };
    };
}, false);
