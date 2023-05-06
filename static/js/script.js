$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

function sellItem(id) {
    // Sell Item in market place 
    // can only sell items that are in the list of items in inventory
    var xhttp = new XMLHttpRequest();
    xhttp.open("PUT", "/sell_item", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onload = function () {
        location.reload()
    }
    xhttp.send(JSON.stringify({id: id, price: parseInt($('#sellPrice').val())}));
    
}


function buyItem(id) {
    // Buy Item in market place 
    // can only buy items that are in the list of items for sale
    // items will appear in the list with a buy button next to them
    // need to get function to display list of items in market

    var xhttp = new XMLHttpRequest();
    xhttp.open("PUT", "/buy_item", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onload = function () {
        location.reload()
    }
    xhttp.send(JSON.stringify({id: id, paying: [parseInt($('#buyd4').val()) , parseInt($('#buyd6').val()), parseInt($('#buyd8').val()), parseInt($('#buyd10').val()), parseInt($('#buyd12').val()), parseInt($('#buyd20').val())]}));
}

function equipItem(id) {
    // Equip Item
    // items are found in the inventory list
    // items will appear in the list with an equip button next to them
    // if equip button is clicked, item will be equipped and stats will be updated into Equipped Items list

    var xhttp = new XMLHttpRequest();
    xhttp.open("PUT", "/equip_item", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onload = function () {
        location.reload()
    }
    xhttp.send(id);
}

function unequipItem(id) {
    // Unequip Item
    // items are found in the equipped items list
    // items will appear in the list with an unequip button next to them
    // if unequip button is clicked, item will be unequipped and stats will be updated into Inventory list

    var xhttp = new XMLHttpRequest();
    xhttp.open("PUT", "/unequip_item", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onload = function () {
        location.reload()
    }
    xhttp.send(id);

}

function moveToVault(id){
    var xhttp = new XMLHttpRequest();
    xhttp.open("PUT", "/move_vault", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onload = function () {
        location.reload()
    }
    xhttp.send(id);
}

function moveToInv(id){
    var xhttp = new XMLHttpRequest();
    xhttp.open("PUT", "/move_inv", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onload = function () {
        location.reload()
    }
    xhttp.send(id);
}