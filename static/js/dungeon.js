window.onload = function() {
            displayMap(mapData);
};

function displayMap(mapData){
    const tileClasses = {
        0: "unexplored",
        1: "explored",
        2: "blocked",
        3: "entrance",
        4: "exit",
        5: "player"
      };
    
      // Get the table element from the HTML
      const table = document.getElementById("map-table");
      table.innerHTML='';
    
      // Loop through each row and column in the map data
      for (let row = 0; row < mapData.length; row++) {
        const tr = document.createElement("tr"); // Create a new table row
        table.appendChild(tr); // Add the row to the table
    
        for (let col = 0; col < mapData[row].length; col++) {
          const td = document.createElement("td"); // Create a new table cell
    
          // Add the corresponding CSS class to the cell based on the map data value
          td.classList.add(tileClasses[mapData[row][col]]);
    
          tr.appendChild(td); // Add the cell to the row
        }
    }
}

function getdungeon()
        {
            var http = new XMLHttpRequest();
            http.open("GET", "/dungeon");
            http.setRequestHeader("Content-Type", "application/json");
            http.onload = function() {
                if (this.status == 200){
                    displayMap(JSON.parse(this.responseText));
                }
            };
            http.send();
        }
var MAX_LOG_SIZE = 20;
var numLines = 0;
function movedungeon(direction){
            var http = new XMLHttpRequest();
            http.open("PUT", "/dungeon/move");
            http.setRequestHeader("Content-Type", "application/json");
            http.onload = function addtoLog(responseText) {
                if (this.status == 200){
                    $("#log").append(this.responseText + "\n");
                    numLines++;
                    getdungeon();
                    if (numLines > MAX_LOG_SIZE){
                        var lines = $("#log").html().split('\n');
                        lines.splice(0, numlines - MAX_LOG_SIZE);
                        $("#log").html(lines.join("\n"))
                        numLines=MAX_LOG_SIZE;
                    }
                }
                else if(this.status == 302){
                    window.location.href = this.responseText;
                }
            };
            http.send(direction);
}

function attack(){
    var totalDice = [];
    totalDice.push(document.getElementById("d4").value);
    totalDice.push(document.getElementById("d6").value);
    totalDice.push(document.getElementById("d8").value);
    totalDice.push(document.getElementById("d10").value);
    totalDice.push(document.getElementById("d12").value);
    totalDice.push(document.getElementById("d20").value);

    var http = new XMLHttpRequest();
        http.open("PUT", "/dungeon/attack");
        http.setRequestHeader("Content-Type", "application/json");
        http.onload = function() {
            if (this.status == 200){
                $("#log").append(this.responseText + "\n");
            }
        };
        http.send(JSON.stringify({"spent_dice" : totalDice}));
}

function defend(){


    var http = new XMLHttpRequest();
    http.open("PUT", "/dungeon/defend");
    http.setRequestHeader("Content-Type", "application/json");
    http.onload = function() {
        if (this.status == 200){
            $("#log").append(this.responseText + "\n");
        }
    };
    http.send();
}

function retreat(){
    var http = new XMLHttpRequest();
        http.open("PUT", "/dungeon/retreat");
        http.setRequestHeader("Content-Type", "application/json");
        http.onload = function() {
            if (this.status == 200){
                $("#log").append(this.responseText + "\n");
            }
        };
        http.send();
}