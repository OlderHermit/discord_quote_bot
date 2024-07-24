var number_of_dialog_fields = 0;
var possible_authors;
let data;
const runes = [
    'ᚠ', 'ᚡ', 'ᚢ', 'ᚣ', 'ᚤ', 'ᚥ', 'ᚦ', 'ᚧ', 'ᚨ', 'ᚩ', 'ᚪ', 'ᚫ', 'ᚬ', 'ᚭ', 'ᚮ', 'ᚯ',
    'ᚰ', 'ᚱ', 'ᚲ', 'ᚳ', 'ᚴ', 'ᚵ', 'ᚶ', 'ᚷ', 'ᚸ', 'ᚹ', 'ᚺ', 'ᚻ', 'ᚼ', 'ᚽ', 'ᚾ', 'ᚿ',
    'ᛀ', 'ᛁ', 'ᛂ', 'ᛃ', 'ᛄ', 'ᛅ', 'ᛆ', 'ᛇ', 'ᛈ', 'ᛉ', 'ᛊ', 'ᛋ', 'ᛌ', 'ᛍ', 'ᛎ', 'ᛏ',
    'ᛐ', 'ᛑ', 'ᛒ', 'ᛓ', 'ᛔ', 'ᛕ', 'ᛖ', 'ᛗ', 'ᛘ', 'ᛙ', 'ᛚ', 'ᛛ', 'ᛜ', 'ᛝ', 'ᛞ', 'ᛟ',
    'ᛠ', 'ᛡ', 'ᛢ', 'ᛣ', 'ᛤ', 'ᛥ', 'ᛦ', 'ᛧ', 'ᛨ', 'ᛩ', 'ᛪ', '᛫', '᛬', '᛭', 'ᛮ', 'ᛯ',
    'ᛰ'
];

readTextFile("static/authors.json", function (text) {
    data = JSON.parse(text);
    add_field();
});

function clear_output() {
    document.getElementById("quote_output").textContent = "";
}

function add_field() {
    var container = document.getElementById("dialog");
    var line = document.createElement("tr");
    var author = document.createElement("select");
    author.className = "select";
    author.name = "author" + number_of_dialog_fields;
    author.id = "author" + number_of_dialog_fields;

    var option = document.createElement("option");
    option.value = "-------";
    option.text = "-------";
    option.className = "option";
    option.setAttribute("disabled", "");
    option.setAttribute("hidden", "");
    option.setAttribute("selected", "");
    author.options.add(option);

    for (e of Object.entries(data).map(([k, v]) => v).sort((l, p) => l['author'] > p['author'])) {
        var option = document.createElement("option")
        option.value = e['author'];
        option.text = e['author'];
        option.className = "option";
        //option.style = "color: rgb(" + e['color'].replace(/ /g, ", ") + ");"
        author.options.add(option);
    }
    var td = document.createElement("td");
    td.appendChild(author);
    line.appendChild(td);

    var input = document.createElement("input");
    input.type = "text";
    input.className = "quote"
    input.id = "quote" + number_of_dialog_fields;
    input.name = "quote" + number_of_dialog_fields;
    input.spellcheck = "true"
    input.setAttribute("onkeypress", "click_press(event)");
    input.setAttribute("selected", "");
    
    var td = document.createElement("td");
    td.appendChild(input);
    line.appendChild(td);
    container.appendChild(line)
    
    number_of_dialog_fields++;
}

function generate_quote() {
    /*
    {
      "quote": "Idioto gówniana",
      "author": "Oliwer",
      "date": "≈2014",
      "explanation": "Jeden z pierwszych wulgaryzmów stworzonych przez Oliwera"
    }
      {
      "quote": [
        "[Zuza]Robert! Za Tobą!",
        "[Robert]Co masz na myśli?"
      ],
      "author": "Zuza;Robert",
      "date": "----",
      "explanation": "----"
    }
    */
    var list = [];
    var quote = "";
    var date = new Date(document.getElementById("date").value);
    var explanation = document.getElementById("explanation").value;
    var date_string = "";

    if (isNaN(date)) {
        date_string = "----";
    }
    else {
        date_string = date.toLocaleString('default', { month: 'long' }) + " " + date.getFullYear();
    }

    if (explanation.length <= 1)
        explanation = "----";

    for (i = 0; i < number_of_dialog_fields; i++) {
        var author = document.getElementById("author" + i);
        var quote = document.getElementById("quote" + i);
        if (author.options[author.selectedIndex].text != "-------")
            list.push([author.options[author.selectedIndex].text, quote.value]);
    }
    if (list.length == 0){
        alert("Can't submit quote without author");
        clear_output();
        return;
    }
    else if (list.length == 1) {
        quote = `{\n\t"quote": "${list[0][1]}",\n\t"author": "${list[0][0]}",\n\t"date": "${date_string}",\n\t"explanation": "${explanation}"\n}`;
    } else {
        var base_quote = "";
        var authors = "";
        for (e of list.filter(([a,q]) => a != "-------")) {
            base_quote += `\t\t"[${e[0]}]${e[1]}",\n`;
            authors += e[0] + ';';
        }
        base_quote = base_quote.substring(0, base_quote.length - 1);
        authors = authors.substring(0, authors.length - 1);

        quote = `{\n\t"quote": [\n${base_quote}\n\t],\n\t"author": "${authors}",\n\t"date": "${date_string}",\n\t"explanation": "${explanation}"\n}`;
    }
    document.getElementById("quote_output").value = quote;
}

function readTextFile(file, callback) {
    var rawFile = new XMLHttpRequest();
    rawFile.overrideMimeType("application/json");
    rawFile.open("GET", file, true);
    rawFile.onreadystatechange = function () {
        if (rawFile.readyState === 4 && rawFile.status == "200") {
            callback(rawFile.responseText);
        }
    }
    rawFile.send(null);
}

function click_press(event) {
    if (event.key == "Enter") {
        add_field();
        document.querySelector('[name="author' + (number_of_dialog_fields - 1) + '"]').focus();
    }
}

async function triggerCommand() {
    const data = document.getElementById('quote_output').value;
    if (data == "")
        return;
    
    try {
        //should be loaded from json?
        const response = await fetch('http://172.27.27.2:8000', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        alert('Quote successfully Added')
    } catch (error) {
        alert(`There was an server error: ${error}`)
    }
}

function generate_rune_for_background() {
    var delay = Math.random() * 25;
    var amount = Math.floor(Math.random() * 9) + 3;
    var x = Math.random() * 105 - 20;
    var y = Math.random() * 95;
    
    // var retry_counter = 5;
    // console.log('try');
    // console.log(list.filter(e => Math.abs(e.y - y) <= 2).length);
    // console.log(list.filter(e => Math.abs(e.y - y) <= 2).filter(e => e.left < x && e.right > x).length);
    // while(list.filter(e => Math.abs(e.y - y) <= 2).filter(e => e.left < x && e.right > x).length > 0 && retry_counter > 0){
    //     console.log('retry');
    //     x = Math.random() * 105 - 20;
    //     y = Math.random() * 95;
    //     retry_counter--;
    // }

    // if (retry_counter == 0){
    //     console.log('dupa');
    //     x = 0;
    //     y = 0;
    //     amount = 0;
    // }
    

    var rune = document.createElement("div");

    rune.className = "runes-container";
    rune.style = `left: ${x}%;top: ${y}vh;animation: scrollAnimation ${amount*7}s infinite linear;animation-delay: ${delay}s`;

    for(i=0; i < amount; i++){
        var character = document.createElement("div");

        character.className = "rune";
        character.style = `animation-delay: ${delay+i*0.5}s`;
        character.append(runes[Math.floor(Math.random() * runes.length)]);
        rune.appendChild(character);
    }
    return rune;
}

function generate_background() {
    //var generated = []
    for(j=0; j < 200; j++){
        //var e = generate_rune_for_background(generated);
        document.getElementById("background").appendChild(generate_rune_for_background());
        //generated.push(e.getBoundingClientRect());
    }
}