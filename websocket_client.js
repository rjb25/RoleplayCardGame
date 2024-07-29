my_team = "good"
enemy_team = "evil"
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
    fetch(menuContainer).appendChild(menuButton);
}
function updateCardButton(cardButton,card){
    cardButton.card = card;
    cardTitle = cardButton.querySelector(".title");
    moneyString = "&#128176;".repeat(card["cost"]);
    cardTitle.innerHTML = moneyString +" " + "&hearts;".repeat(card["stability"]);
}
function inspect(slot){
    cardButton = slot.querySelector('.card')
    if(cardButton){
        card = cardButton.card;
        if(card){
            triggersText = ""
            Object.entries(card["triggers"]).forEach(([triggerType,triggers]) => {
                triggersText += triggerType + " ";
                //triggers.forEach

            });
            fetch(inspectContainer).innerHTML = triggersText ;
        }
    }
}
function generateCardButton(card){
    cardButton = document.createElement("div");
    cardButton.id = card["id"]
    cardButton.classList.add("card");
    cardTitle = document.createElement("div");
    cardTitle.classList.add("title");
    cardImage = new Image(90,90);
    cardImage.classList.add("picture");
    //cardImage = cardButton.querySelector(".picture");
    cardImage.src = "pics/" + card["title"]+".png";
    cardImage.alt = card["title"];
    cardImage.draggable = true;
    cardImage.setAttribute("ondragstart", "drag(event)");
    cardImage.id = card["id"];
    moneyString = "&#128176;".repeat(card["cost"]);
    cardTitle.innerHTML = moneyString +" " + "&hearts;".repeat(card["stability"]);
    cardButton.appendChild(cardTitle);
    cardButton.appendChild(cardImage);
    return cardButton;
}
function createSlots(container){
    for (let i = 0; i < 5; i++){
        slot = document.createElement("div");
        slot.setAttribute("spot", i);
        slot.classList.add("slot");
        slot.setAttribute("ondrop","drop(event)");
        slot.setAttribute("ondragover","allowDrop(event)");
        slot.onclick = function(){
            inspect(this);
        };
        fetch(container).append(slot);
    }
}

function updateSlots(container,messageJson,containerName){
    newCards = messageJson[containerName];
    newCards.forEach((newCard,i) => {
            slot = container.childNodes[i];
            
            cardButton = slot.childNodes[0];
            //Replace or delete
            if(!cardButton || cardButton["id"] != newCard["id"]){
                container.childNodes[i].innerHTML = '';
                if(newCard){
                    cardBox = generateCardButton(newCard);
                    container.childNodes[i].append(cardBox);
                }
            } else {
                //Update
                updateCardButton(cardButton,newCard);
            }
        });
}
function fetch(id){
    return document.querySelector(id);
}

document.addEventListener('DOMContentLoaded', function(){
    //HAVE A list of targets under an attack cards with the images of what's being targetted. Pulse green for good things red for bad targets.
    changeBackground("red");
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
                        changeBackground("green");
                    } else {
                        changeBackground("red");
                    }
                }
        };
    };
}, false);
