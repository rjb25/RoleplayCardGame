my_team = "good"
enemy_team = "evil"
oldBoards = {"good":[0,0,0,0,0], "evil":[0,0,0,0,0]}
oldHand = [0,0,0,0,0]
function join_good(){
    console.log("goodness")
    my_team = "good"
    enemy_team = "evil"
}
function join_evil(){
    console.log("evilness")
    my_team = "evil"
    enemy_team = "good"
}
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

      event.preventDefault();
    }, true);
    //socketname = prompt("WebSocketURL no http://")
    socketname = "visually-popular-iguana.ngrok-free.app"
    //This is what you run if you want to reconnect to server
    const websocketClient = new WebSocket("wss://"+socketname);
    const messagesContainer = document.querySelector("#messages_container");
    const situationsContainer = document.querySelector("#situations_container");
    const plansContainer = document.querySelector("#plans_container");
    const goldContainer = document.querySelector("#gold_container");
    const cardsContainer = document.querySelector("#cards_container");
    const menuContainer = document.querySelector("#menu_container");
    const timerContainer = document.querySelector("#timer_container");
    const healthContainer = document.querySelector("#health_container");
    containers = { "good": plansContainer, "evil": situationsContainer};

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
            console.log("called function" + title)
            console.log(window)
            if (window[title]){
                console.log("called extra function " + title)
                window[title]();
            }
        };
        menuContainer.appendChild(menuButton);
    }
    makeMenuButton("pause");
    makeMenuButton("add_ai_evil");
    makeMenuButton("add_ai_good");
    makeMenuButton("join_good");
    makeMenuButton("join_evil");
    function generateCard(card){
        cardButton = document.createElement("div");
        cardButton.id = card["id"]
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
    for([team, container] of Object.entries(containers)){
        for (let i = 0; i < 5; i ++){
            cardDiv = document.createElement("div");
            cardBox = generateCard(0);
            cardDiv.appendChild(cardBox);
            container.append(cardDiv);
        }
    }
    for (let i = 0; i < 5; i ++){
        cardDiv = document.createElement("div");
        cardBox = generateCard(0);
        cardDiv.appendChild(cardBox);
        cardsContainer.append(cardDiv);
    }
    websocketClient.onopen = function(){
        console.log("Client connected!");

        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            //console.log(JSON.stringify(messageJson));

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
                    newHand = playerState["hand"];

                    newHand.forEach((card,i) => {
                        if(oldHand[i]["id"] != card["id"]){
                            cardDiv = document.createElement("div");
                            cardBox = generateCard(card);
                            cardBox.onclick = function(){
                                websocketClient.send( JSON.stringify({
                                id: card["id"],
                                index: target
                                }));
                                target++;
                                target = target % 5;
                            };
                            cardDiv.appendChild(cardBox);
                            cardsContainer.childNodes[i].replaceWith(cardDiv);
                            cardButtons[card["id"]] = cardBox;
                        }
                    });
                    oldHand = newHand;
                }
            }

            if("teams_table" in messageJson){
                teamTable = messageJson["teams_table"];
                teamState = messageJson["teams_table"][my_team];
                //Enemy
                //TODO make this not fail so hard
                for([team, container] of Object.entries(containers)){
                    oldBoard = oldBoards[team]
                    newBoard = teamTable[team]["board"];
                    for (let i = 0; i < oldBoard.length; i ++){
                        if(oldBoard[i]["id"] != newBoard[i]["id"]){
                            cardDiv = document.createElement("div");
                            cardBox = generateCard(newBoard[i]);
                            cardDiv.appendChild(cardBox);
                            container.childNodes[i].replaceWith(cardDiv);
                        }
                    }
                    oldBoards[team] = newBoard

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

            }

        };
    };
}, false);
