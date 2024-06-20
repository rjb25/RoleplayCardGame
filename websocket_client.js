
document.addEventListener('DOMContentLoaded', function(){
    window.addEventListener("keydown", function (event) {
      if (event.defaultPrevented) {
        return; // Do nothing if the event was already processed
      }
        number = Number(event.key);
        if(number > 0 && number < 6){
            target = number-1;
        }
        console.log(number)

    // Cancel the default action to avoid it being handled twice
      event.preventDefault();
    }, true);
    //socketname = prompt("WebSocketURL no http://")
    socketname = "visually-popular-iguana.ngrok-free.app"
    username = prompt("Username:")
    team = "evil"
    enemy_team = "good"
    if(confirm("Join good team? Otherwise join evil.")){
        team = "good"
        enemy_team = "evil"
    }
    //This is what you run if you want to reconnect to server
    const websocketClient = new WebSocket("wss://"+socketname+"/"+username+"/"+team);
    const messagesContainer = document.querySelector("#messages_container");
    const situationsContainer = document.querySelector("#situations_container");
    const plansContainer = document.querySelector("#plans_container");
    const goldContainer = document.querySelector("#gold_container");
    const cardsContainer = document.querySelector("#cards_container");
    const menuContainer = document.querySelector("#menu_container");
    const timerContainer = document.querySelector("#timer_container");
    const healthContainer = document.querySelector("#health_container");
    cardButtons = {};
    function changeBackground(color) {
        document.body.style.background = color;
    }
    var time = 0;
    var target = 0;
    var running = false;
    changeBackground("red");
    var timer = setInterval(function(){
        timerContainer.innerHTML = "&#8987;" + time;
        if(running){
            time = Math.max(time - 1,0);
        }
    }, 1000);
    function removeAllChildNodes(parent) {
        while (parent.firstChild) {
            parent.removeChild(parent.firstChild);
        }
    }
    function makeMenuButton(title) {
        menuButton = document.createElement("div");
        menuButton.classList.add("card");
        menuTitle = document.createElement("div");
        menuTitle.innerHTML = title;
        menuButton.appendChild(menuTitle);
        menuButton.onclick = function(){
            websocketClient.send( JSON.stringify({
            command: title
            }))
        };
        menuContainer.appendChild(menuButton);
    }
    makeMenuButton("pause");
    makeMenuButton("add_ai_evil");
    makeMenuButton("add_ai_good");
    function generateCard(card){
        cardButton = document.createElement("div");
        cardButton.classList.add("card");
        cardTitle = document.createElement("div");
        cardBase = document.createElement("div");
        //TODO make targetting an image
        if (card) {
            cardTitle.innerHTML =  card["title"] + " &#128176;" + card["cost"] + " &hearts;" + card["stability"];
            enter_effect = card["enter"][0];
            enter_text = enter_effect["function"] + " " + enter_effect["target"] + " " + enter_effect["amount"];
            progress_effect = card["progress"][0];
            progress_text = progress_effect["function"] + " " + progress_effect["target"] + " " + progress_effect["amount"];
            exit_effect = card["exit"][0];
            exit_text = exit_effect["function"] + " " + exit_effect["target"] + " " + exit_effect["amount"];
            cardBase.innerHTML = enter_text + "<br>" + progress_text + "<br>" + exit_text;
        }
        cardButton.appendChild(cardTitle);
        cardButton.appendChild(cardBase);
        return cardButton;
    }
    websocketClient.onopen = function(){
        console.log("Client connected!");

        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            //console.log(JSON.stringify(messageJson));
                /*

            if("log" in messageJson){
                log = messageJson["log"];
                if (log){
                    console.log(log);
                }
            }
            */

            if("player_state" in messageJson){
                //Myself
                playerState = messageJson["player_state"]
                if ("gold" in playerState){
                    gold = playerState["gold"];
                    goldContainer.innerHTML = "";
                    const goldDiv = document.createElement("div");
                    goldDiv.innerHTML = "&#128176;" + gold;
                    goldContainer.appendChild(goldDiv);
                }
                if("hand" in playerState){
                    cardsContainer.innerHTML = "";
                    removeAllChildNodes(cardsContainer);
                    cardButtons = {};
                    hand = playerState["hand"];

                    hand.forEach((card) => {
                        cardDiv = document.createElement("div");
                        cardBox = generateCard(card)
                        cardBox.onclick = function(){
                            websocketClient.send( JSON.stringify({
                            id: card["id"],
                            index: target
                            }));
                            target++;
                            target = target % 5;
                        };
                        cardDiv.appendChild(cardBox);
                        cardsContainer.appendChild(cardDiv);
                        cardButtons[card["id"]] = cardBox;
                    });
                }
            }

            if("teams_table" in messageJson){
                teamState = messageJson["teams_table"][team];
                enemyState = messageJson["teams_table"][enemy_team];
                
                //Enemy
                if("board" in enemyState){
                    board = enemyState["board"];
                    situationsContainer.innerHTML = "";
                    board.forEach((card) => {
                        cardDiv = document.createElement("div");
                        cardBox = generateCard(card);
                        cardDiv.appendChild(cardBox);
                        situationsContainer.appendChild(cardDiv);
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
                    messageDiv.innerHTML = "&hearts;" + messageText;
                    healthContainer.innerHTML = "";
                    healthContainer.appendChild(messageDiv);
                }
                if("running" in teamState){
                    running = teamState["running"];
                    if (running) {
                        changeBackground("green");
                    } else {
                        changeBackground("red");
                    }
                }

                if("board" in teamState){
                    board = teamState["board"];
                    plansContainer.innerHTML = "";
                    board.forEach((card) => {
                        cardDiv = document.createElement("div");
                        cardBox = generateCard(card);
                        cardDiv.appendChild(cardBox);

                        plansContainer.appendChild(cardDiv);
                    });
                }
            }

        };
    };
}, false);
