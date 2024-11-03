my_team = "good";
enemy_team = "evil";
firstUpdate = 1;
tr = " 0.7)";
actionColors = {"damage":"rgba(255, 0, 0," + tr, "finish":"rgba(255, 255, 255," +tr, "income":"rgba(255, 255, 0," +tr,"draw":"rgba(0, 255, 0," +tr};
var running = false;
var target = 0;
socketname = "visually-popular-iguana.ngrok-free.app";
//These need to be variables
buttonContainers = ["#enemy_base_container","#situations_container", "#ally_base_container", "#plans_container", "#tent_container","#cards_container","#discard_container"];
buttonContainerLocations = ["base","board","base","board","tent","hand","discard"];
buttonContainerNames = [enemy_team,enemy_team,my_team,my_team,"me","me","me"];
menuButtons = ["remove_ai","win_game","reset_game","pause","add_ai_evil","add_ai_good","join_good","join_evil","game_log"];
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
    buttonContainerNames = [enemy_team,enemy_team,my_team,my_team,"me","me","me"];
}
function join_evil(){
    console.log("evilness")
    my_team = "evil"
    enemy_team = "good"
    buttonContainerNames = [enemy_team,enemy_team,my_team,my_team,"me","me","me"];
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
        play(cardId,target.getAttribute("spot"),target.getAttribute("location"));
    }
}
function play(cardId,targ, locat){
    websocketClient.send( JSON.stringify({
        id: cardId,
        index: targ,
        location: locat
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
    fetch("#menu_container").appendChild(menuButton);
}
function inspect(slot){
    cardButton = slot.querySelector('.card')
    if(cardButton){
        card = cardButton.card;
        if(card){
            infoText = "Health: " + card["health"] + "<br>Cost:" + card["cost"] + "<br>";
            
            triggersText = "";
            Object.entries(card["triggers"]).forEach(([triggerType,events]) => {
                events.forEach((eventDict) => {
                    triggersText += triggerType;
                    if (eventDict["goal"]) {
                        triggersText += " length:" + eventDict["goal"];
                    }
                    triggersText += "<br>";
                    eventDict["actions"].forEach((action) => {
                        triggersText += "&nbsp;&nbsp;&nbsp;&nbsp;" + action["action"] + " " + action["target"];
                        if (action["amount"]) {
                            triggersText += " " + action["amount"];
                        }
                        triggersText += "<br>";
                    });
                });
            });
            fetch("#inspect_container").innerHTML = infoText + triggersText ;
        }
    }
}
function updateCardButton(cardButton,card){
    cardButton.card = card;
    health = cardButton.querySelector(".health");
    cardCoinImage = cardButton.querySelector(".coin");
    skullImage = cardButton.querySelector(".skull");
    cost = cardButton.querySelector(".cost");
    if(card["location"] == "tent"){
        bank = cardButton.querySelector(".bank");
        bank.innerHTML = card["gold"];
    }
    if(card["location"] == "hand" && "cost" in card){
        cost.innerHTML = card["cost"];
        mContainer = fetch("#messages_container");
        if (mContainer.playerState){
            money = mContainer.playerState["gold"];
            if (card["cost"] > money){
                cost.style.color = "crimson";
            }else{
                cost.style.color = "black";
            }
        }
    } else {
        percent = 100 * card["health"] / card["max_health"] ;
        health.style.width = Math.max(percent,0) +"%";
        if (percent > 75){
            health.style.background = "rgba(0, 255, 0, 0.8)";
        } else if (percent > 40){
            health.style.background = "rgba(255, 255, 0, 0.8)";
        } else if (percent > 0){
            health.style.background = "rgba(255, 0, 0, 0.8)";
        } else {
            if(card["location"] != "tent"){
                skullImage.style.display = "";
            }
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
                amount = 0;
                if(firstAction["amount"]){
                    amount = firstAction["amount"];
                }
                height = 2 + Math.max(amount,0);
                progressBar.style.height = height + "px";
                progressBar.style.bottom = currentBottom + "px";
                currentBottom += height;
                percent = 100 * eventDict["progress"] / eventDict["goal"] 
                progressBar.style.width = percent +"%";
                color = actionColors[firstAction["action"]];
                if (!color){
                    color = "white";
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

    skullImage = new Image();
    skullImage.classList.add("skull");
    skullImage.classList.add("picture");
    skullImage.src = "pics/" + "skull.png";
    skullImage.alt = "skull";
    skullImage.draggable = false;
    skullImage.style.display = "none";

    health = document.createElement("div");
    health.classList.add("health");

    cardButton.appendChild(cardImage);
    cardButton.appendChild(health);
    cardButton.appendChild(coinImage);
    cardButton.appendChild(cost);
    cardButton.append(skullImage);

    if (card["location"] == "tent"){
        bank = document.createElement("p");
        bank.classList.add("bank");
        sackImage = new Image();
        sackImage.classList.add("coin");
        sackImage.src = "pics/" + "coin3.png";
        sackImage.alt = "sack";
        sackImage.draggable = false;
        cardButton.appendChild(sackImage);
        cardButton.appendChild(bank);
    }

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

function createSlots(container, length, location){
    for (let i = 0; i < length; i++){
        slot = document.createElement("div");
        slot.setAttribute("spot", i);
        slot.setAttribute("location", location);
        slot.classList.add("slot");
        slot.setAttribute("ondrop","drop(event)");
        slot.setAttribute("ondragover","allowDrop(event)");
        slot.onclick = function(){
            inspect(this);
        };
        container.append(slot);
    }
}

function updateSlots(container, messageJson, name, location){
    newCards = []
    if (name == "me"){
        name = messageJson["me"]
    }
    try{
        newCards = messageJson["game_table"]["entities"][name]["locations"][location];
    } catch (e) {
        console.log("yi")
        console.log(buttonContainerNames)
        console.log(e)
        console.log(messageJson)
        console.log(messageJson["game_table"]["entities"])
        console.log(name)
        console.log(location)
        console.log("kes")
    }
    if (location == "discard"){
        newCards = [];
    }

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
    websocketClient.onopen = function(){
        console.log("Client connected!");
        websocketClient.onmessage = function(message){
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            //console.log(messageJson);
            if(firstUpdate){
                changeBackground("black");
                buttonContainers.forEach(function (container,index){ 
                    name = buttonContainerNames[index]
                    local = buttonContainerLocations[index]
                    if (name == "me"){
                        name = messageJson["me"]
                    }
                    length = messageJson["game_table"]["entities"][name]["locations"][local].length;
                    if (container == "#discard_container"){
                        length = 1;
                    }
                    createSlots(fetch(container),length, local);
                });
                menuButtons.forEach(makeMenuButton);
                firstUpdate = 0;
            }
            //console.log(JSON.stringify(messageJson));
            buttonContainers.forEach(function (container,index){ 
                updateSlots(fetch(container),messageJson,buttonContainerNames[index],buttonContainerLocations[index]);
            });

            //Myself
            gameState = messageJson["game_table"]
            teamsState = gameState["teams"]
            me = messageJson["me"];
            mContainer = fetch("#messages_container");
            mContainer.message = messageJson;
            playerState = gameState["entities"][me]["locations"]["tent"][0];
            mContainer.playerState = playerState

            messageText = gameState["text"][my_team];
            if(messageText){
                mContainer.innerHTML = messageText;
            }
            running = gameState["running"];
            if (running) {
                changeBackground("black");
            } else {
                changeBackground("red");
            }
        };
    };
}, false);
