my_team = "good";
enemy_team = "evil";
actionColors = {"damage":"rgba(255, 0, 0, 0.8)", "destabilize":"rgba(100, 55, 55, 0.8)"};
var running = false;
var target = 0;
socketname = "visually-popular-iguana.ngrok-free.app";
messagesContainer =   "#messages_container";
situationsContainer = "#situations_container";
goldContainer =       "#gold_container";
menuContainer =       "#menu_container";
inspectContainer =       "#inspect_container";
healthContainer =     "#health_container";
//These need to be variables
buttonContainers = ["#situations_container", "#plans_container", "#cards_container"];
buttonContainerNames = [enemy_team,my_team,"hand"];
menuButtons = ["reset_game","pause","add_ai_evil","add_ai_good","join_good","join_evil"];
//This is what you run if you want to reconnect to server
//socketname = prompt("WebSocketURL no http://")
const websocketClient = new WebSocket("wss://"+socketname);

function pause(){
    changeBackground("red");
}
function join_good(){
    console.log("goodness")
    my_team = "good"
    enemy_team = "evil"
    buttonContainerNames = [enemy_team,my_team,"hand"];
}
function join_evil(){
    console.log("evilness")
    my_team = "evil"
    enemy_team = "good"
    buttonContainerNames = [enemy_team,my_team,"hand"];
}
function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  ev.dataTransfer.setData("text", ev.target.id);
}

function findAncestor (el, cls) {
    if (el.classList.contains(cls)){
        return el;
    }
    while ((el = el.parentElement) && !el.classList.contains(cls));
    return el;
}

function drop(ev) {
    ev.preventDefault();
    var cardId = ev.dataTransfer.getData("text");
    nestedTarget = ev.target;
    target = findAncestor(nestedTarget, "slot");
    container = findAncestor(nestedTarget, "playable");
    if(container) {
        play(cardId,target.getAttribute("spot"));
    }
}
function play(cardId,targ){
    websocketClient.send( JSON.stringify({
        id: cardId,
        index: targ
    }));
};
function changeBackground(color) {
    document.body.style.background = color;
}
function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}
function makeMenuButton(title) {
    menuButton = document.createElement("div");
    menuButton.classList.add("menu");
    menuTitle = document.createElement("div");
    menuTitle.innerHTML = title;
    menuButton.appendChild(menuTitle);
    menuButton.onclick = function(){
        websocketClient.send( JSON.stringify({
        command: title
        }))
        console.log("called function " + title)
        console.log(window)
        if (window[title]){
            console.log("called extra function " + title)
            window[title]();
        }
    };
    fetch(menuContainer).appendChild(menuButton);
}
function inspect(slot){
    cardButton = slot.querySelector('.card')
    if(cardButton){
        card = cardButton.card;
        if(card){
            triggersText = ""
            Object.entries(card["triggers"]).forEach(([triggerType,events]) => {
                events.forEach((eventDict) => {
                    triggersText += triggerType;
                    if (eventDict["goal"]) {
                        triggersText += " length:" + eventDict["goal"];
                    }
                    triggersText += "<br>";
                    eventDict["actions"].forEach((action) => {
                        triggersText += "&nbsp;&nbsp;&nbsp;&nbsp;" + action["function"] + " " + action["target"];
                        if (action["amount"]) {
                            triggersText += " " + action["amount"];
                        }
                        triggersText += "<br>";
                    });
                });
            });
            fetch(inspectContainer).innerHTML = triggersText ;
        }
    }
}
function updateCardButton(cardButton,card){
    cardButton.card = card;
    health = cardButton.querySelector(".health");
    cardCoinImage = cardButton.querySelector(".coin");
    cost = cardButton.querySelector(".cost");
    if(card["location"] == "hand"){
        cost.innerHTML =  card["cost"];
    } else {
        //health.innerHTML = "&hearts;".repeat(Math.max(card["stability"],0));
        percent = 100 * card["stability"] / card["max_stability"] ;
        health.style.width = percent +"%";
        //target = findAncestor(nestedTarget, "slot");
        if (percent > 75){
            health.style.background = "rgba(0, 255, 0, 0.8)";
        } else if (percent > 40){
            health.style.background = "rgba(255, 255, 0, 0.8)";
        } else {
            health.style.background = "rgba(255, 0, 0, 0.8)";
        }

        cost.innerHTML = "";
        cardCoinImage.style.display = "none";
    }
    currentBottom = 0;
    //Should be reversed at some point to match input data
    Object.entries(card["triggers"]).forEach(([triggerType,events]) => {
        events.forEach((eventDict,i) => {
            if(eventDict["goal"]){
                progressBars = cardButton.querySelectorAll(".progress");
                progressBar = progressBars[i];
                firstAction = eventDict["actions"][0];
                height = 2 + firstAction["amount"];
                progressBar.style.height = height + "px";
                progressBar.style.bottom = currentBottom + "px";
                currentBottom += height;
                percent = 100 * eventDict["progress"] / eventDict["goal"] 
                if (percent < 0.1){
                    percent = 100;
                }
                progressBar.style.width = percent +"%";
                color = actionColors[firstAction["function"]];
                if (!color){
                    color = "black";
                }
                progressBar.style.background = color;
            }
        });
    });
}
function generateCardButton(card){
    cardButton = document.createElement("div");
    cardButton.id = card["id"]
    cardButton.classList.add("card");
    cardImage = new Image();
    cardImage.classList.add("picture");
    cardImage.src = "pics/" + card["title"]+".png";
    cardImage.alt = card["title"];
    cardImage.draggable = true;
    cardImage.setAttribute("ondragstart", "drag(event)");
    cardImage.id = card["id"];

    cost = document.createElement("p");
    cost.classList.add("cost");
    coinImage = new Image();
    coinImage.draggable = false;
    coinImage.classList.add("coin");
    coinImage.src = "pics/" + "coin3.png";
    coinImage.alt = "coin";

    health = document.createElement("div");
    health.classList.add("health");

    cardButton.appendChild(cardImage);
    cardButton.appendChild(health);
    cardButton.appendChild(coinImage);
    cardButton.appendChild(cost);

    Object.entries(card["triggers"]).forEach(([triggerType,events]) => {
        events.forEach((eventDict) => {
            if (eventDict["goal"]){
                progressBar = document.createElement("div");
                progressBar.classList.add("progress");
                cardButton.appendChild(progressBar);
            }
        });
    });
    updateCardButton(cardButton,card);
    return cardButton;
}
function createSlots(container){
    for (let i = 0; i < 5; i++){
        slot = document.createElement("div");
        skullImage = new Image();
        skullImage.classList.add("picture");
        skullImage.src = "pics/" + "skull.png";
        skullImage.alt = "skull";
        skullImage.draggable = false;
        slot = document.createElement("div");
        slot.setAttribute("spot", i);
        slot.classList.add("slot");
        slot.setAttribute("ondrop","drop(event)");
        slot.setAttribute("ondragover","allowDrop(event)");
        slot.onclick = function(){
            inspect(this);
        };
        //slot.append(skullImage);
        fetch(container).append(slot);
    }
}

function updateSlots(container,messageJson,containerName){
    newCards = messageJson[containerName];
    newCards.forEach((newCard,i) => {
            slot = container.childNodes[i];
            oldCardButton = slot.querySelector(".card");
            oldId = 0;
            newId = 0;
            if (oldCardButton) {
                oldId = oldCardButton["id"];
            } 
            if (newCard) {
                newId = newCard["id"];
            }
            //Replace or delete
            if(newId != oldId){
                if(newId){
                    newCardButton = generateCardButton(newCard);
                    slot.append(newCardButton);
                    if (oldCardButton){
                        oldCardButton.remove();
                    }
                } else {
                    if (oldCardButton){
                        oldCardButton.remove();
                    }
                }
            } else {
                //Update
                if(newCard){
                    updateCardButton(oldCardButton,newCard);
                }
            }
        });
}
function fetch(id){
    return document.querySelector(id);
}

document.addEventListener('DOMContentLoaded', function(){
    //HAVE A list of targets under an attack cards with the images of what's being targetted. Pulse green for good things red for bad targets.
    changeBackground("black");
    buttonContainers.forEach(createSlots);
    menuButtons.forEach(makeMenuButton);
    websocketClient.onopen = function(){
        console.log("Client connected!");
        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            //console.log(JSON.stringify(messageJson));
            buttonContainers.forEach(function (container,index){ 
                updateSlots(fetch(container),messageJson,buttonContainerNames[index]);
            });

            if("player_state" in messageJson){
                //Myself
                playerState = messageJson["player_state"]
                if ("gold" in playerState){
                    gold = playerState["gold"];
                    fetch(goldContainer).innerHTML = "";
                    const goldDiv = document.createElement("div");
                    goldDiv.innerHTML = "&#128176;" + gold;
                    fetch(goldContainer).appendChild(goldDiv);
                }
            }

            if("teams_table" in messageJson){
                teamState = messageJson["teams_table"][my_team];
                enemyState = messageJson["teams_table"][enemy_team];
                //My team
                if("text" in teamState){
                    messageText = teamState["text"];
                    const messageDiv = document.createElement("div");
                    messageDiv.innerHTML = messageText;
                    fetch(messagesContainer).innerHTML = "";
                    fetch(messagesContainer).appendChild(messageDiv);
                }
                if("health" in teamState){
                    myText = teamState["health"];
                    enemyText = enemyState["health"];
                    const messageDiv = document.createElement("div");
                    messageDiv.innerHTML = "Ally &hearts;" + myText + ".    Enemy &hearts;" +enemyText;
                    fetch(healthContainer).innerHTML = "";
                    fetch(healthContainer).appendChild(messageDiv);
                }

            }
            if("game_table" in messageJson){
                gameTable = messageJson["game_table"];
                running = gameTable["running"];
                if (running) {
                    changeBackground("black");
                } else {
                    changeBackground("red");
                }
            }
        };
    };
}, false);
