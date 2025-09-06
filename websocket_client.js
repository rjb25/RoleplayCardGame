function full(){
    document.documentElement.webkitRequestFullScreen();
    document.documentElement.requestFullscreen()
        .catch((e) => {
            console.log(e);
        });
}
gameState = {}
myself = ""
my_team = "good";
enemy_team = "evil";
lastMissing = [];
firstUpdate = 1;
tr = " 0.7)";
actionColors = {
    "damage": "rgba(255, 0, 0," + tr,
    "finish": "rgba(255, 255, 255," + tr,
    "income": "rgba(255, 255, 0," + tr,
    "draw": "rgba(0, 255, 0," + tr
};
var running = false;
var target = 0;
socketname = "localhost:12345";
//These need to be variables
buttonContainers = ["#enemy_base_container", "#situations_container", "#ally_base_container", "#plans_container", "#tent_container", "#cards_container", "#discard_container", "#merchant_container", "#shop_container", "#trash_container"];
buttonContainerLocations = ["base", "board", "base", "board", "tent", "hand", "discard", "stall", "shop", "trash"];
buttonContainerNames = [enemy_team, enemy_team, my_team, my_team, "me", "me", "me", "trader", "trader", "trader"];
menuButtons = ["remove_ai", "reset_session", "pause", "add_ai_evil", "add_ai_good", "join_good", "join_evil", "skip_trader"/*,"load_game","save_user","load_user"*/];
//This is what you run if you want to reconnect to server
//socketname = prompt("WebSocketURL no http://")
const websocketClient = new WebSocket("ws://" + socketname);

function pause() {
    changeBackground("DodgerBlue");
}

function join_good() {
    console.log("goodness")
    my_team = "good"
    enemy_team = "evil"
    buttonContainerNames = [enemy_team, enemy_team, my_team, my_team, "me", "me", "me", "trader", "trader", "trader"];
}

function join_evil() {
    console.log("evilness")
    my_team = "evil"
    enemy_team = "good"
    buttonContainerNames = [enemy_team, enemy_team, my_team, my_team, "me", "me", "me", "trader", "trader", "trader"];
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.id);
}

function findAncestor(el, cls) {
    if (el.classList.contains(cls)) {
        return el;
    }
    while ((el = el.parentElement) && !el.classList.contains(cls)) ;
    return el;
}

function drop(ev) {
    ev.preventDefault();
    var cardId = ev.dataTransfer.getData("text");
    nestedTarget = ev.target;
    target = findAncestor(nestedTarget, "slot");
    container = findAncestor(nestedTarget, "playable");
    if (container) {
        play(cardId, target.getAttribute("slot"), target.getAttribute("location"));
    }
}

function play(cardId, targ, locat) {
    websocketClient.send(JSON.stringify({
        command: "handle_play",
        id: cardId,
        index: targ,
        location: locat
    }));
    audio = new Audio("audio/play4.mp3");
    audio.play();
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
    menuButton.onclick = function () {
        websocketClient.send(JSON.stringify({
            command: title,
        }))
        console.log("called function " + title)
        console.log(window)
        if (window[title]) {
            console.log("called extra function " + title)
            window[title]();
        }
    };
    fetch("#menu_container").appendChild(menuButton);
}
function makeConnectButton(title) {
    menuButton = document.createElement("div");
    menuButton.classList.add("menu");
    menuTitle = document.createElement("div");
    menuTitle.innerHTML = title;
    menuButton.appendChild(menuTitle);
    menuButton.onclick = function () {
        websocketClient.send(JSON.stringify({
            command: "reconnect",
            reconnect: title
            //save: document.getElementById("save").value
        }))
        console.log("called function " + title)
        console.log(window)
    };
    fetch("#reconnect_container").appendChild(menuButton);
}


function inspect(slot) {
    inspection = slot.querySelector('.inspection');
    inspection.innerHTML = "";
    if(inspection.info){
        inspection.style.display = "none";
        inspection.info = false
    }else {
        inspection.style.display = "block";
        inspection.info = true
    }
    cardButton = slot.querySelector('.cardWhole');
    if (cardButton) {
        var card = cardButton.card;
        if (card) {
            if (card.location == "tent"){
                inspection.classList.add("inspectionDeck");
                locations = ["deck","discard"];
                //If I wanted to combine multiple do an if with vvvv
                //cards.push(...gameState["entities"][myself]["locations"]["discard"]);
                locations.forEach((location) => {
                    cards = gameState["entities"][myself]["locations"][location];
                    sectionDiv = document.createElement("div");
                    sectionDiv.classList.add("inspectSectionDiv");
                    sectionDiv.innerHTML += location;
                    cards.forEach((ca) => {
                        cardDiv = document.createElement("div");
                        cardDiv.classList.add("inspectCardDiv");
                        cardImage = new Image();
                        cardImage.classList.add("picture");
                        cardImage.src = "pics/" + ca["title"] + ".png";
                        cardImage.alt = ca["title"];
                        cardDiv.appendChild(cardImage);
                        sectionDiv.appendChild(cardDiv);
                    });
                    inspection.appendChild(sectionDiv);
                });
            } else {
            infoText = "Health: " + card["health"] + /*"<br>Cost:" + card["cost"] + "<br>Shield:" + card["shield"] +*/ "<br>";

            triggersText = "";
            Object.entries(card["triggers"]).forEach(([triggerType, events]) => {
                events.forEach((eventDict) => {
                    triggersText += triggerType;
                    if (eventDict["goal"]) {
                        triggersText += " length:" + eventDict["goal"];
                    }
                    triggersText += "<br>";
                    eventDict["actions"].forEach((action) => {
                        triggersText += "&nbsp;&nbsp;&nbsp;&nbsp;" + action["action"];
                        if (action["target"]) {
                            triggersText += " " + action["target"];
                        }
                        if (action["to"]) {
                            if (action["to"]["location"]) {
                                triggersText += " to " + action["to"]["location"];
                            }
                        }

                        if (action["amount"]) {
                            triggersText += " " + action["amount"];
                        }
                        //{"action": "effect_relative", "target": "self", "effect_function":{"name":"armor","function":"add","value":0.75}, "end_trigger":"exit"}
                        if (action["effect_function"]) {
                            triggersText += " " + action["effect_function"]["function"] + " " + action["effect_function"]["value"] + " " + action["effect_function"]["name"] + " till " + action["end_trigger"];
                        }

                        triggersText += "<br>";
                    });
                });
            });
            description = "";
            if (card["description"]){
                description = card["description"]+ "<br>";
            }
            inspection.innerHTML = description + infoText; //+ triggersText;
            }
            /*
            var infoImage = new Image();
            infoImage.draggable = false;
            //infoImage.classList.add("coin");
            infoImage.src = "pics/" + card["name"] + "info.png";
            infoImage.alt = "info";
            fetch("#inspect_container").appendChild(infoImage);
             */
        }
    }
}

//TODO make this happen less frequently. It's the most expensive
function updateCardButton(cardButton, card) {
    cardButton.card = card;
    var health = cardButton.querySelector(".health");
    var shield = cardButton.querySelector(".shield");
    var topRightImage = cardButton.querySelector(".topRightImage");
    var topLeftImage = cardButton.querySelector(".topLeftImage");
    var topRightText = cardButton.querySelector(".topRightText");
    var topLeftText = cardButton.querySelector(".topLeftText");
    if (["tent"].includes(card["location"])){
        bank = cardButton.querySelector(".topRightText");
        bank.innerHTML = Math.floor(card["gold"]);

        bank2 = cardButton.querySelector(".topLeftText");
        bank2.innerHTML = Math.floor(card["gems"]);

        mContainer = fetch("#messages_container");
        if (mContainer.playerState) {
            discard = cardButton.querySelector(".rightText");
            discard.innerHTML = mContainer.playerState.discardLength;
            deck = cardButton.querySelector(".leftText");
            deck.innerHTML = mContainer.playerState.deckLength;
            /*
            cooldown = cardButton.querySelector(".bottomRightText");
            cooldown.innerHTML = 0;//mContainer.playerState.cooldownLength;
            loaded = cardButton.querySelector(".bottomLeftText");
            loaded.innerHTML = 0;//mContainer.playerState.cooldownLength;
             */
        }
    }
    if (["shop"].includes(card["location"])){
        topRightText.innerHTML = card["value"];
        topRightImage.src = "pics/gem.png";
        topLeftImage.style.display = "none";
        mContainer = fetch("#messages_container");
        if (mContainer.playerState) {
            gems = mContainer.playerState["gems"];
            if (card["value"] > gems) {
                topRightText.style.color = "crimson";
            } else {
                topRightText.style.color = "white";
            }
        }
    }
    if (["hand"].includes(card["location"])){
        if("cost" in card) {
            topRightText.innerHTML = card["cost"];
            mContainer = fetch("#messages_container");
            if (mContainer.playerState) {
                money = mContainer.playerState["gold"];
                if (card["cost"] > money) {
                    topRightText.style.color = "crimson";
                } else {
                    topRightText.style.color = "white";
                }
            }
        }
    }
    if (["board","hand"].includes(card["location"])) {
        if (card["hype"] || card["level"]){
            bonus = card["hype"]+card["level"];
            topLeftText.innerHTML = parseFloat(bonus.toFixed(1));
            topLeftImage.src = "pics/level-icon.png";
            topLeftImage.style.display = "inline-block";
        }else {
            topLeftText.innerHTML = "";
            topLeftImage.style.display = "none";
        }
    }
    if (!["shop","stall"].includes(card["location"]) ){
        let percent = 100 * card["health"] / card["max_health"];
        health.style.width = Math.max(percent, 0) + "%";
        //Have heart icons below the bar instead maybe?
        health.style.height = 4.0 /* + card["max_health"] / 2.0*/ + "%";
        if (percent > 75) {
            health.style.background = "rgba(0, 255, 0, 0.8)";
        } else if (percent > 40) {
            health.style.background = "rgba(255, 255, 0, 0.8)";
        } else if (percent > 0) {
            health.style.background = "rgba(255, 0, 0, 0.8)";
        }
        percent = 100 * card["shield"] / card["max_shield"];
        shield.style.width = Math.max(percent, 0) + "%";
        shield.style.background = "rgba(30,144,255,0.9)";
    }
    if (!["shop","tent","hand"].includes(card["location"])){
        topRightText.innerHTML = "";
        topRightImage.style.display = "none";
    }
    if (!["board","tent","hand"].includes(card["location"])){
        topLeftText.innerHTML = "";
        topLeftImage.style.display = "none";
    }
    //currentBottom = 0;
    //Should be reversed at some point to match input data
    progressBar = cardButton.querySelector(".progress");
    if (progressBar) {
        eventDict = card["triggers"][progressBar.triggerType][progressBar.triggerIndex];
        percent = 100 * eventDict["progress"] / eventDict["goal"]
        percent_limit = Math.min(percent, 100);
        progressBar.style.height = percent_limit + "%";
    }

    storageBar = cardButton.querySelector(".storageBar");
    if(storageBar){
        for(i = 0; i < card["storage"].length; i++) {
            //Add dom div if the effect is not in existing keys.
            if (!storageBar.existing.includes(card["storage"][i]) && card["storage"][i]) {
                storageBar.existing.push(card["storage"][i]);
                innerImage = cardButton.querySelector(".storage"+(i+1)+"Inner");
                innerImage.parentNode.style.visibility = "visible";

                //innerImage.draggable = false;
                innerImage.classList.add("image");
                console.log(gameState);
                innerImage.src = "pics/" + gameState["ids"][card["storage"][i]]["name"] + ".png";
                console.log(innerImage.src);
                innerImage.alt = "stored";

            } else {
                //Wipe out the image
                //Need bonus image in center
               // storageDiv = storageBar.querySelector("." + storageType);
               // amountText = storageDiv.querySelector(".storageAmount");
               // amountText.innerHTML = amount.toFixed(1);
            }
        }
        storageBar.existing.forEach((storage) => {
            if (!(Object.keys(card["storage"]).includes(storage))) {
                arrayRemove(storageBar.existing, storage);
            }
        });
    }
    effectBar = cardButton.querySelector(".effectBar");
    //This is bad performance Only update when needed
    Object.entries(card["effects"]).forEach(([effectType, amount]) => {
        //Add dom div if the effect is not in existing keys.
        if (!(effectBar.existing.includes(effectType))) {
            effectBar.existing.push(effectType);
            amountText = document.createElement("p");
            amountText.classList.add("effectAmount");
            amountText.innerHTML = parseFloat(amount.toFixed(1)); //Repeat the image in the div, don't use text

            effectDiv = document.createElement("div");
            effectDiv.classList.add("effectDiv");
            effectDiv.classList.add(effectType);
            effectImage = new Image(20,20);
            //effectImage.draggable = false;
            effectImage.classList.add("image");
            effectImage.src = "pics/" + effectType + "-icon.png";
            effectImage.alt = effectType;

            effectDiv.appendChild(amountText);
            effectDiv.appendChild(effectImage);
            effectBar.appendChild(effectDiv);
        } else {
            effectDiv = effectBar.querySelector("." + effectType);
            amountText = effectDiv.querySelector(".effectAmount");
            amountText.innerHTML = amount.toFixed(1);
        }
    });
    effectBar.existing.forEach((effect) => {
        if (!(Object.keys(card["effects"]).includes(effect))) {
            arrayRemove(effectBar.existing, effect);
            effectBar.querySelector("." + effect).remove();
        }
    });
}

function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

function arrayRemove(array, item) {
    var index = array.indexOf(item);
    if (index !== -1) {
        array.splice(index, 1);
    }
}
function addImage(image, size, location, target = "", storage = ""){

    MyDiv = document.createElement("div");
    MyDiv.classList.add(size+"Div",location);
    /*
    if (target){
        MyDiv.classList.add(target);
    }
     */
    MyText = document.createElement("p");
    MyText.classList.add("count",location+"Text");
    MyImage = new Image();
    //MyImage.draggable = false;
    MyImage.classList.add("image",location+"Image");
        MyImage.src = "pics/" + image + ".png";
        MyImage.alt = "pics/" + image + ".png";
    MyDiv.appendChild(MyImage);
    MyDiv.appendChild(MyText);
    if(storage){
        InnerImage = new Image();
        InnerDiv = document.createElement("div");
        InnerDiv.classList.add("inner");
        InnerDiv.style.visibility = "hidden";
        //InnerImage.draggable = false;
        InnerImage.classList.add("image",location+"Inner");
        //InnerImage.src = "pics/" + image + ".png";
        //InnerImage.alt = "pics/" + image + ".png";
        InnerDiv.appendChild(InnerImage);
        MyDiv.appendChild(InnerDiv);

    }
    return MyDiv;

}

function generateCardButton(card) {
    let i;
    cardWhole = document.createElement("div");
    cardWhole.id = card["id"]
    cardWhole.classList.add("cardWhole");
    cardButton = document.createElement("div");
    cardButton.id = card["id"]
    cardButton.classList.add("card");
    cardInspection = document.createElement("div");
    cardInspection.classList.add("inspection");

    cardImage = new Image();
    cardImage.classList.add("picture");
    cardImage.src = "pics/" + card["title"] + ".png";
    cardImage.alt = card["title"];
    cardImage.onerror = function() {
        console.log("pics/" + card["title"] + ".png");
        cardImage.src = "pics/" + card["title"] + ".png";
        //this.onerror = null;
    };
    cardImage.draggable = true;
    cardImage.setAttribute("ondragstart", "drag(event)");
    cardImage.id = card["id"];

    health = document.createElement("div");
    health.classList.add("health");
    shield = document.createElement("div");
    shield.classList.add("shield");

    cardButton.appendChild(cardImage);
    cardButton.appendChild(health);
    cardButton.appendChild(shield);
    found = 0;
    cardProgress = document.createElement("div");
    cardProgress.classList.add("cardProgress");
    //Could just list the progress percent on the card based on main
    Object.entries(card["triggers"]).forEach(([triggerType, events]) => {
        if (!found) {
            for (i =0; i < events.length; i++) {
                eventDict = events[i];
                if (eventDict["goal"] && !found && "main" in eventDict) {
                    progressBar = document.createElement("div");
                    progressBar.classList.add("progress");
                    progressBar.triggerType = triggerType;
                    progressBar.triggerIndex = i;
                    progressBar.style.background = "dodgerblue";//All progress same color for clarity//eventDict["main"];
                    cardProgress.appendChild(progressBar);
                    found = 1;
                }
            }
        }
    });
    cardButton.appendChild(addImage("gem", "big", "topLeft"));
    cardButton.appendChild(addImage("coin3", "big", "topRight"));

    //PROGRESS
    showTarget = card["team"] === my_team || card["team"] === "gaia";
    locations = ["bottomLeftProgress", "leftProgress", "topLeftProgress"];
    if(card["icons"] ){
        for(i = 0; i < card["icons"].length; i++){
            if (card["icons"][i]) {
                if(showTarget){
                    target = card["targets"][i]
                } else {
                    target = "none"
                }
                cardProgress.appendChild(addImage(card["icons"][i]+"-icon", "small", locations[i], target));
            }
        }
    }
    //PROGRESS

    if (card["location"] == "tent") {
        cardButton.appendChild(addImage("discard", "big", "right"));
        cardButton.appendChild(addImage("deck", "big", "left"));
        //cardButton.appendChild(addImage("cooldown", "big", "bottomRight"));
        //cardButton.appendChild(addImage("loaded", "big", "bottomLeft"));
    }

    //The bar that contains effects like armor etc.
    //EFFECT
    effectBar = document.createElement("div");
    effectBar.existing = [];
    effectBar.classList.add("effectBar");
    //EFFECT

    //SLOTS
    if (card["storage"]){
        storageBar = document.createElement("div");
        storageBar.existing = [];
        storageBar.classList.add("storageBar");
        for (let i = 0; i < card["storage"].length; i++) {
            storageBar.appendChild(addImage("crate", "medium", "storage"+(i+1),"", true));
        }
        cardButton.appendChild(storageBar);
    }
    //SLOTS

    cardButton.appendChild(effectBar);
    cardWhole.appendChild(cardProgress)
    cardWhole.appendChild(cardButton)
    cardWhole.appendChild(cardInspection)

    updateCardButton(cardWhole, card);
    return cardWhole;
}

function createSlots(container, length, location) {
    for (let i = 0; i < length; i++) {
        slot = document.createElement("div");
        slot.setAttribute("slot", i);
        slot.setAttribute("location", location);
        slot.classList.add("slot");
        slot.setAttribute("ondrop", "drop(event)");
        slot.setAttribute("ondragover", "allowDrop(event)");
        if (location === "shop"){
                slot.onclick = function () {
                    cardButton = this.querySelector('.card')
                    if (cardButton) {
                        play(cardButton.id, i, "hand");
                    }
                };
        } else {
            slot.onclick = function () {
                inspect(this);
            };

        }
        container.append(slot);
    }
}

function updateSlots(container, messageJson, name, location) {
    newCards = []
    if (name == "me") {
        name = messageJson["me"]
    }
    try {
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
    if (location == "discard") {
        newCards = [];
    }

    newCards.forEach((newCard, i) => {
        slot = container.getElementsByClassName("slot")[i];
        oldCardButton = slot.querySelector(".cardWhole");
        oldId = 0;
        newId = 0;
        if (oldCardButton) {
            oldId = oldCardButton["id"];
        }
        if (newCard) {
            newId = newCard["id"];
        }
        //Replace or delete
        if (newId != oldId) {
            if (newId) {
                newCardButton = generateCardButton(newCard);
                slot.append(newCardButton);
                if (oldCardButton) {
                    oldCardButton.remove();
                }
            } else {
                if (oldCardButton) {
                    oldCardButton.remove();
                }
            }
        } else {
            //Update
            if (newCard) {
                updateCardButton(oldCardButton, newCard);
            }
        }
    });
}

function fetch(id) {
    return document.querySelector(id);
}

//CANVAS
var projectiles = [];
var fogs = [];
function hideFog(){
    fogs.forEach(function (fog) {
       fog.visible = false;
    });

}
function showFog(){
    fogs.forEach(function (fog) {
        fog.visible = true;
    });

}
function makeFog(bound1, image = "pics/fogCardBest.webp") {
    if (bound1) {
        d1 = bound1;
        pWidth = d1.width;
        pHeight = d1.height+18;
        startX = d1.x;
        startY = d1.y;
        fogs.push(new component(pWidth, pHeight, image, startX, startY));
    }
}

function launchProjectile(dom1, dom2, size = 1, image = "pics/bang.png") {
    //console.log(dom1,dom2)
    if (dom1 && dom2) {
        d1 = dom1;
        d2 = dom2;
        pWidth = 30 * size;
        pHeight = 30 * size;
        startX = d1.x + d1.width / 2 - pWidth / 2;
        startY = d1.y + d1.height / 2 - pHeight / 2;
        endX = d2.x + d2.width / 2 - pWidth / 2;
        endY = d2.y + d2.height / 2 - pHeight / 2;
        projectiles.push(new component(pWidth, pHeight, image, startX, startY, endX, endY, 0.02));
    }
}

function fog(on = true) {
    if (on) {
        bound = document.getElementById("situations_container").getBoundingClientRect();
        projectiles.push(new component(bound.width, bound.height, "grey", bound.x, bound.y));
    }
}

function startGame() {
    myGameArea.start();
}

var myGameArea = {

    canvas: document.getElementById("myCanvas"),
    cardArea: document.getElementById("myPlayArea").getBoundingClientRect(),
    scale: window.devicePixelRatio,
    start: function () {
        this.canvas.width = Math.floor(this.cardArea.width * this.scale);
        this.canvas.height = Math.floor(this.cardArea.height * this.scale);
        this.canvas.style.width = this.cardArea.width + "px";
        this.canvas.style.height = this.cardArea.height + "px";
        this.context = this.canvas.getContext("2d");
        this.context.scale(this.scale,this.scale);
        this.frameNo = 0;
        this.interval = setInterval(updateGameArea, 20);
    },
    update: function () {
        this.scale = window.devicePixelRatio;
        this.cardArea = document.getElementById("myPlayArea").getBoundingClientRect();
        this.canvas.width = Math.floor(this.cardArea.width * this.scale);
        this.canvas.height = Math.floor(this.cardArea.height * this.scale);
        this.canvas.style.width = this.cardArea.width + "px";
        this.canvas.style.height = this.cardArea.height + "px";
        this.context.scale(this.scale,this.scale);
        continueComponents = []
        for (i = 0; i < projectiles.length; i += 1) {
            projectiles[i].update();
            if (!projectiles[i].done) {
                continueComponents.push(projectiles[i])
            }
        }
        for (i = 0; i < fogs.length; i += 1) {
            fogs[i].update();
        }
        projectiles = continueComponents
    },
    stop: function () {
        clearInterval(this.interval);
    },
    clear: function () {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

function component(width, height, color, x, y, destX = 0, destY = 0, rate = false, text = "") {
    this.width = width;
    this.height = height;
    this.x = x;
    this.y = y;
    //If I want this to auto adjust then it needs to recaculate from the dom every time. X would just be dom.getClientBoundRect().x
    this.destX = destX;
    this.destY = destY;
    this.sourceX = x;
    this.sourceY = y;
    this.rate = rate;
    this.done = false;
    this.visible = true;
    this.progress = 0.0;
    this.update = function () {
        ctx = myGameArea.context;
        if (this.visible) {
            if (color.includes("pics")) {
                img = new Image();
                img.src = color
                ctx.drawImage(img, this.x, this.y, this.width, this.height)

            } else {
                ctx.fillStyle = color;
                ctx.fillRect(this.x, this.y, this.width, this.height);
            }
        }
        if (this.rate) {
            this.x = this.sourceX + (this.destX - this.sourceX) * this.progress;
            this.y = this.sourceY + (this.destY - this.sourceY) * this.progress;
            if (this.progress >= 1.0) {
                this.done = true;
            } else {
                this.progress += this.rate;
            }
        }
    }
}

function updateGameArea() {
    myGameArea.update();
}

document.addEventListener('DOMContentLoaded', function () {

    startGame();
    //HAVE A list of targets under an attack cards with the images of what's being targetted. Pulse green for good things red for bad targets.
    websocketClient.onopen = function () {
        console.log("Client connected!");
        websocketClient.onmessage = function (message) {
            messageJson = JSON.parse(message.data.replace(/'/g, '"'));
            //console.log(messageJson);
            if (firstUpdate) {
                changeBackground("dodgerBlue");
                buttonContainers.forEach(function (container, index) {
                    name = buttonContainerNames[index]
                    local = buttonContainerLocations[index]
                    if (name === "me") {
                        name = messageJson["me"]
                    }
                    //This length of slot if different between players would not update properly. Slots would need to be reupdated. Ok for now since slot sizes are constant between players
                    //This could be name indifferent if I had a list of sizes for all the slots
                    //TODO recreate slots on user switch. Basically handle expandable slots
                    length = messageJson["game_table"]["entities"][name]["locations"][local].length;
                    if (container == "#discard_container") {
                        length = 1;
                    }
                    createSlots(fetch(container), length, local);
                });
                menuButtons.forEach(makeMenuButton);
                firstUpdate = 0;
            }
            //console.log(JSON.stringify(messageJson));
            //Get location for animation before update.
            if ("animations" in messageJson && messageJson["animations"].length > 0) {
                //If you know where the card is before tick, use that if you can't find the card after tick
                messageJson["animations"].forEach(function (animation) {
                    card1 = document.getElementById(animation["sender"].id)
                    card2 = document.getElementById(animation["receiver"].id)
                    if (card1) {
                        animation["bound1"] = card1.getBoundingClientRect()
                    }
                    if (card2) {
                        animation["bound2"] = card2.getBoundingClientRect()
                    }
                })
            }
            missing = messageJson["missing"];
            if (JSON.stringify(missing) != JSON.stringify(lastMissing)){
                removeAllChildNodes(fetch("#reconnect_container"));
                missing.forEach(makeConnectButton);
                lastMissing = missing;
            }

            buttonContainers.forEach(function (container, index) {
                updateSlots(fetch(container), messageJson, buttonContainerNames[index], buttonContainerLocations[index]);
            });

            if ("animations" in messageJson && messageJson["animations"].length > 0) {
                //console.log(messageJson["animations"])
                messageJson["animations"].forEach(function (animation) {

                    card1 = document.getElementById(animation["sender"].id)
                    card2 = document.getElementById(animation["receiver"].id)
                    post1 = ""
                    post2 = ""
                    if (card1) {
                        post1 = card1.getBoundingClientRect();
                    }
                    if (card2) {
                        post2 = card2.getBoundingClientRect();
                    }
                    if (!post1) {
                        post1 = animation["bound1"]
                    }
                    if (!post2) {
                        post2 = animation["bound2"]
                    }
                    launchProjectile(post1,
                        post2, animation["size"], animation["image"]);
                })
            }

            /*
            if (fogs.length < 1){
                Array.from(document.getElementById("situations_container").getElementsByClassName("slot")).forEach(function (slot) {
                    bound = slot.getBoundingClientRect();

                    console.log(bound)
                    makeFog(bound);

                });}
            fog = messageJson["fog"]
            if (fog){
                showFog();
            }else{
                hideFog();
            }
             */


            //Myself
            gameState = messageJson["game_table"]
            teamsState = gameState["teams"]
            me = messageJson["me"];
            myself = me;
            mContainer = fetch("#messages_container");
            mContainer.message = messageJson;
            playerState = gameState["entities"][me]["locations"]["tent"][0];
            playerState.discardLength = gameState["entities"][me]["locations"]["discard"].length;
            playerState.deckLength = gameState["entities"][me]["locations"]["deck"].length;
            mContainer.playerState = playerState

            messageText = messageJson["text"];
            if (messageText) {
                mContainer.innerHTML = "Good Wins:" + messageText["evil"]["losses"] + "&nbsp;&nbsp;&nbsp;&nbsp; " + "Evil Wins:" + messageText["good"]["losses"];
            }
            running = gameState["running"];
            if (running) {
                changeBackground("DodgerBlue");
            } else {
                changeBackground("DodgerBlue");
            }

        };
    };
}, false);
