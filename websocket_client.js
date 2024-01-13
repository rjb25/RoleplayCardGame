document.addEventListener('DOMContentLoaded', function(){
    //socketname = prompt("WebSocketURL no http://")
    socketname = "e6d6-108-45-153-120.ngrok-free.app"
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
    const goldContainer = document.querySelector("#gold_container");
    const cardsContainer = document.querySelector("#cards_container");
    const timerContainer = document.querySelector("#timer_container");
    const healthContainer = document.querySelector("#health_container");
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
    function generateCard(card){
        cardButton = document.createElement("div");
        cardButton.classList.add("card");
        cardTitle = document.createElement("div");
        cardTitle.innerHTML =  card["title"] + " $" + card["cost"] + " ST" + card["stability"];
        cardBase = document.createElement("div");
        enter_effect = card["enter"][0];
        enter_text = enter_effect["function"] + " " + enter_effect["target"] + " " + enter_effect["amount"];
        progress_effect = card["progress"][0];
        progress_text = progress_effect["function"] + " " + progress_effect["target"] + " " + progress_effect["amount"];
        exit_effect = card["exit"][0];
        exit_text = exit_effect["function"] + " " + exit_effect["target"] + " " + exit_effect["amount"];
        cardBase.innerHTML = enter_text + "<br>" + progress_text + "<br>" + exit_text;
        cardButton.appendChild(cardTitle);
        cardButton.appendChild(cardBase);
        return cardButton;
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
                played.forEach((card) => {
                    if (card in cardButtons){
                        button = cardButtons[card];
                        button.parentNode.removeChild(button);
                        delete cardButtons[card];
                    }
                });
            }


            if("gold" in messageJson){
                gold = messageJson["gold"];
                goldContainer.innerHTML = "";
                const goldDiv = document.createElement("div");
                goldDiv.innerHTML = gold;
                goldContainer.appendChild(goldDiv);
            }

            if("player_table" in messageJson){
                //Myself
                playerState = messageJson["player_table"]
                if ("gold" in playerState){
                    gold = playerState["gold"];
                    goldContainer.innerHTML = "";
                    const goldDiv = document.createElement("div");
                    goldDiv.innerHTML = gold;
                    goldContainer.appendChild(goldDiv);
                }
                if("hand" in playerState){
                    hand = playerState["hand"];
                    newCards = [];
                    hand.forEach((card) => {
                        if (!(card["id"] in cardButtons)){
                            newCards.push(card);
                        }
                    });
                    console.log(newCards)

                    newCards.forEach((card) => {
                        cardButton = generateCard(card)
                        cardButton.onclick = function(){
                            websocketClient.send(card["id"]);
                        };
                        cardsContainer.appendChild(cardButton);
                        cardButtons[card["id"]] = cardButton;
                    });
                }
            }

            if("teams_table" in messageJson){
                teamState = messageJson["teams_table"][team];
                enemyState = messageJson["teams_table"][enemy_team];
                
                //Enemy
                if("plans" in enemyState){
                    plans = enemyState["plans"];
                    situationsContainer.innerHTML = "";
                    plans.forEach((plan) => {
                        planDiv = document.createElement("div");
                        plan.forEach((card) => {
                        cardBox = generateCard(card);
                        planDiv.appendChild(cardBox);
                        });
                        situationsContainer.appendChild(planDiv);
                    });
                }

                //My team
                if("text" in teamState){
                    messageText = teamState["text"];
                    const messageDiv = document.createElement("div");
                    messageDiv.innerHTML = messageText;
                    messagesContainer.innerHTML = "";
                    messagesContainer.appendChild(messageDiv);
                }
                if("time" in teamState){
                    time = teamState["time"];
                }
                if("health" in teamState){
                    messageText = teamState["health"];
                    const messageDiv = document.createElement("div");
                    messageDiv.innerHTML = messageText;
                    healthContainer.innerHTML = "";
                    healthContainer.appendChild(messageDiv);
                }
                if("running" in teamState){
                    running = teamState["running"];
                }


                if("plans" in teamState){
                    plans = teamState["plans"];
                    plansContainer.innerHTML = "";
                    plans.forEach((plan) => {
                        planDiv = document.createElement("div");
                        plan.forEach((card) => {
                        cardBox = generateCard(card);
                        planDiv.appendChild(cardBox);
                        });
                        plansContainer.appendChild(planDiv);
                    });
                }
            }

        };
    };
}, false);
