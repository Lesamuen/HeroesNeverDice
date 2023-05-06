function sellItem() {
    // Sell Item in market place 
    // can only sell items that are in the list of items in inventory

}

function buyItem() {
    // Buy Item in market place 
    // can only buy items that are in the list of items for sale
    // items will appear in the list with a buy button next to them
    // need to get function to display list of items in market

}

function equipItem() {
    // Equip Item
    // items are found in the inventory list
    // items will appear in the list with an equip button next to them
    // if equip button is clicked, item will be equipped and stats will be updated into Equipped Items list

    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", "http://127.0.0.1:5000/equip_item", true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.onload = function () {
        // handle response here 

    }
    xhttp.send("item.name = " + item.name);


}

function unequipItem() {
    // Unequip Item
    // items are found in the equipped items list
    // items will appear in the list with an unequip button next to them
    // if unequip button is clicked, item will be unequipped and stats will be updated into Inventory list

    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", "http://127.0.0.1:5000/unequip_item", true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.onload = function () {
        
        // TODO: Implement the code to update the equipped items table

    };
    xhttp.send("item.name=" + item.name);

}