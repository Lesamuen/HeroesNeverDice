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
                    displayMap(jsonify(this.responseText));
                }
            };
            http.send();
        }

function movedungeon(direction){
            var http = new XMLHttpRequest();
            http.open("PUT", "/dungeon/move");
            http.setRequestHeader("Content-Type", "application/json");
            http.onload = function() {
                if (this.status == 200){
                    $("#log").append(this.responseText + "\n");
                    getdungeon();
                }
            };
            http.send(direction);
}