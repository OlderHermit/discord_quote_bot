var number_of_dialog_fields = 0;
var possible_authors;
let data;
readTextFile("static/quotes.json", function (text) {
    data = JSON.parse(text);
    add_field();
});

function clear_output() {
    document.getElementById("quote_output").textContent = "";
}

function add_field() {
    var container = document.getElementById("dialog");
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

    for (e of Object.entries(data['authors']).map(([k, v]) => v)) {
        var option = document.createElement("option")
        option.value = e['author'];
        option.text = e['author'];
        option.className = "option";
        //option.style = "color: rgb(" + e['color'].replace(/ /g, ", ") + ");"
        author.options.add(option);
    }
    container.appendChild(author);
    var input = document.createElement("input");
    input.type = "text";
    input.className = "quote"
    input.id = "quote" + number_of_dialog_fields;
    input.name = "quote" + number_of_dialog_fields;
    input.spellcheck = "true"
    input.setAttribute("onkeypress", "click_press(event)");
    input.setAttribute("selected", "");
    container.appendChild(input);
    container.appendChild(document.createElement("br"));
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
    if (list.length == 1) {
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
    return quote;
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

function copy_to_clipboard(){
    var area = document.getElementById('quote_output');
    navigator.clipboard.writeText(area.value);
}

async function triggerCommand() {
    const data = document.getElementById('quote_output').value;

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